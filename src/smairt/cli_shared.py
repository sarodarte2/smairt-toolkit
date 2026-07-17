"""Shared presentation helpers for CLI command modules."""

from __future__ import annotations

import json
from contextvars import ContextVar
from pathlib import Path

import click
import typer
from rich.console import Console

from smairt.project import find_project

console = Console()
_PROJECT_OVERRIDE: ContextVar[Path | None] = ContextVar("smairt_project_override", default=None)


def set_project_override(path: Path | None) -> None:
    """Set one explicit project-discovery start for the current CLI invocation."""
    _PROJECT_OVERRIDE.set(path.expanduser().resolve() if path is not None else None)


def project_root() -> Path:
    """Resolve the current SMAIRT project or fail with a user-facing message."""
    root = find_project(_PROJECT_OVERRIDE.get() or Path.cwd())
    if root is None:
        raise FileNotFoundError("No SMAIRT project found from the current directory.")
    return root


def json_envelope(payload: object, command: str | None = None) -> dict[str, object]:
    """Wrap machine output in the breaking beta JSON contract."""
    context = click.get_current_context(silent=True)
    command_name = command or (context.command_path if context else "smairt")
    mapping = payload if isinstance(payload, dict) else {}
    warnings = mapping.get("warnings", []) if isinstance(mapping, dict) else []
    errors = mapping.get("errors", []) if isinstance(mapping, dict) else []
    return {
        "schema_version": 1,
        "command": command_name,
        "ok": bool(mapping.get("ok", True)) if isinstance(mapping, dict) else True,
        "data": payload,
        "warnings": warnings if isinstance(warnings, list) else [warnings],
        "errors": errors if isinstance(errors, list) else [errors],
    }


def emit(payload: object, as_json: bool, *, command: str | None = None) -> None:
    """Render readable output or the versioned machine-output envelope."""
    if as_json:
        typer.echo(json.dumps(json_envelope(payload, command), indent=2, default=str))
    else:
        console.print(payload)
