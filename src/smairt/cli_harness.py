"""Harness-selection CLI commands."""

from typing import Annotated

import typer

from smairt.cli_shared import emit, project_root
from smairt.harnesses import (
    harness_status,
    install_harness,
    list_harnesses,
    select_harness,
    switch_plan,
)

harness_app = typer.Typer(help="Install and inspect coding-harness adapters")


@harness_app.command("list")
def harness_list(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """List supported harness adapters and active state."""
    emit(list_harnesses(project_root()), as_json)


@harness_app.command("status")
def harness_status_command(
    harness: Annotated[str | None, typer.Argument()] = None,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Inspect one harness or the active harness."""
    emit(harness_status(project_root(), harness), as_json)


@harness_app.command("install")
def harness_install(harness: Annotated[str, typer.Argument()]) -> None:
    """Install a harness when no conflicting adapter is active."""
    emit(install_harness(project_root(), harness), False)


@harness_app.command("upgrade")
def harness_upgrade(harness: Annotated[str, typer.Argument()]) -> None:
    """Upgrade the selected harness managed files."""
    emit(install_harness(project_root(), harness, upgrade=True), False)


@harness_app.command("select")
def harness_select(
    harness: Annotated[str, typer.Argument()],
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    backup_and_switch: Annotated[bool, typer.Option("--backup-and-switch")] = False,
) -> None:
    """Preview or apply an authoritative, conflict-aware harness switch."""
    payload = (
        switch_plan(project_root(), harness)
        if dry_run
        else select_harness(project_root(), harness, backup_and_switch=backup_and_switch)
    )
    emit(payload, False)
