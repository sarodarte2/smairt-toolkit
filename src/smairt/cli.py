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
from smairt.code_quality import build_code_index, validate_code
from smairt.guidance import next_guidance
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
    validate_background,
    validate_proposal_set,
)
from smairt.runner import run_experiment
from smairt.scaffold import conda_environments, create_project
from smairt.tui import run_new_project, run_project_menu
from smairt.upgrade import upgrade_project

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
code_app = typer.Typer(help="Index and validate readable research code")

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
app.add_typer(code_app, name="code")


def _root() -> Path:
    """Resolve the current project or terminate a command with a clear error."""
    try:
        return find_project()
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(2) from exc


def _emit(payload: object, as_json: bool) -> None:
    """Render payloads either as stable JSON or readable Rich output."""
    if as_json:
        console.print_json(json.dumps(payload, default=str))
    else:
        console.print(payload)


def _show_guidance(root: Path) -> None:
    """Print the compact completed/recommended/alternatives handoff footer."""
    guidance = next_guidance(root)
    console.print(f"\n[bold #f28c28]Completed:[/] {guidance['completed']}")
    recommended = guidance.get("recommended")
    if recommended:
        console.print(f"[bold]Recommended next:[/] {recommended['label']}")
    alternatives = [item["label"] for item in guidance["actions"] if item is not recommended]
    if alternatives:
        console.print("[dim]Other options: " + " · ".join(alternatives) + "[/dim]")


@app.callback()
def main(
    ctx: typer.Context,
    version: Annotated[bool, typer.Option("--version", help="Show the installed version.")] = False,
) -> None:
    """Handle global version output and show help when no command is selected."""
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
    allow_existing: bool = False,
) -> None:
    """Share interactive and non-interactive creation behavior across aliases."""
    if not name or not author:
        created = run_new_project(destination, allow_existing=allow_existing)
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
        allow_existing=allow_existing,
    )
    console.print(f"[bold #f28c28]Created {config.project.name}[/] at {destination}")
    _show_guidance(destination)


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
        False,
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
        False,
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
        True,
    )


@app.command("menu")
def menu_command() -> None:
    """Open the editable project dashboard."""
    run_project_menu(_root())


