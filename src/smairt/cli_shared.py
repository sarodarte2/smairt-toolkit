"""Shared presentation helpers for CLI command modules."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from smairt.project import find_project

console = Console()


def project_root() -> Path:
    """Resolve the current SMAIRT project or fail with a user-facing message."""
    root = find_project(Path.cwd())
    if root is None:
        raise FileNotFoundError("No SMAIRT project found from the current directory.")
    return root


def emit(payload: object, as_json: bool) -> None:
    """Render a command payload as JSON or readable terminal output."""
    if as_json:
        typer.echo(json.dumps(payload, indent=2, default=str))
    else:
        console.print(payload)
