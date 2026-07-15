"""User-local integration profiles and checkout-local project bindings.

Connection identifiers belong to the researcher and machine, not to the
shared scientific project contract.  API keys remain in environment variables
or the OS keyring; this module persists only connection metadata and profile
names outside Git-managed project files.
"""

from __future__ import annotations

import os
import re
from pathlib import Path, PurePosixPath
from typing import Literal

import yaml
from platformdirs import user_config_path
from pydantic import Field, field_validator, model_validator

from smairt.models import ComputeMode, DurableModel, ZoteroLibraryType, ZoteroMode
from smairt.utils import atomic_write, validate_identifier

ProviderName = Literal["openalex", "semantic_scholar", "zotero", "unpaywall"]
ThemeName = Literal[
    "scientific",
    "pnnl",
    "utep",
    "matrix",
    "dracula",
    "nord",
    "solarized",
    "amber",
    "high-contrast",
    "monochrome",
    "custom",
]
MarkName = Literal["none", "custom"]


class AppearanceConfig(DurableModel):
    """Store machine-local terminal presentation preferences only."""

    theme: ThemeName = "scientific"
    mark: MarkName = "none"
    primary_color: str | None = None
    secondary_color: str | None = None
    motion: Literal["automatic", "off"] = "automatic"

    @field_validator("primary_color", "secondary_color")
    @classmethod
    def valid_color(cls, value: str | None) -> str | None:
        """Accept only explicit six-digit RGB colors for custom accents."""
        if value is not None and not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
            raise ValueError("terminal colors must use #RRGGBB")
        return value.lower() if value else None

    @model_validator(mode="after")
    def coherent_custom_theme(self) -> AppearanceConfig:
        """Require both accents when the researcher chooses a custom theme."""
        if self.theme == "custom" and not (self.primary_color and self.secondary_color):
            raise ValueError("custom themes require primary and secondary colors")
        return self


class ConnectionProfile(DurableModel):
    """Describe one secret-free user-local provider connection."""

    provider: ProviderName
    credential_profile: str = "default"
    environment_variable: str | None = None
    mode: ZoteroMode | None = None
    library_id: str | None = None
    library_type: ZoteroLibraryType | None = None
    contact_email: str | None = None

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
        if self.provider in {"openalex", "semantic_scholar"}:
            if (
                self.mode is not None
                or self.library_id is not None
                or self.library_type is not None
                or self.contact_email is not None
            ):
                raise ValueError(
                    f"{self.provider.replace('_', ' ').title()} profiles cannot contain "
                    "Zotero connection fields"
                )
            return self
        if self.provider == "unpaywall":
            if not self.contact_email or not re.fullmatch(
                r"[^\s@]+@[^\s@]+\.[^\s@]+", self.contact_email
            ):
                raise ValueError("Unpaywall profiles require a valid contact email")
            if (
                self.mode is not None
                or self.library_id is not None
                or self.library_type is not None
            ):
                raise ValueError("Unpaywall profiles cannot contain Zotero connection fields")
            return self
        if self.mode not in {ZoteroMode.LOCAL, ZoteroMode.WEB}:
            raise ValueError("Zotero profiles require local or web mode")
        if self.mode is ZoteroMode.WEB and not (self.library_id or "").strip():
            raise ValueError("Zotero Web profiles require a library ID")
        if self.mode is ZoteroMode.WEB and self.library_type is None:
            raise ValueError("Zotero Web profiles require a library type")
        return self


class SlurmProfile(DurableModel):
    """Describe a native or existing-OpenSSH Slurm submit host."""

    mode: ComputeMode
    remote_root: str
    host_alias: str | None = None

    @field_validator("remote_root")
    @classmethod
    def safe_remote_root(cls, value: str) -> str:
        """Require one absolute POSIX directory without shell metacharacters."""
        path = PurePosixPath(value)
        if (
            not path.is_absolute()
            or ".." in path.parts
            or not re.fullmatch(r"/[A-Za-z0-9_./-]+", value)
        ):
            raise ValueError("remote root must be a safe absolute POSIX path")
        return value.rstrip("/") or "/"

    @model_validator(mode="after")
    def coherent_mode(self) -> SlurmProfile:
        """Require only SSH mode to name a preconfigured host alias."""
        if self.mode is ComputeMode.SSH:
            if not self.host_alias or not re.fullmatch(r"[A-Za-z0-9_.-]+", self.host_alias):
                raise ValueError("SSH Slurm profiles require a safe OpenSSH host alias")
        elif self.host_alias is not None:
            raise ValueError("native Slurm profiles cannot contain a host alias")
        return self


