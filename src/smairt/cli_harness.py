"""Harness-selection CLI commands."""

import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Annotated

import typer
from rich.panel import Panel
from rich.table import Table

from smairt.cli_shared import console, emit, project_root
from smairt.harness_presentation import harness_info
from smairt.harnesses import (
    harness_status,
    install_harness,
    list_harnesses,
    select_harness,
    switch_plan,
)
from smairt.hook_policy import hook_response, parse_hook_payload
from smairt.models import HarnessName
from smairt.project import find_project

harness_app = typer.Typer(help="Install and inspect coding-harness adapters")


def _optional_project_root() -> Path | None:
    """Return the current project when present without making chooser commands project-only."""
    try:
        return find_project(Path.cwd())
    except FileNotFoundError:
        return None


def _details(item: Mapping[str, object]) -> Mapping[str, object]:
    """Normalize project status and global chooser records for presentation."""
    nested = item.get("presentation")
    return nested if isinstance(nested, dict) else item


def _render_harness_list(items: list[dict[str, object]]) -> None:
    """Render a wide comparison table or readable stacked cards."""
    if console.width >= 104:
        table = Table(title="SMAIRT · Choose a Coding Harness", header_style="bold #f28c28")
        table.add_column("", width=2)
        table.add_column("Harness", style="bold")
        table.add_column("Best for", ratio=2)
        table.add_column("Workflow", ratio=1)
        table.add_column("Safety and review", ratio=2)
        for item in items:
            details = _details(item)
            table.add_row(
                "◆" if item.get("active") else "",
                str(details["display_name"]),
                str(details["best_for"]),
                str(details["invocation"]),
                f"{details['safety']}\n{details['reviewer']}",
            )
        console.print(table)
    else:
        console.print("[bold #f28c28]SMAIRT · Choose a Coding Harness[/]\n")
        for item in items:
            details = _details(item)
            marker = " · ACTIVE" if item.get("active") else ""
            body = (
                f"[bold]{details['tagline']}[/]\n\n"
                f"Best for: {details['best_for']}\n"
                f"Workflow: {details['invocation']}\n"
                f"Review: {details['reviewer']}"
            )
            console.print(Panel(body, title=f"{details['display_name']}{marker}", expand=True))
    console.print(
        "[dim]Inspect one: smairt harness info HARNESS · Preview a switch inside a project: "
        "smairt harness select HARNESS --dry-run[/dim]"
    )


def _render_harness_info(payload: Mapping[str, object]) -> None:
    """Render one concise native-adapter guide."""
    details = _details(payload)
    lines = [
        f"[bold]{details['tagline']}[/]",
        "",
        f"Best for: {details['best_for']}",
        f"Orientation: {details['orientation']}",
        f"Workflow: {details['invocation']}",
        f"Safety: {details['safety']}",
        f"Reviewer: {details['reviewer']}",
        f"Setup: {details['setup']}",
        f"Limitation: {details['limitation']}",
        f"Guide: {details['guide']}",
    ]
    if "installed" in payload:
        state = "active" if payload.get("active") else "inactive"
        freshness = "current" if payload.get("adapter_supported") else "not installed/current"
        lines.extend(["", f"Project state: {state} · {freshness}"])
    console.print(Panel("\n".join(lines), title=f"SMAIRT · {details['display_name']}", expand=True))


@harness_app.command("list")
def harness_list(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """List supported harness adapters and active state."""
    root = _optional_project_root()
    payload = list_harnesses(root)
    if as_json:
        emit(payload, True)
    else:
        _render_harness_list(payload)


@harness_app.command("info")
def harness_info_command(
    harness: Annotated[HarnessName, typer.Argument()],
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Explain who one harness suits and how its SMAIRT adapter behaves."""
    root = _optional_project_root()
    payload = harness_status(root, harness.value) if root else harness_info(harness)
    if as_json:
        emit(payload, True)
    else:
        _render_harness_info(payload)


@harness_app.command("status")
def harness_status_command(
    harness: Annotated[str | None, typer.Argument()] = None,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Inspect one harness or the active harness."""
    payload = harness_status(project_root(), harness)
    if as_json:
        emit(payload, True)
    else:
        _render_harness_info(payload)


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
