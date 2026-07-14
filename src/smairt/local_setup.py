"""User-local integration profiles and checkout-local project bindings.

Connection identifiers belong to the researcher and machine, not to the
shared scientific project contract.  API keys remain in environment variables
or the OS keyring; this module persists only connection metadata and profile
names outside Git-managed project files.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from platformdirs import user_config_path
from pydantic import Field, field_validator, model_validator

from smairt.models import DurableModel, ZoteroLibraryType, ZoteroMode
from smairt.utils import atomic_write, validate_identifier

ProviderName = Literal["openalex", "zotero"]


class ConnectionProfile(DurableModel):
    """Describe one secret-free user-local provider connection."""

    provider: ProviderName
    credential_profile: str = "default"
    environment_variable: str | None = None
    mode: ZoteroMode | None = None
    library_id: str | None = None
    library_type: ZoteroLibraryType | None = None

    @field_validator("credential_profile")
    @classmethod
    def valid_credential_profile(cls, value: str) -> str:
        """Keep keyring account selectors portable and path-safe."""
        return validate_identifier(value, label="credential profile")

    @field_validator("environment_variable")
    @classmethod
    def valid_environment_variable(cls, value: str | None) -> str | None:
        """Reuse shell-safe environment variable validation."""
        if value is None:
            return None
        from smairt.models import CredentialProfile

        return CredentialProfile(environment_variable=value).environment_variable

    @model_validator(mode="after")
    def coherent_provider(self) -> ConnectionProfile:
        """Require only the fields needed by the selected provider and mode."""
        if self.provider == "openalex":
            if (
                self.mode is not None
                or self.library_id is not None
                or self.library_type is not None
            ):
                raise ValueError("OpenAlex profiles cannot contain Zotero connection fields")
            return self
        if self.mode not in {ZoteroMode.LOCAL, ZoteroMode.WEB}:
            raise ValueError("Zotero profiles require local or web mode")
        if self.mode is ZoteroMode.WEB and not (self.library_id or "").strip():
            raise ValueError("Zotero Web profiles require a library ID")
        if self.mode is ZoteroMode.WEB and self.library_type is None:
            raise ValueError("Zotero Web profiles require a library type")
        return self


class UserSetupConfig(DurableModel):
    """Store named provider profiles in the user's OS configuration area."""

    schema_version: int = 1
    motion: Literal["automatic", "off"] = "automatic"
    profiles: dict[str, ConnectionProfile] = Field(default_factory=dict)

    @field_validator("profiles")
    @classmethod
    def valid_profile_names(
        cls, values: dict[str, ConnectionProfile]
    ) -> dict[str, ConnectionProfile]:
        """Reject profile labels that could alter file or keyring semantics."""
        for name in values:
            validate_identifier(name, label="connection profile")
        return values


class LocalIntegrationBindings(DurableModel):
    """Bind this checkout to user-local profiles without entering Git."""

    schema_version: int = 1
    providers: dict[ProviderName, str] = Field(default_factory=dict)

    @field_validator("providers")
    @classmethod
    def valid_bindings(cls, values: dict[ProviderName, str]) -> dict[ProviderName, str]:
        """Validate every selected local profile name."""
        for name in values.values():
            validate_identifier(name, label="connection profile")
        return values


def setup_config_path() -> Path:
    """Return the user-wide config path, with a test/operator override."""
    override = os.environ.get("SMAIRT_CONFIG_HOME")
    root = Path(override).expanduser() if override else user_config_path("smairt", appauthor=False)
    return root / "setup.yaml"


def local_bindings_path(root: Path) -> Path:
    """Return the checkout-local ignored integration binding path."""
    return root / ".smairt/local/integrations.yaml"


def load_user_setup() -> UserSetupConfig:
    """Load user-wide profiles or return an empty validated configuration."""
    path = setup_config_path()
    if not path.exists():
        return UserSetupConfig()
    return UserSetupConfig.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})


def save_user_setup(config: UserSetupConfig) -> None:
    """Atomically persist secret-free setup metadata with owner-only mode."""
    content = yaml.safe_dump(config.model_dump(mode="json", exclude_none=True), sort_keys=False)
    atomic_write(setup_config_path(), content, mode=0o600)


def configure_profile(name: str, profile: ConnectionProfile) -> ConnectionProfile:
    """Create or replace one named user-local connection profile."""
    validate_identifier(name, label="connection profile")
    config = load_user_setup()
    config.profiles[name] = profile
    save_user_setup(config)
    return profile


def delete_profile(name: str) -> bool:
    """Delete one local profile without touching its separate keyring secret."""
    config = load_user_setup()
    existed = config.profiles.pop(name, None) is not None
    if existed:
        save_user_setup(config)
    return existed


def load_bindings(root: Path) -> LocalIntegrationBindings:
    """Load checkout-local bindings without creating a file during status checks."""
    path = local_bindings_path(root)
    if not path.exists():
        return LocalIntegrationBindings()
    return LocalIntegrationBindings.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    )


def save_bindings(root: Path, bindings: LocalIntegrationBindings) -> None:
    """Persist bindings beneath the scaffold's ignored local-state directory."""
    content = yaml.safe_dump(bindings.model_dump(mode="json"), sort_keys=False)
    atomic_write(local_bindings_path(root), content, mode=0o600)


