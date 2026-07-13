"""Repository-safety CLI commands."""

from typing import Annotated

import typer
from rich.prompt import Confirm

from smairt.cli_shared import emit, project_root
from smairt.safety import (
    attest_repository,
    refresh_repository_visibility,
    release_check,
    safety_status,
    set_safety_mode,
)

safety_app = typer.Typer(help="Inspect and change project safety policy")


@safety_app.command("status")
def safety_status_command(
    as_json: Annotated[bool, typer.Option("--json")] = False,
    refresh_visibility: Annotated[bool, typer.Option("--refresh-visibility")] = False,
) -> None:
    """Show active safety policy and visibility evidence."""
    root = project_root()
    if refresh_visibility:
        refresh_repository_visibility(root)
    emit(safety_status(root), as_json, command="safety status")


@safety_app.command("set")
def safety_set(
    mode: Annotated[str, typer.Argument()], yes: Annotated[bool, typer.Option("--yes")] = False
) -> None:
    """Set Standard or Strict safety mode after confirmation."""
    if not yes and not Confirm.ask(f"Change safety mode to {mode}?", default=False):
        raise typer.Exit()
    emit(set_safety_mode(project_root(), mode), False)


@safety_app.command("release-check")
def safety_release_check(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Run repository release and publication safety gates."""
    payload = release_check(project_root())
    emit(payload, as_json)
    if not payload["ok"]:
        raise typer.Exit(1)


@safety_app.command("attest")
def safety_attest(
    visibility: Annotated[str, typer.Option()],
    yes: Annotated[bool, typer.Option("--yes")] = False,
) -> None:
    """Record a contributor-confirmed repository visibility."""
    if not yes and not Confirm.ask(
        f"Confirm repository visibility is {visibility}?", default=False
    ):
        raise typer.Exit()
    emit(attest_repository(project_root(), visibility), False)
