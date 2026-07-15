"""Research-lifecycle CLI commands from background through evidence correction."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from smairt.cli_shared import emit, project_root
from smairt.code_quality import build_code_index
from smairt.corrections import amend_artifact, correct_run
from smairt.guidance import next_guidance
from smairt.hpc import submit_slurm
from smairt.models import ComputeResources, Decision
from smairt.research import (
    activate_hypothesis,
    create_background,
    create_experiment,
    create_proposal_set,
    new_iteration,
    record_decision,
    validate_background,
    validate_proposal_set,
)
from smairt.runner import run_experiment

console = Console()
background_app = typer.Typer(help="Manage source-grounded project background")
hypothesis_app = typer.Typer(help="Manage proposal sets and human-selected hypotheses")
proposal_app = typer.Typer(help="Create and validate three-option proposal sets")
experiment_app = typer.Typer(help="Manage experiments")
iteration_app = typer.Typer(help="Manage immutable research iterations")
decision_app = typer.Typer(help="Record human research decisions")
hypothesis_app.add_typer(proposal_app, name="proposals")


def _show_next(root: Path) -> None:
    """Render the authoritative recommendation after a successful state transition."""
    guidance = next_guidance(root)
    recommended = guidance.get("recommended")
    recommended_label = (
        recommended.get("label")
        if isinstance(recommended, dict)
        else guidance.get("recommended_next")
    )
    actions = guidance.get("actions")
    alternatives = (
        [item.get("label") for item in actions[1:] if isinstance(item, dict)]
        if isinstance(actions, list)
        else guidance.get("alternatives", [])
    )
    console.print(
        {
            "completed": guidance["completed"],
            "recommended_next": recommended_label,
            "alternatives": alternatives,
        }
    )


@background_app.command("create")
def background_create() -> None:
    """Create the initial-background synthesis workspace and show what follows."""
    root = project_root()
    console.print(create_background(root))
    _show_next(root)


@background_app.command("validate")
def background_validate() -> None:
    """Check background structure and grounding against indexed references."""
    errors = validate_background(project_root())
    emit({"ok": not errors, "errors": errors}, False)
    if errors:
        raise typer.Exit(1)


@proposal_app.command("new")
def proposal_new() -> None:
    """Create a retained three-option hypothesis proposal set."""
    root = project_root()
    console.print(create_proposal_set(root))
    _show_next(root)


@proposal_app.command("validate")
def proposal_validate(path: Annotated[Path, typer.Argument()]) -> None:
    """Validate proposal completeness before a researcher chooses an option."""
    errors = validate_proposal_set(path)
    emit({"ok": not errors, "errors": errors}, False)
    if errors:
        raise typer.Exit(1)


@hypothesis_app.command("activate")
def hypothesis_activate(
    proposal_set: Annotated[Path, typer.Option()],
    option: Annotated[str, typer.Option()],
    title: Annotated[str, typer.Option()],
    statement: Annotated[str, typer.Option()],
    selected_by: Annotated[str, typer.Option()],
    rationale: Annotated[str, typer.Option()],
) -> None:
    """Record the researcher's explicit hypothesis selection and rationale."""
    root = project_root()
    console.print(
        activate_hypothesis(
            root,
            proposal_set,
            option,
            title=title,
            statement=statement,
            selected_by=selected_by,
            rationale=rationale,
        )
    )
    _show_next(root)


@experiment_app.command("new")
def experiment_new(
    title: Annotated[str, typer.Option()],
    hypothesis: Annotated[str | None, typer.Option()] = None,
    purpose: Annotated[str | None, typer.Option()] = None,
) -> None:
    """Create a linked or exploratory experiment with a readable entrypoint."""
    root = project_root()
    console.print(
        create_experiment(
            root,
            title=title,
            hypothesis_id=hypothesis,
            purpose=purpose,
            enforce_protocol=True,
        )
    )
    build_code_index(root)
    _show_next(root)


