"""Read-only MCP server and harness-access CLI commands."""

from __future__ import annotations

from typing import Annotated

import typer

from smairt.cli_shared import emit, project_root
from smairt.harnesses import configure_mcp, mcp_status
from smairt.models import HarnessName

mcp_app = typer.Typer(help="Serve and configure SMAIRT's bounded read-only MCP")


@mcp_app.command("serve")
def mcp_serve() -> None:
    """Serve exactly five read-only metadata tools over stdio."""
    from smairt.mcp_server import serve

    serve(project_root())


@mcp_app.command("status")
def mcp_status_command(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Report active harness MCP policy without contacting providers."""
    emit(mcp_status(project_root()), as_json)


@mcp_app.command("enable")
def mcp_enable(
    harness: Annotated[HarnessName, typer.Option()],
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
) -> None:
    """Enable the project-scoped server for the active maintained harness."""
    emit(configure_mcp(project_root(), harness, True, dry_run=dry_run), False)


@mcp_app.command("disable")
def mcp_disable(
    harness: Annotated[HarnessName, typer.Option()],
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
) -> None:
    """Disable the project-scoped MCP entry for the active harness."""
    emit(configure_mcp(project_root(), harness, False, dry_run=dry_run), False)
