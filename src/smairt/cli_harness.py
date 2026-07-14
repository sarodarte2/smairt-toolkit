"""Harness-selection CLI commands."""

import json
import sys
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
from smairt.hook_policy import hook_response, parse_hook_payload

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


@harness_app.command("hook", hidden=True)
def harness_hook(
    harness: Annotated[str, typer.Option("--harness")],
    event: Annotated[str, typer.Option("--event")],
) -> None:
    """Evaluate one bounded harness hook request without network access."""
    try:
        payload = parse_hook_payload(sys.stdin.buffer.read(1024 * 1024 + 1))
        response = hook_response(project_root(), harness, event, payload)
    except (OSError, ValueError) as exc:
        response = (
            {"cancel": True, "contextModification": "", "errorMessage": str(exc)}
            if harness == "cline"
            else {
                "hookSpecificOutput": {
                    "hookEventName": event,
                    "permissionDecision": "deny",
                    "permissionDecisionReason": str(exc),
                }
            }
        )
    typer.echo(json.dumps(response, separators=(",", ":")))
