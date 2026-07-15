"""Transactional non-secret integration configuration and health services."""

from __future__ import annotations

from pathlib import Path

from smairt.credentials import (
    CredentialBackendLocked,
    CredentialBackendUnavailable,
    keyring_health,
    resolve_credential,
)
from smairt.local_setup import (
    ConnectionProfile,
    ProviderName,
    bind_profile,
    configure_profile,
    load_bindings,
    resolve_profile,
    unbind_profile,
)
from smairt.locking import mutating
from smairt.models import (
    CredentialProfile,
    DataClassification,
    SmairtConfig,
    ZoteroIntegration,
    ZoteroLibraryType,
    ZoteroMode,
    utc_now,
)
from smairt.transactions import FileTransaction


def _load_v4(root: Path) -> SmairtConfig:
    """Load an integration-editable project or explain the required migration."""
    config = SmairtConfig.load(root / "smairt.yaml")
    if config.schema_version < 4:
        raise ValueError("integration settings require schema v4; run 'smairt migrate apply'")
    return config


def _binding_status(
    root: Path, provider: ProviderName
) -> tuple[str | None, ConnectionProfile | None]:
    """Resolve a local binding for status output without turning absence into an error."""
    name = load_bindings(root).providers.get(provider)
    if not name:
        return None, None
    try:
        _, profile = resolve_profile(root, provider)
    except ValueError:
        return name, None
    return name, profile


def _credential_source(provider: str, profile: str, environment_variable: str | None) -> str:
    """Return a secret-free resolution label for status displays."""
    try:
        _, resolution = resolve_credential(provider, profile, environment_variable)
    except CredentialBackendLocked:
        return "locked"
    except CredentialBackendUnavailable:
        return "keyring-unavailable"
    return resolution.source if resolution else "missing"


@mutating("configure OpenAlex")
def configure_openalex(
    root: Path,
    *,
    enabled: bool,
    profile: str,
    environment_variable: str = "OPENALEX_API_KEY",
) -> dict[str, object]:
    """Configure a local OpenAlex profile and shared project enablement policy."""
    config = _load_v4(root)
    integration = config.integrations.openalex
    integration.enabled = enabled
    if enabled:
        configure_profile(
            profile,
            ConnectionProfile(
                provider="openalex",
                credential_profile=profile,
                environment_variable=environment_variable,
            ),
        )
        bind_profile(root, "openalex", profile)
    else:
        unbind_profile(root, "openalex")
    if config.schema_version < 5:
        integration.credential.profile = profile
        integration.credential.environment_variable = environment_variable
    transaction = FileTransaction(root, "configure OpenAlex")
    transaction.stage_text(root / "smairt.yaml", config.to_yaml())
    transaction.commit()
    return openalex_status(root)


def openalex_status(root: Path) -> dict[str, object]:
    """Report shared policy and local OpenAlex readiness without network access."""
    integration = _load_v4(root).integrations.openalex
    name, profile = _binding_status(root, "openalex")
    credential_profile = profile.credential_profile if profile else None
    environment_variable = profile.environment_variable if profile else None
    return {
        "enabled": integration.enabled,
        "bound_profile": name,
        "ready": bool(integration.enabled and profile),
        "credential_source": (
            _credential_source("openalex", credential_profile, environment_variable)
            if credential_profile
            else "missing-profile"
        ),
        "network_accessed": False,
    }


