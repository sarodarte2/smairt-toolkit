"""Project lock and transaction-recovery CLI groups."""

from __future__ import annotations

from typing import Annotated

import typer
from rich.prompt import Confirm

from smairt.cli_shared import emit, project_root
from smairt.locking import break_lock, read_lock
from smairt.transactions import complete_transaction, rollback_transaction, transaction_status

lock_app = typer.Typer(help="Inspect and recover the project mutation lock")
recovery_app = typer.Typer(help="Inspect and resolve interrupted file transactions")


@lock_app.command("status")
def lock_status(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Show the current lock owner and locally verifiable liveness."""
    emit(read_lock(project_root()), as_json)


@lock_app.command("break")
def lock_break(yes: Annotated[bool, typer.Option("--yes")] = False) -> None:
    """Break a lock only after an explicit stale-owner confirmation."""
    if not yes and not Confirm.ask("Break the current project mutation lock?", default=False):
        raise typer.Exit()
    emit(break_lock(project_root(), force=True), False)


@recovery_app.command("status")
def recovery_status(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """List committed, rolled-back, and incomplete transaction journals."""
    emit(transaction_status(project_root()), as_json)


@recovery_app.command("complete")
def recovery_complete(
    identifier: Annotated[str, typer.Argument()],
    yes: Annotated[bool, typer.Option("--yes")] = False,
) -> None:
    """Finish publishing every staged post-transaction file."""
    if not yes and not Confirm.ask(f"Complete transaction {identifier}?", default=False):
        raise typer.Exit()
    emit(complete_transaction(project_root(), identifier), False)


@recovery_app.command("rollback")
def recovery_rollback(
    identifier: Annotated[str, typer.Argument()],
    yes: Annotated[bool, typer.Option("--yes")] = False,
) -> None:
    """Restore every backed-up pre-transaction file."""
    if not yes and not Confirm.ask(f"Roll back transaction {identifier}?", default=False):
        raise typer.Exit()
    emit(rollback_transaction(project_root(), identifier), False)
