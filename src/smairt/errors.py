"""Typed domain failures shared by SMAIRT interfaces."""

from __future__ import annotations


class SmairtError(Exception):
    """Base class for expected failures that should not expose a traceback."""

    exit_code = 2
    code = "smairt_error"


class UsageError(SmairtError):
    """Report invalid arguments or an operation outside a SMAIRT project."""

    code = "usage_error"


class PolicyError(SmairtError):
    """Report a validation or safety-policy blocker."""

    exit_code = 1
    code = "policy_error"


class IntegrityError(PolicyError):
    """Report a mismatch in immutable scientific provenance."""

    code = "integrity_error"


class ExternalServiceError(SmairtError):
    """Report a stable failure from a subprocess or remote metadata service."""

    code = "external_service_error"


class MutationConflictError(SmairtError):
    """Report that another process owns the project mutation lock."""

    exit_code = 3
    code = "mutation_conflict"


class RecoveryRequiredError(MutationConflictError):
    """Report an incomplete transaction requiring explicit recovery."""

    code = "recovery_required"
