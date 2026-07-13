"""Credential references backed by environment variables or the OS keyring."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

SERVICE_NAME = "smairt"
SUPPORTED_PROVIDERS = {"openalex", "zotero"}


class CredentialError(RuntimeError):
    """Base class for credential-backend failures with secret-free messages."""


class CredentialBackendUnavailable(CredentialError):
    """Indicate that no usable keyring backend is available."""


class CredentialBackendLocked(CredentialError):
    """Indicate that the configured keyring exists but is locked."""


@dataclass(frozen=True)
class CredentialResolution:
    """Describe where a configured secret was resolved without exposing it."""

    provider: str
    profile: str
    source: str


def _account(provider: str, profile: str) -> str:
    from smairt.utils import validate_identifier

    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"unsupported credential provider: {provider}")
    validate_identifier(profile, label="credential profile")
    return f"{provider}/{profile}"


def _keyring() -> Any:
    try:
        import keyring
    except ImportError as exc:
        raise CredentialBackendUnavailable("OS keyring support is not installed") from exc
    return keyring


def _translate_keyring_error(exc: Exception) -> CredentialError:
    """Map platform-specific keyring errors to stable, secret-free categories."""
    from keyring import errors

    if isinstance(exc, errors.KeyringLocked):
        return CredentialBackendLocked(
            "OS keyring is locked; unlock it or use the provider environment variable"
        )
    return CredentialBackendUnavailable(
        "OS keyring is unavailable; configure the provider environment variable"
    )


def resolve_credential(
    provider: str, profile: str = "default", environment_variable: str | None = None
) -> tuple[str | None, CredentialResolution | None]:
    """Resolve an environment variable before consulting the OS keyring."""
    account = _account(provider, profile)
    if environment_variable and os.environ.get(environment_variable):
        return os.environ[environment_variable], CredentialResolution(
            provider, profile, f"environment:{environment_variable}"
        )
    keyring = _keyring()
    from keyring import errors

    try:
        value = keyring.get_password(SERVICE_NAME, account)
    except errors.KeyringError as exc:
        raise _translate_keyring_error(exc) from exc
    return (value, CredentialResolution(provider, profile, "keyring") if value else None)


def set_credential(provider: str, profile: str, value: str) -> None:
    """Store a non-empty secret in the active OS keyring backend."""
    if not value:
        raise ValueError("credential value must not be empty")
    keyring = _keyring()
    from keyring import errors

    try:
        keyring.set_password(SERVICE_NAME, _account(provider, profile), value)
    except errors.KeyringError as exc:
        raise _translate_keyring_error(exc) from exc


def delete_credential(provider: str, profile: str) -> bool:
    """Delete a named keyring entry without exposing its former value."""
    keyring = _keyring()
    from keyring import errors

    account = _account(provider, profile)
    try:
        if keyring.get_password(SERVICE_NAME, account) is None:
            return False
        keyring.delete_password(SERVICE_NAME, account)
    except errors.KeyringError as exc:
        raise _translate_keyring_error(exc) from exc
    return True


def keyring_health() -> dict[str, object]:
    """Inspect the backend itself without reading any credential values."""
    try:
        backend = _keyring().get_keyring()
        priority = float(getattr(backend, "priority", 0))
        name = f"{type(backend).__module__}.{type(backend).__name__}"
        healthy = priority > 0 and "fail" not in name.lower() and "null" not in name.lower()
        return {
            "available": healthy,
            "status": "available" if healthy else "null",
            "backend": name,
            "priority": priority,
        }
    except CredentialBackendLocked as exc:
        return {"available": False, "status": "locked", "backend": None, "warning": str(exc)}
    except CredentialBackendUnavailable as exc:
        return {
            "available": False,
            "status": "unavailable",
            "backend": None,
            "warning": str(exc),
        }
    except (AttributeError, TypeError, ValueError) as exc:
        return {
            "available": False,
            "status": "unavailable",
            "backend": None,
            "warning": f"invalid keyring backend: {type(exc).__name__}",
        }