@iteration_app.command("new")
def iteration_new(
    experiment: Annotated[str, typer.Option()],
    from_iteration: Annotated[str, typer.Option("--from")],
) -> None:
    """Fork a method into a new immutable iteration for a meaningful change."""
    root = project_root()
    console.print(new_iteration(root, experiment, from_iteration))
    build_code_index(root)
    _show_next(root)


@decision_app.command("record")
def decision_record(
    experiment: Annotated[str, typer.Option()],
    iteration: Annotated[str, typer.Option()],
    run: Annotated[str, typer.Option()],
    decision: Annotated[Decision, typer.Option()],
    rationale: Annotated[str, typer.Option()],
    decided_by: Annotated[str, typer.Option()],
) -> None:
    """Append an explicit human interpretation decision for one run."""
    root = project_root()
    console.print(
        record_decision(
            root,
            experiment_id=experiment,
            iteration_id=iteration,
            run_id=run,
            decision=decision,
            rationale=rationale,
            decided_by=decided_by,
        )
    )
    _show_next(root)


def run_command(
    ctx: typer.Context,
    experiment: Annotated[str, typer.Option()],
    iteration: Annotated[str, typer.Option()],
    backend: Annotated[str, typer.Option("--backend")] = "local",
    cpus: Annotated[int, typer.Option("--cpus", min=1)] = 1,
    memory_mib: Annotated[int, typer.Option("--memory-mib", min=64)] = 1024,
    wall_minutes: Annotated[int, typer.Option("--wall-minutes", min=1)] = 60,
    gpus: Annotated[int, typer.Option("--gpus", min=0)] = 0,
    partition: Annotated[str | None, typer.Option("--partition")] = None,
    account: Annotated[str | None, typer.Option("--account")] = None,
    qos: Annotated[str | None, typer.Option("--qos")] = None,
) -> None:
    """Execute an iteration through SMAIRT's provenance-capturing runner."""
    command = list(ctx.args)
    if command and command[0] == "--":
        command = command[1:]
    if backend == "slurm":
        job = submit_slurm(
            project_root(),
            experiment_id=experiment,
            iteration_id=iteration,
            command=command,
            resources=ComputeResources(
                cpus=cpus,
                memory_mib=memory_mib,
                wall_minutes=wall_minutes,
                gpus=gpus,
                partition=partition,
                account=account,
                qos=qos,
            ),
        )
        emit(job.model_dump(mode="json", exclude_none=True), False)
        return
    if backend != "local":
        raise typer.BadParameter("backend must be local or slurm")
    record = run_experiment(
        project_root(), experiment_id=experiment, iteration_id=iteration, command=command
    )
    emit(record.model_dump(mode="json", exclude_none=True), False)
    if record.exit_code:
        raise typer.Exit(record.exit_code)
    _show_next(project_root())


def amend_command(
    record: Annotated[Path, typer.Option()],
    field: Annotated[str, typer.Option()],
    previous: Annotated[str, typer.Option()],
    corrected: Annotated[str, typer.Option()],
    reason: Annotated[str, typer.Option()],
) -> None:
    """Append a contributor-attributed correction without changing its target."""
    console.print(amend_artifact(project_root(), record, field, previous, corrected, reason))


def retract_command(
    run: Annotated[str, typer.Option()], reason: Annotated[str, typer.Option()]
) -> None:
    """Retract accepted evidence and invalidate dependent records."""
    console.print(correct_run(project_root(), "retract", run, reason))


def supersede_command(
    run: Annotated[str, typer.Option()],
    replacement_run: Annotated[str, typer.Option("--replacement-run")],
    reason: Annotated[str, typer.Option()],
) -> None:
    """Link old evidence to a verified replacement and invalidate dependents."""
    console.print(correct_run(project_root(), "supersede", run, reason, replacement_run))


def register_root_commands(app: typer.Typer) -> None:
    """Attach lifecycle commands that intentionally remain at the root CLI level."""
    app.command("run", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})(
        run_command
    )
    app.command("amend")(amend_command)
    app.command("retract")(retract_command)
    app.command("supersede")(supersede_command)