def bind_profile(root: Path, provider: ProviderName, name: str) -> ConnectionProfile:
    """Bind a configured user profile to one checkout."""
    profile = load_user_setup().profiles.get(name)
    if profile is None or profile.provider != provider:
        raise ValueError(f"unknown {provider} connection profile: {name}")
    bindings = load_bindings(root)
    bindings.providers[provider] = name
    save_bindings(root, bindings)
    return profile


def unbind_profile(root: Path, provider: ProviderName) -> bool:
    """Remove one checkout-local provider binding."""
    bindings = load_bindings(root)
    existed = bindings.providers.pop(provider, None) is not None
    if existed:
        save_bindings(root, bindings)
    return existed


def resolve_profile(root: Path, provider: ProviderName) -> tuple[str, ConnectionProfile]:
    """Resolve this checkout's selected profile or provide a guided error."""
    name = load_bindings(root).providers.get(provider)
    if not name:
        raise ValueError(
            f"{provider.title()} is not connected on this machine; run 'smairt setup' "
            f"then 'smairt integration bind {provider} <profile>'"
        )
    profile = load_user_setup().profiles.get(name)
    if profile is None or profile.provider != provider:
        raise ValueError(f"local {provider} profile '{name}' is missing or incompatible")
    return name, profile


def discover_zotero_libraries(profile: ConnectionProfile) -> list[tuple[str, str, str]]:
    """Validate a Web key and return selectable user/group libraries."""
    if profile.provider != "zotero" or profile.mode is not ZoteroMode.WEB:
        raise ValueError("Zotero library discovery requires a Web profile")
    from smairt.credentials import resolve_credential

    key, _ = resolve_credential(
        "zotero", profile.credential_profile, profile.environment_variable or "ZOTERO_API_KEY"
    )
    if not key:
        raise ValueError("Zotero Web API key is missing")
    try:
        import httpx

        headers = {"Zotero-API-Key": key, "Zotero-API-Version": "3"}
        response = httpx.get("https://api.zotero.org/keys/current", headers=headers, timeout=15)
        if response.status_code == 403:
            raise ValueError("Zotero rejected the API key or its library permissions")
        if response.status_code != 200:
            raise ValueError(f"Zotero key check failed with HTTP {response.status_code}")
        payload = response.json()
        user_id = str(payload.get("userID") or "")
        if not user_id:
            raise ValueError("Zotero key response did not identify a user library")
        libraries = [("user", user_id, "My Zotero Library")]
        groups = httpx.get(
            f"https://api.zotero.org/users/{user_id}/groups",
            headers=headers,
            timeout=15,
        )
        if groups.status_code == 200:
            for item in groups.json():
                data = item.get("data", {}) if isinstance(item, dict) else {}
                group_id = str(data.get("id") or item.get("id") or "")
                if group_id:
                    libraries.append(("group", group_id, str(data.get("name") or "Zotero Group")))
        return libraries
    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError("Zotero Web is unavailable; no setup value was changed") from exc


def test_profile(name: str) -> dict[str, object]:
    """Contact one configured provider with a bounded, secret-free health request."""
    profile = load_user_setup().profiles.get(name)
    if profile is None:
        raise ValueError(f"unknown connection profile: {name}")
    try:
        import httpx

        if profile.provider == "openalex":
            from smairt.credentials import resolve_credential

            key, _ = resolve_credential(
                "openalex",
                profile.credential_profile,
                profile.environment_variable or "OPENALEX_API_KEY",
            )
            if not key:
                raise ValueError("OpenAlex API key is missing")
            response = httpx.get(
                "https://api.openalex.org/rate-limit",
                params={"api_key": key},
                timeout=15,
            )
            if response.status_code in {401, 403}:
                raise ValueError("OpenAlex rejected the API key")
            if response.status_code != 200:
                raise ValueError(f"OpenAlex test failed with HTTP {response.status_code}")
            payload = response.json()
            return {
                "ok": True,
                "provider": "openalex",
                "profile": name,
                "remaining": payload.get("remaining_usd")
                or response.headers.get("X-RateLimit-Remaining"),
                "network_accessed": True,
            }
        if profile.mode is ZoteroMode.LOCAL:
            response = httpx.get(
                "http://localhost:23119/api/users/0/collections",
                params={"limit": 1, "v": 3},
                timeout=5,
            )
            if response.status_code == 403:
                raise ValueError(
                    "Zotero is running, but 'Allow other applications on this computer to "
                    "communicate with Zotero' is disabled"
                )
            if response.status_code != 200:
                raise ValueError(f"Zotero Local test failed with HTTP {response.status_code}")
            return {
                "ok": True,
                "provider": "zotero",
                "profile": name,
                "mode": "local",
                "network_accessed": False,
            }
        libraries = discover_zotero_libraries(profile)
        return {
            "ok": True,
            "provider": "zotero",
            "profile": name,
            "mode": "web",
            "libraries_available": len(libraries),
            "network_accessed": True,
        }
    except (ValueError, RuntimeError):
        raise
    except Exception as exc:
        if profile.provider == "zotero" and profile.mode is ZoteroMode.LOCAL:
            raise RuntimeError(
                "Zotero Local is unreachable; start Zotero and enable local API access"
            ) from exc
        raise RuntimeError(f"{profile.provider.title()} is unavailable") from exc