@mutating("configure Zotero")
def configure_zotero(
    root: Path,
    *,
    mode: ZoteroMode,
    library_id: str | None,
    library_type: ZoteroLibraryType,
    profile: str,
    environment_variable: str = "ZOTERO_API_KEY",
    mcp_access_enabled: bool = False,
    confirm_agent_access: bool = False,
) -> dict[str, object]:
    """Configure local Zotero connection data and shared project consent."""
    config = _load_v4(root)
    if mcp_access_enabled and mode is ZoteroMode.DISABLED:
        raise ValueError("Zotero MCP access requires a configured local or Web integration")
    if mcp_access_enabled and config.data.classification is DataClassification.CONTROLLED:
        raise ValueError("controlled projects cannot enable Zotero MCP access")
    confirmed_by = None
    confirmed_at = None
    if mcp_access_enabled and config.data.classification is DataClassification.PRIVATE:
        if not confirm_agent_access or not config.active_contributor:
            raise ValueError(
                "private projects require --confirm-agent-access and an active contributor"
            )
        confirmed_by = config.active_contributor
        confirmed_at = utc_now()
    enabled = mode is not ZoteroMode.DISABLED
    if enabled:
        configure_profile(
            profile,
            ConnectionProfile(
                provider="zotero",
                credential_profile=profile,
                environment_variable=environment_variable,
                mode=mode,
                library_id=library_id.strip() if library_id else None,
                library_type=library_type if mode is ZoteroMode.WEB else None,
            ),
        )
        bind_profile(root, "zotero", profile)
    else:
        unbind_profile(root, "zotero")
    if config.schema_version < 5:
        config.integrations.zotero = ZoteroIntegration(
            enabled=enabled,
            mode=mode,
            library_id=library_id.strip() if library_id else None,
            library_type=library_type,
            credential=CredentialProfile(
                profile=profile, environment_variable=environment_variable
            ),
            mcp_access_enabled=mcp_access_enabled,
            mcp_confirmed_by=confirmed_by,
            mcp_confirmed_at=confirmed_at,
        )
    else:
        config.integrations.zotero = ZoteroIntegration(
            enabled=enabled,
            mcp_access_enabled=mcp_access_enabled,
            mcp_confirmed_by=confirmed_by,
            mcp_confirmed_at=confirmed_at,
        )
    # Full validation covers cross-record classification and contributor invariants.
    config = SmairtConfig.model_validate(config.model_dump(mode="json", exclude_none=True))
    transaction = FileTransaction(root, "configure Zotero")
    transaction.stage_text(root / "smairt.yaml", config.to_yaml())
    transaction.commit()
    return zotero_status(root)


def zotero_status(root: Path) -> dict[str, object]:
    """Report shared policy and local Zotero readiness without exposing identifiers."""
    zotero = _load_v4(root).integrations.zotero
    name, profile = _binding_status(root, "zotero")
    credential_profile = profile.credential_profile if profile else None
    environment_variable = profile.environment_variable if profile else None
    return {
        "enabled": zotero.enabled,
        "mode": profile.mode.value if profile and profile.mode else "not-bound",
        "bound_profile": name,
        "ready": bool(zotero.enabled and profile),
        "credential_source": (
            "not-required"
            if profile and profile.mode is ZoteroMode.LOCAL
            else _credential_source("zotero", credential_profile, environment_variable)
            if credential_profile
            else "missing-profile"
        ),
        "mcp_access_enabled": zotero.mcp_access_enabled,
        "network_accessed": False,
    }


def integration_health(root: Path) -> dict[str, object]:
    """Return offline provider and backend status for the terminal hub."""
    semantic_name, semantic = _binding_status(root, "semantic_scholar")
    unpaywall_name, unpaywall = _binding_status(root, "unpaywall")
    semantic_source = (
        _credential_source(
            "semantic_scholar",
            semantic.credential_profile,
            semantic.environment_variable,
        )
        if semantic
        else "public"
    )
    return {
        "openalex": openalex_status(root),
        "zotero": zotero_status(root),
        "semantic_scholar": {
            "bound_profile": semantic_name,
            "ready": True,
            "access_mode": (
                "authenticated"
                if semantic_source not in {"missing", "public", "keyring-unavailable", "locked"}
                else "public"
            ),
            "credential_source": semantic_source,
            "network_accessed": False,
        },
        "unpaywall": {
            "bound_profile": unpaywall_name,
            "ready": bool(unpaywall and unpaywall.contact_email),
            "contact_email_configured": bool(unpaywall and unpaywall.contact_email),
            "network_accessed": False,
        },
        "keyring": keyring_health(),
    }