class UserSetupConfig(DurableModel):
    """Store named provider and compute profiles in the user's OS configuration area."""

    schema_version: Literal[6] = 6
    appearance: AppearanceConfig = Field(default_factory=AppearanceConfig)
    profiles: dict[ProviderName, dict[str, ConnectionProfile]] = Field(default_factory=dict)
    compute_profiles: dict[str, SlurmProfile] = Field(default_factory=dict)
    default_compute_profile: str | None = None

    @field_validator("profiles")
    @classmethod
    def valid_profile_names(
        cls, values: dict[ProviderName, dict[str, ConnectionProfile]]
    ) -> dict[ProviderName, dict[str, ConnectionProfile]]:
        """Reject unsafe labels and profiles stored beneath the wrong provider."""
        for provider, profiles in values.items():
            for name, profile in profiles.items():
                validate_identifier(name, label="connection profile")
                if profile.provider != provider:
                    raise ValueError(f"{name!r} is stored beneath the wrong provider")
        return values

    @model_validator(mode="after")
    def valid_default_compute(self) -> UserSetupConfig:
        """Require the selected compute profile to exist in the same local record."""
        if (
            self.default_compute_profile is not None
            and self.default_compute_profile not in self.compute_profiles
        ):
            raise ValueError("default compute profile is not configured")
        return self


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


def custom_logo_path() -> Path:
    """Return the owner-local sanitized logo file."""
    return setup_config_path().with_name("logo.txt")


def sanitize_ascii_logo(value: str) -> str:
    """Validate a compact terminal logo and reject control-sequence injection."""
    normalized = value.replace("\r\n", "\n").replace("\r", "\n").strip("\n")
    normalized = normalized.expandtabs(4)
    lines = normalized.splitlines()
    if not normalized or len(normalized.encode("utf-8")) > 2048:
        raise ValueError("custom logo must contain 1 to 2048 bytes")
    if len(lines) > 8 or any(len(line) > 40 for line in lines):
        raise ValueError("custom logo is limited to 8 lines and 40 columns")
    bidi_controls = {*range(0x202A, 0x202F), *range(0x2066, 0x206A)}
    if "\x1b" in normalized or any(ord(char) in bidi_controls for char in normalized):
        raise ValueError("custom logo cannot contain escape or bidi control characters")
    if any(ord(char) < 32 and char not in {"\n", "\t"} for char in normalized):
        raise ValueError("custom logo cannot contain terminal control characters")
    return normalized


def save_custom_logo(value: str) -> Path:
    """Sanitize and atomically save a user-local ASCII logo."""
    path = custom_logo_path()
    atomic_write(path, sanitize_ascii_logo(value) + "\n", mode=0o600)
    return path


def load_custom_logo() -> str | None:
    """Load the sanitized local logo when configured and present."""
    path = custom_logo_path()
    if not path.exists():
        return None
    return sanitize_ascii_logo(path.read_text(encoding="utf-8"))


def local_bindings_path(root: Path) -> Path:
    """Return the checkout-local ignored integration binding path."""
    return root / ".smairt/local/integrations.yaml"


def load_user_setup() -> UserSetupConfig:
    """Load user-wide profiles or return an empty validated configuration."""
    path = setup_config_path()
    if not path.exists():
        return UserSetupConfig()
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if isinstance(payload, dict) and int(payload.get("schema_version", 1)) in {1, 2, 3}:
        motion = payload.pop("motion", "automatic")
        if motion is False:  # YAML 1.1 readers treat the legacy word "off" as false.
            motion = "off"
        payload["appearance"] = {"motion": motion}
        payload["schema_version"] = 4
    if isinstance(payload, dict) and int(payload.get("schema_version", 1)) == 4:
        appearance = payload.get("appearance")
        if not isinstance(appearance, dict):
            appearance = {}
        legacy_logo = appearance.pop("logo", "smairt")
        appearance["mark"] = {
            "pnnl-mark": "pnnl",
            "custom": "custom",
        }.get(str(legacy_logo), "none")
        payload["appearance"] = appearance
        legacy_profiles = payload.get("profiles")
        grouped: dict[str, dict[str, object]] = {}
        if isinstance(legacy_profiles, dict):
            for name, raw_profile in legacy_profiles.items():
                if isinstance(raw_profile, dict) and raw_profile.get("provider"):
                    provider = str(raw_profile["provider"])
                    grouped.setdefault(provider, {})[str(name)] = raw_profile
        payload["profiles"] = grouped
        payload["schema_version"] = 5
    if isinstance(payload, dict) and int(payload.get("schema_version", 1)) == 5:
        appearance = payload.get("appearance")
        if not isinstance(appearance, dict):
            appearance = {}
        # Built-in institutional marks were removed in setup schema 6. Preserve the
        # independent named color themes while migrating a selected legacy mark to
        # SMAIRT's neutral wordmark. Custom sanitized marks remain supported.
        if appearance.get("mark") not in {"none", "custom"}:
            appearance["mark"] = "none"
        payload["appearance"] = appearance
        payload["schema_version"] = 6
    return UserSetupConfig.model_validate(payload)


