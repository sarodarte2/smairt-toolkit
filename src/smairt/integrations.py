"""Transactional non-secret integration configuration and health services."""

from __future__ import annotations

from pathlib import Path

from smairt.credentials import (
    CredentialBackendLocked,
    CredentialBackendUnavailable,
    keyring_health,
    resolve_credential,
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
    """Persist an OpenAlex credential reference without reading its secret."""
    config = _load_v4(root)
    integration = config.integrations.openalex
    integration.enabled = enabled
    integration.credential.profile = profile
    integration.credential.environment_variable = environment_variable
    transaction = FileTransaction(root, "configure OpenAlex")
    transaction.stage_text(root / "smairt.yaml", config.to_yaml())
    transaction.commit()
    return openalex_status(root)


def openalex_status(root: Path) -> dict[str, object]:
    """Report non-secret OpenAlex configuration without network access."""
    integration = _load_v4(root).integrations.openalex
    credential = integration.credential
    return {
        "enabled": integration.enabled,
        "profile": credential.profile,
        "environment_variable": credential.environment_variable,
        "credential_source": _credential_source(
            "openalex", credential.profile, credential.environment_variable
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
    """Persist validated read-only Zotero settings and attributed MCP consent."""
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
    config.integrations.zotero = ZoteroIntegration(
        mode=mode,
        library_id=library_id.strip() if library_id else None,
        library_type=library_type,
        credential=CredentialProfile(profile=profile, environment_variable=environment_variable),
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
    """Report non-secret Zotero configuration without network access."""
    zotero = _load_v4(root).integrations.zotero
    credential = zotero.credential
    return {
        "mode": zotero.mode.value,
        "library_id": zotero.library_id,
        "library_type": zotero.library_type.value,
        "profile": credential.profile,
        "environment_variable": credential.environment_variable,
        "credential_source": _credential_source(
            "zotero", credential.profile, credential.environment_variable
        ),
        "mcp_access_enabled": zotero.mcp_access_enabled,
        "network_accessed": False,
    }


def integration_health(root: Path) -> dict[str, object]:
    """Return offline provider and backend status for the terminal hub."""
    return {
        "openalex": openalex_status(root),
        "zotero": zotero_status(root),
        "keyring": keyring_health(),
    }
