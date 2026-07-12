"""Public SMAIRT command-line interface."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Annotated

import typer
import yaml
from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt

from smairt import __version__
from smairt.models import DataClassification, Decision, EnvironmentMode, SmairtConfig
from smairt.paper import validate_paper
from smairt.project import context as build_context
from smairt.project import find_project, validate_project
from smairt.project import status as project_status
from smairt.references import add_reference, inspect_pdf, load_index, unindexed_pdfs
from smairt.research import (
    activate_hypothesis,
    amend_record,
    create_background,
    create_experiment,
    create_proposal_set,
    new_iteration,
    record_decision,
    validate_proposal_set,
)
from smairt.runner import run_experiment
from smairt.scaffold import conda_environments, create_project
from smairt.tui import run_new_project, run_project_menu

console = Console()
app = typer.Typer(
    help="Scientific Method with AI Research Toolkit",
    no_args_is_help=True,
    invoke_without_command=True,
)
start_app = typer.Typer(help="Friendly project-start aliases")
reference_app = typer.Typer(help="Manage local scholarly references")
background_app = typer.Typer(help="Manage source-grounded project background")
hypothesis_app = typer.Typer(help="Manage proposal sets and human-selected hypotheses")
proposal_app = typer.Typer(help="Create and validate three-option proposal sets")
experiment_app = typer.Typer(help="Manage experiments")
iteration_app = typer.Typer(help="Manage immutable research iterations")
decision_app = typer.Typer(help="Record human research decisions")
paper_app = typer.Typer(help="Manage paper evidence provenance")
env_app = typer.Typer(help="Inspect and enter the project environment")

app.add_typer(start_app, name="start")
app.add_typer(reference_app, name="reference")
app.add_typer(background_app, name="background")
app.add_typer(hypothesis_app, name="hypothesis")
hypothesis_app.add_typer(proposal_app, name="proposals")
app.add_typer(experiment_app, name="experiment")
app.add_typer(iteration_app, name="iteration")
app.add_typer(decision_app, name="decision")
app.add_typer(paper_app, name="paper")
app.add_typer(env_app, name="env")


def _root() -> Path:
    try:
        return find_project()
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(2) from exc


def _emit(payload: object, as_json: bool) -> None:
    if as_json:
        console.print_json(json.dumps(payload, default=str))
    else:
        console.print(payload)


@app.callback()
def main(
    ctx: typer.Context,
    version: Annotated[bool, typer.Option("--version", help="Show the installed version.")] = False,
) -> None:
    if version:
        console.print(__version__)
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


def _new_project(
    destination: Path | None,
    name: str | None,
    author: str | None,
    question: str | None,
    description: str | None,
    classification: DataClassification,
    git: bool,
    environment_mode: EnvironmentMode,
    environment_name: str | None,
) -> None:
    if not name or not author:
        created = run_new_project(destination)
        if created:
            console.print(f"[bold #f28c28]Created SMAIRT project:[/] {created}")
        return
    destination = (destination or Path(name.lower().replace(" ", "-"))).resolve()
    config = create_project(
        destination,
        name=name,
        author=author,
        question=question,
        description=description,
        classification=classification,
        initialize_git=git,
        environment_mode=environment_mode,
        environment_name=environment_name,
        create_environment=environment_mode is EnvironmentMode.NEW_CONDA,
    )
    console.print(f"[bold #f28c28]Created {config.project.name}[/] at {destination}")


@app.command("new")
def new_command(
    destination: Annotated[Path | None, typer.Argument()] = None,
    name: Annotated[str | None, typer.Option()] = None,
    author: Annotated[str | None, typer.Option()] = None,
    question: Annotated[str | None, typer.Option()] = None,
    description: Annotated[str | None, typer.Option()] = None,
    classification: Annotated[DataClassification, typer.Option()] = DataClassification.UNPUBLISHED,
    git: Annotated[bool, typer.Option("--git/--no-git")] = True,
    environment: Annotated[EnvironmentMode, typer.Option()] = EnvironmentMode.NONE,
    environment_name: Annotated[str | None, typer.Option()] = None,
) -> None:
    """Create a new project; opens the TUI when name/author are omitted."""
    _new_project(
        destination,
        name,
        author,
        question,
        description,
        classification,
        git,
        environment,
        environment_name,
    )


@start_app.command("project")
def start_project(
    destination: Annotated[Path | None, typer.Argument()] = None,
) -> None:
    """Friendly alias for the interactive project wizard."""
    _new_project(
        destination,
        None,
        None,
        None,
        None,
        DataClassification.UNPUBLISHED,
        True,
        EnvironmentMode.NONE,
        None,
    )


@app.command("init")
def init_command(
    destination: Annotated[Path | None, typer.Argument()] = None,
    name: Annotated[str | None, typer.Option()] = None,
    author: Annotated[str | None, typer.Option()] = None,
) -> None:
    """Initialize an existing directory, interactively by default."""
    _new_project(
        destination or Path.cwd(),
        name,
        author,
        None,
        None,
        DataClassification.UNPUBLISHED,
        True,
        EnvironmentMode.NONE,
        None,
    )


@app.command("menu")
def menu_command() -> None:
    """Open the editable project dashboard."""
    run_project_menu(_root())


@app.command("status")
def status_command(
    as_json: Annotated[bool, typer.Option("--json")] = False,
    compact: Annotated[bool, typer.Option("--compact")] = False,
) -> None:
    payload = project_status(_root())
    if as_json:
        _emit(payload, True)
        return
    project = payload["project"]
    console.print(f"[bold #f28c28]{project['name']}[/] · {payload['data_classification']}")
    console.print(f"Author: {project['author']}")
    console.print(f"Active: {payload['active'] or 'none'}")
    validation = payload["validation"]
    console.print(f"Validation: {'PASS' if validation['ok'] else 'FAIL'}")
    if not compact:
        console.print(payload["counts"])
        for warning in validation["warnings"]:
            console.print(f"[yellow]Warning:[/] {warning}")


@app.command("validate")
def validate_command(
    as_json: Annotated[bool, typer.Option("--json")] = False,
    staged: Annotated[bool, typer.Option("--staged")] = False,
    tool_input: Annotated[bool, typer.Option("--tool-input", hidden=True)] = False,
) -> None:
    report = validate_project(_root(), staged=staged, tool_input=tool_input)
    if as_json:
        _emit(report.as_dict(), True)
    else:
        console.print("[green]PASS[/]" if report.ok else "[red]FAIL[/]")
        for error in report.errors:
            console.print(f"[red]Error:[/] {error}")
        for warning in report.warnings:
            console.print(f"[yellow]Warning:[/] {warning}")
    if not report.ok:
        raise typer.Exit(1)


@app.command("context")
def context_command(
    task: Annotated[str, typer.Option(help="planning, code, run, interpretation, or paper")],
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    payload = build_context(_root(), task)
    _emit(payload, as_json)


@reference_app.command("list")
def reference_list(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    records = [record.model_dump(mode="json", exclude_none=True) for record in load_index(_root())]
    _emit(records, as_json)


@reference_app.command("scan")
def reference_scan(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    paths = [str(path) for path in unindexed_pdfs(_root())]
    _emit({"unindexed": paths}, as_json)


@reference_app.command("add")
def reference_add(
    source: Annotated[Path, typer.Argument()],
    title: Annotated[str | None, typer.Option()] = None,
    authors: Annotated[list[str] | None, typer.Option()] = None,
    year: Annotated[int | None, typer.Option()] = None,
    doi: Annotated[str | None, typer.Option()] = None,
    verified: Annotated[bool, typer.Option("--verified")] = False,
    link: Annotated[bool, typer.Option("--link")] = False,
    yes: Annotated[bool, typer.Option("--yes")] = False,
) -> None:
    proposed = inspect_pdf(source)
    title = title or str(proposed["title"])
    authors = authors or list(proposed["authors"])
    doi = doi or proposed["doi"]
    if not yes:
        console.print({"title": title, "authors": authors, "year": year, "doi": doi})
        title = Prompt.ask("Confirmed title", default=title)
        if year is None:
            entered = IntPrompt.ask("Year (0 if unknown)", default=0)
            year = entered or None
        verified = Confirm.ask("Have you verified this metadata?", default=False)
        if not Confirm.ask("Add this local reference?", default=True):
            raise typer.Exit()
    record = add_reference(
        _root(),
        source,
        title=title,
        authors=authors,
        year=year,
        doi=doi,
        verified=verified,
        link=link,
    )
    _emit(record.model_dump(mode="json", exclude_none=True), False)


@background_app.command("create")
def background_create() -> None:
    console.print(create_background(_root()))


@background_app.command("validate")
def background_validate() -> None:
    path = _root() / "background/initial_background.md"
    content = path.read_text()
    errors = []
    if "[Codex:" in content:
        errors.append("background still contains synthesis placeholder")
    if "## References Used" not in content:
        errors.append("background lacks References Used section")
    _emit({"ok": not errors, "errors": errors}, False)
    if errors:
        raise typer.Exit(1)


@proposal_app.command("new")
def proposal_new() -> None:
    console.print(create_proposal_set(_root()))


@proposal_app.command("validate")
def proposal_validate(path: Annotated[Path, typer.Argument()]) -> None:
    errors = validate_proposal_set(path)
    _emit({"ok": not errors, "errors": errors}, False)
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
    console.print(
        activate_hypothesis(
            _root(),
            proposal_set,
            option,
            title=title,
            statement=statement,
            selected_by=selected_by,
            rationale=rationale,
        )
    )


@experiment_app.command("new")
def experiment_new(
    title: Annotated[str, typer.Option()],
    hypothesis: Annotated[str | None, typer.Option()] = None,
    purpose: Annotated[str | None, typer.Option()] = None,
) -> None:
    console.print(
        create_experiment(_root(), title=title, hypothesis_id=hypothesis, purpose=purpose)
    )


@iteration_app.command("new")
def iteration_new(
    experiment: Annotated[str, typer.Option()],
    from_iteration: Annotated[str, typer.Option("--from")],
) -> None:
    console.print(new_iteration(_root(), experiment, from_iteration))


@app.command("run", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def run_command(
    ctx: typer.Context,
    experiment: Annotated[str, typer.Option()],
    iteration: Annotated[str, typer.Option()],
) -> None:
    command = list(ctx.args)
    if command and command[0] == "--":
        command = command[1:]
    record = run_experiment(
        _root(), experiment_id=experiment, iteration_id=iteration, command=command
    )
    _emit(record.model_dump(mode="json", exclude_none=True), False)
    if record.exit_code:
        raise typer.Exit(record.exit_code)


@decision_app.command("record")
def decision_record(
    experiment: Annotated[str, typer.Option()],
    iteration: Annotated[str, typer.Option()],
    run: Annotated[str, typer.Option()],
    decision: Annotated[Decision, typer.Option()],
    rationale: Annotated[str, typer.Option()],
    decided_by: Annotated[str, typer.Option()],
) -> None:
    console.print(
        record_decision(
            _root(),
            experiment_id=experiment,
            iteration_id=iteration,
            run_id=run,
            decision=decision,
            rationale=rationale,
            decided_by=decided_by,
        )
    )


@app.command("amend")
def amend_command(
    record: Annotated[Path, typer.Option()],
    field: Annotated[str, typer.Option()],
    previous: Annotated[str, typer.Option()],
    corrected: Annotated[str, typer.Option()],
    reason: Annotated[str, typer.Option()],
) -> None:
    amend_record(record, field=field, previous=previous, corrected=corrected, reason=reason)


def _change_selection_status(experiment: str, status: str, reason: str) -> None:
    path = _root() / "analysis" / experiment / "selection.yaml"
    if not path.exists():
        raise typer.BadParameter("experiment has no accepted selection")
    payload = yaml.safe_load(path.read_text())
    payload["status"] = status
    payload["status_reason"] = reason
    path.write_text(yaml.safe_dump(payload, sort_keys=False))


@app.command("retract")
def retract_command(
    experiment: Annotated[str, typer.Option()],
    reason: Annotated[str, typer.Option()],
) -> None:
    _change_selection_status(experiment, "RETRACTED", reason)


@app.command("supersede")
def supersede_command(
    experiment: Annotated[str, typer.Option()],
    reason: Annotated[str, typer.Option()],
) -> None:
    _change_selection_status(experiment, "SUPERSEDED", reason)


@paper_app.command("validate")
def paper_validate() -> None:
    errors = validate_paper(_root())
    _emit({"ok": not errors, "errors": errors}, False)
    if errors:
        raise typer.Exit(1)


@env_app.command("status")
def env_status(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    config = SmairtConfig.load(_root() / "smairt.yaml")
    payload = {
        "configured": config.environment.model_dump(mode="json", exclude_none=True),
        "available_conda_environments": conda_environments(),
    }
    _emit(payload, as_json)


@env_app.command("shell")
def env_shell() -> None:
    config = SmairtConfig.load(_root() / "smairt.yaml")
    shell = os.environ.get("SHELL", "/bin/sh")
    if config.environment.mode is EnvironmentMode.NEW_CONDA and config.environment.name:
        command = ["conda", "run", "-n", config.environment.name, shell]
    elif config.environment.mode is EnvironmentMode.EXISTING_CONDA and config.environment.prefix:
        command = ["conda", "run", "-p", config.environment.prefix, shell]
    else:
        command = [shell]
    raise typer.Exit(subprocess.run(command, check=False).returncode)