def save_user_setup(config: UserSetupConfig) -> None:
    """Atomically persist secret-free setup metadata with owner-only mode."""
    content = yaml.safe_dump(config.model_dump(mode="json", exclude_none=True), sort_keys=False)
    atomic_write(setup_config_path(), content, mode=0o600)


def configure_slurm_profile(name: str, profile: SlurmProfile) -> SlurmProfile:
    """Create and select one user-local Slurm profile."""
    validate_identifier(name, label="compute profile")
    config = load_user_setup()
    config.compute_profiles[name] = profile
    config.default_compute_profile = name
    save_user_setup(config)
    return profile


def selected_slurm_profile() -> tuple[str, SlurmProfile]:
    """Return the selected profile or a guided setup error."""
    config = load_user_setup()
    name = config.default_compute_profile
    if not name or name not in config.compute_profiles:
        raise ValueError("Slurm is not configured on this machine; run 'smairt setup'")
    return name, config.compute_profiles[name]


def configure_profile(name: str, profile: ConnectionProfile) -> ConnectionProfile:
    """Create or replace one named user-local connection profile."""
    validate_identifier(name, label="connection profile")
    config = load_user_setup()
    config.profiles.setdefault(profile.provider, {})[name] = profile
    save_user_setup(config)
    return profile


def delete_profile(provider: ProviderName, name: str) -> bool:
    """Delete one local profile without touching its separate keyring secret."""
    config = load_user_setup()
    profiles = config.profiles.get(provider, {})
    existed = profiles.pop(name, None) is not None
    if not profiles:
        config.profiles.pop(provider, None)
    if existed:
        save_user_setup(config)
    return existed


def provider_profiles(provider: ProviderName) -> dict[str, ConnectionProfile]:
    """Return the configured profiles for one provider."""
    return dict(load_user_setup().profiles.get(provider, {}))


def iter_profiles() -> list[tuple[ProviderName, str, ConnectionProfile]]:
    """Flatten provider-scoped profiles for status and setup displays."""
    return [
        (provider, name, profile)
        for provider, profiles in load_user_setup().profiles.items()
        for name, profile in profiles.items()
    ]


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
    profile = load_user_setup().profiles.get(provider, {}).get(name)
    if profile is None:
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
    profile = load_user_setup().profiles.get(provider, {}).get(name)
    if profile is None:
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


def test_profile(provider: ProviderName, name: str) -> dict[str, object]:
    """Contact one configured provider with a bounded, secret-free health request."""
    profile = load_user_setup().profiles.get(provider, {}).get(name)
    if profile is None:
        raise ValueError(f"unknown {provider} connection profile: {name}")
    try:
        import httpx

        if profile.provider in {"openalex", "semantic_scholar"}:
            from smairt.credentials import CredentialError, resolve_credential

            try:
                key, _ = resolve_credential(
                    profile.provider,
                    profile.credential_profile,
                    profile.environment_variable
                    or (
                        "OPENALEX_API_KEY"
                        if profile.provider == "openalex"
                        else "SEMANTIC_SCHOLAR_API_KEY"
                    ),
                )
            except CredentialError:
                if profile.provider == "openalex":
                    raise
                key = None
            if profile.provider == "openalex" and not key:
                raise ValueError("OpenAlex API key is missing")
            response = httpx.get(
                (
                    "https://api.openalex.org/rate-limit"
                    if profile.provider == "openalex"
                    else "https://api.semanticscholar.org/graph/v1/paper/search"
                ),
                params=(
                    {"api_key": key}
                    if profile.provider == "openalex"
                    else {"query": "SMAIRT", "limit": 1, "fields": "paperId"}
                ),
                headers=({} if profile.provider == "openalex" or not key else {"x-api-key": key}),
                timeout=15,
            )
            if response.status_code in {401, 403}:
                raise ValueError(f"{profile.provider} rejected the API key")
            if response.status_code != 200:
                raise ValueError(f"{profile.provider} test failed with HTTP {response.status_code}")
            payload = response.json()
            return {
                "ok": True,
                "provider": profile.provider,
                "profile": name,
                "remaining": payload.get("remaining_usd")
                or response.headers.get("X-RateLimit-Remaining"),
                "access_mode": "authenticated" if key else "public",
                "network_accessed": True,
            }
        if profile.provider == "unpaywall":
            return {
                "ok": True,
                "provider": "unpaywall",
                "profile": name,
                "contact_email_configured": bool(profile.contact_email),
                "network_accessed": False,
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