@app.command("upgrade")
def upgrade_command(
    apply: Annotated[bool, typer.Option("--apply")] = False,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Preview or apply safe framework-managed guidance updates."""
    root = _root()
    payload = upgrade_project(root, apply=apply)
    _emit(payload, as_json)
    if apply:
        _show_guidance(root)


@app.command("status")
def status_command(
    as_json: Annotated[bool, typer.Option("--json")] = False,
    compact: Annotated[bool, typer.Option("--compact")] = False,
) -> None:
    """Show project identity, active artifacts, health, and optionally full JSON."""
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
    """Run structural, safety, code, provenance, and readiness validation."""
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
    """Return only the initial files relevant to the requested research task."""
    payload = build_context(_root(), task)
    _emit(payload, as_json)


@app.command("next")
def next_command(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Show the state-aware next actions for this research project."""
    payload = next_guidance(_root())
    if as_json:
        _emit(payload, True)
    else:
        _show_guidance(_root())


@code_app.command("index")
def code_index(
    check: Annotated[bool, typer.Option("--check")] = False,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Build the AST-derived code index, or check whether it is current."""
    root = _root()
    payload = build_code_index(root, write=not check)
    if check:
        path = root / "scripts/CODE_INDEX.yaml"
        current = yaml.safe_load(path.read_text()) if path.exists() else None
        payload = {"current": current == payload, "index": payload}
        if not payload["current"]:
            _emit(payload, as_json)
            raise typer.Exit(1)
    _emit(payload, as_json)


@code_app.command("validate")
def code_validate(
    path: Annotated[Path | None, typer.Argument()] = None,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Report human-readability and traceability findings without blocking research."""
    root = _root()
    target = (root / path).resolve() if path and not path.is_absolute() else path
    findings = validate_code(root, target)
    _emit(
        {"ok": not any(item["severity"] == "error" for item in findings), "findings": findings},
        as_json,
    )


@reference_app.command("list")
def reference_list(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """List indexed references without loading their full PDF content."""
    records = [record.model_dump(mode="json", exclude_none=True) for record in load_index(_root())]
    _emit(records, as_json)


@reference_app.command("scan")
def reference_scan(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Report local PDFs that have not yet been indexed by checksum."""
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
    """Inspect, confirm, and index one local scholarly PDF."""
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
    """Create the initial-background synthesis workspace and show what follows."""
    root = _root()
    console.print(create_background(root))
    _show_guidance(root)


@background_app.command("validate")
def background_validate() -> None:
    """Check background structure and grounding against indexed references."""
    errors = validate_background(_root())
    _emit({"ok": not errors, "errors": errors}, False)
    if errors:
        raise typer.Exit(1)


@proposal_app.command("new")
def proposal_new() -> None:
    """Create a retained three-option hypothesis proposal set."""
    root = _root()
    console.print(create_proposal_set(root))
    _show_guidance(root)


@proposal_app.command("validate")
def proposal_validate(path: Annotated[Path, typer.Argument()]) -> None:
    """Validate proposal completeness before a researcher chooses an option."""
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
    """Record the researcher's explicit hypothesis selection and rationale."""
    root = _root()
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
    _show_guidance(root)


@experiment_app.command("new")
def experiment_new(
    title: Annotated[str, typer.Option()],
    hypothesis: Annotated[str | None, typer.Option()] = None,
    purpose: Annotated[str | None, typer.Option()] = None,
) -> None:
    """Create a linked or exploratory experiment with a readable entrypoint."""
    root = _root()
    console.print(create_experiment(root, title=title, hypothesis_id=hypothesis, purpose=purpose))
    build_code_index(root)
    _show_guidance(root)


@iteration_app.command("new")
def iteration_new(
    experiment: Annotated[str, typer.Option()],
    from_iteration: Annotated[str, typer.Option("--from")],
) -> None:
    """Fork a method into a new immutable iteration for a meaningful change."""
    root = _root()
    console.print(new_iteration(root, experiment, from_iteration))
    build_code_index(root)
    _show_guidance(root)


@app.command("run", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def run_command(
    ctx: typer.Context,
    experiment: Annotated[str, typer.Option()],
    iteration: Annotated[str, typer.Option()],
) -> None:
    """Execute an iteration through SMAIRT's provenance-capturing runner."""
    command = list(ctx.args)
    if command and command[0] == "--":
        command = command[1:]
    record = run_experiment(
        _root(), experiment_id=experiment, iteration_id=iteration, command=command
    )
    _emit(record.model_dump(mode="json", exclude_none=True), False)
    if record.exit_code:
        raise typer.Exit(record.exit_code)
    _show_guidance(_root())


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
    root = _root()
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
    _show_guidance(root)


@app.command("amend")
def amend_command(
    record: Annotated[Path, typer.Option()],
    field: Annotated[str, typer.Option()],
    previous: Annotated[str, typer.Option()],
    corrected: Annotated[str, typer.Option()],
    reason: Annotated[str, typer.Option()],
) -> None:
    """Append a field correction beside an immutable record."""
    amend_record(record, field=field, previous=previous, corrected=corrected, reason=reason)


def _change_selection_status(experiment: str, status: str, reason: str) -> None:
    """Invalidate a current accepted selection while preserving its history."""
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
    """Mark accepted experiment evidence as invalid and retain the reason."""
    _change_selection_status(experiment, "RETRACTED", reason)


@app.command("supersede")
def supersede_command(
    experiment: Annotated[str, typer.Option()],
    reason: Annotated[str, typer.Option()],
) -> None:
    """Mark accepted evidence as replaced so corrected evidence can follow."""
    _change_selection_status(experiment, "SUPERSEDED", reason)


@paper_app.command("validate")
def paper_validate() -> None:
    """Reject paper elements not backed by current accepted run evidence."""
    errors = validate_paper(_root())
    _emit({"ok": not errors, "errors": errors}, False)
    if errors:
        raise typer.Exit(1)


@env_app.command("status")
def env_status(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Show the configured environment and locally discoverable Conda options."""
    config = SmairtConfig.load(_root() / "smairt.yaml")
    payload = {
        "configured": config.environment.model_dump(mode="json", exclude_none=True),
        "available_conda_environments": conda_environments(),
    }
    _emit(payload, as_json)


@env_app.command("shell")
def env_shell() -> None:
    """Open a shell inside the configured environment when one is managed."""
    config = SmairtConfig.load(_root() / "smairt.yaml")
    shell = os.environ.get("SHELL", "/bin/sh")
    if config.environment.mode is EnvironmentMode.NEW_CONDA and config.environment.name:
        command = ["conda", "run", "-n", config.environment.name, shell]
    elif config.environment.mode is EnvironmentMode.EXISTING_CONDA and config.environment.prefix:
        command = ["conda", "run", "-p", config.environment.prefix, shell]
    else:
        command = [shell]
    raise typer.Exit(subprocess.run(command, check=False).returncode)
