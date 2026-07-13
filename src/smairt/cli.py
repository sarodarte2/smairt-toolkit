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
from smairt.contracts import check_contracts, export_contracts
from smairt.corrections import amend_artifact, correct_run
from smairt.guidance import next_guidance
from smairt.harnesses import harness_status, install_harness, list_harnesses
from smairt.integrity import verify_run
from smairt.migrations import apply_migration, detect_scaffold, migration_plan, rollback_migration
from smairt.models import DataClassification, Decision, EnvironmentMode, SmairtConfig
from smairt.paper import (
    begin_paper,
    build_paper,
    create_claim,
    create_evidence_card,
    review_claim,
    review_section,
    validate_paper,
)
from smairt.project import context as build_context
from smairt.project import find_project, validate_project
from smairt.project import status as project_status
from smairt.provenance import add_contributor, generate_history, load_events, use_contributor
from smairt.references import (
    add_reference,
    edit_reference,
    enrich_reference,
    export_references,
    get_reference,
    inspect_pdf,
    load_index,
    unindexed_pdfs,
    verify_reference,
)
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
from smairt.safety import release_check, safety_status, set_safety_mode
from smairt.scaffold import conda_environments, create_project
from smairt.summaries import create_summary, list_summaries, promote_summary
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
contributor_app = typer.Typer(help="Manage confirmed project contributors")
safety_app = typer.Typer(help="Inspect and change project safety policy")
contract_app = typer.Typer(help="Export and check portable harness contracts")
harness_app = typer.Typer(help="Install and inspect coding-harness adapters")
migrate_app = typer.Typer(help="Plan, apply, and roll back schema migrations")
summary_app = typer.Typer(help="Manage contributor-scoped source summaries")
paper_section_app = typer.Typer(help="Draft and review manuscript sections")
paper_evidence_app = typer.Typer(help="Manage immutable paper evidence cards")
paper_claim_app = typer.Typer(help="Manage human-reviewed manuscript claims")

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
app.add_typer(contributor_app, name="contributor")
app.add_typer(safety_app, name="safety")
app.add_typer(contract_app, name="contract")
app.add_typer(harness_app, name="harness")
app.add_typer(migrate_app, name="migrate")
app.add_typer(summary_app, name="summary")
paper_app.add_typer(paper_evidence_app, name="evidence")
paper_app.add_typer(paper_claim_app, name="claim")
paper_app.add_typer(paper_section_app, name="section")


@contributor_app.command("add")
def contributor_add(
    name: Annotated[str, typer.Option()], email: Annotated[str | None, typer.Option()] = None
) -> None:
    """Register a contributor from explicitly supplied identity fields."""
    _emit(add_contributor(_root(), name, email).model_dump(mode="json", exclude_none=True), False)


@contributor_app.command("list")
def contributor_list(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    config = SmairtConfig.load(_root() / "smairt.yaml")
    _emit(
        {
            "active": config.active_contributor,
            "contributors": [
                c.model_dump(mode="json", exclude_none=True) for c in config.contributors
            ],
        },
        as_json,
    )


@contributor_app.command("use")
def contributor_use(identifier: Annotated[str, typer.Argument()]) -> None:
    _emit(use_contributor(_root(), identifier).model_dump(mode="json", exclude_none=True), False)


@contributor_app.command("confirm-git")
def contributor_confirm_git(yes: Annotated[bool, typer.Option("--yes")] = False) -> None:
    """Suggest Git identity but store it only after explicit confirmation."""
    root = _root()
    name = subprocess.run(
        ["git", "config", "user.name"], cwd=root, capture_output=True, text=True
    ).stdout.strip()
    email = subprocess.run(
        ["git", "config", "user.email"], cwd=root, capture_output=True, text=True
    ).stdout.strip()
    if not name:
        raise typer.BadParameter("Git user.name is not configured")
    if not yes and not Confirm.ask(f"Register Git identity {name} <{email}>?", default=False):
        raise typer.Exit()
    contributor = add_contributor(root, name, email or None, source="confirmed_git")
    use_contributor(root, contributor.id)
    _emit(contributor.model_dump(mode="json", exclude_none=True), False)


@app.command("history")
def history_command(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    root = _root()
    generate_history(root)
    _emit(load_events(root), as_json)


@app.command("doctor")
def doctor_command(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Diagnose scaffold, Git, contract, and adapter health without writing files."""
    root = _root()
    validation = validate_project(root).as_dict()
    payload = {
        "ok": validation["ok"] and detect_scaffold(root) == "v2",
        "scaffold": detect_scaffold(root),
        "git_repository": (root / ".git").exists(),
        "validation": validation,
        "harnesses": list_harnesses(root),
        "migration": migration_plan(root),
    }
    _emit(payload, as_json)
    if not payload["ok"]:
        raise typer.Exit(1)


@safety_app.command("status")
def safety_status_command(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    _emit(safety_status(_root()), as_json)


@safety_app.command("set")
def safety_set(
    mode: Annotated[str, typer.Argument()], yes: Annotated[bool, typer.Option("--yes")] = False
) -> None:
    if not yes and not Confirm.ask(f"Change safety mode to {mode}?", default=False):
        raise typer.Exit()
    _emit(set_safety_mode(_root(), mode), False)


@safety_app.command("release-check")
def safety_release_check(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    payload = release_check(_root())
    _emit(payload, as_json)
    if not payload["ok"]:
        raise typer.Exit(1)


@app.command("verify")
def verify_command(
    run: Annotated[str | None, typer.Option()] = None,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    payload = verify_run(_root(), run)
    _emit(payload, as_json)
    if not payload["ok"]:
        raise typer.Exit(1)


@contract_app.command("export")
def contract_export(destination: Annotated[Path | None, typer.Option()] = None) -> None:
    root = _root()
    _emit(export_contracts(destination or root / ".smairt/contracts/v1"), False)


@contract_app.command("check")
def contract_check(destination: Annotated[Path | None, typer.Option()] = None) -> None:
    root = _root()
    payload = check_contracts(destination or root / ".smairt/contracts/v1")
    _emit(payload, False)
    if not payload["ok"]:
        raise typer.Exit(1)


@harness_app.command("list")
def harness_list(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    _emit(list_harnesses(_root()), as_json)


@harness_app.command("status")
def harness_status_command(
    harness: Annotated[str, typer.Argument()],
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    _emit(harness_status(_root(), harness), as_json)


@harness_app.command("install")
def harness_install(harness: Annotated[str, typer.Argument()]) -> None:
    _emit(install_harness(_root(), harness), False)


@harness_app.command("upgrade")
def harness_upgrade(harness: Annotated[str, typer.Argument()]) -> None:
    _emit(install_harness(_root(), harness, upgrade=True), False)


@migrate_app.command("plan")
def migrate_plan_command(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    _emit(migration_plan(_root()), as_json)


@migrate_app.command("apply")
def migrate_apply(
    contributor: Annotated[str | None, typer.Option()] = None,
    allow_dirty: Annotated[bool, typer.Option("--allow-dirty")] = False,
) -> None:
    _emit(apply_migration(_root(), contributor, allow_dirty=allow_dirty), False)


@migrate_app.command("rollback")
def migrate_rollback(yes: Annotated[bool, typer.Option("--yes")] = False) -> None:
    if not yes and not Confirm.ask("Roll back the last migration?", default=False):
        raise typer.Exit()
    _emit(rollback_migration(_root()), False)


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
    token_budget: Annotated[int, typer.Option("--token-budget", min=1)] = 8000,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Return only the initial files relevant to the requested research task."""
    payload = build_context(_root(), task, token_budget)
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


@reference_app.command("inspect")
def reference_inspect(identifier: Annotated[str, typer.Argument()]) -> None:
    _emit(get_reference(_root(), identifier).model_dump(mode="json", exclude_none=True), False)


@reference_app.command("enrich")
def reference_enrich(identifier: Annotated[str, typer.Argument()]) -> None:
    _emit(enrich_reference(_root(), identifier).model_dump(mode="json", exclude_none=True), False)


@reference_app.command("edit")
def reference_edit(
    identifier: Annotated[str, typer.Argument()],
    field: Annotated[str, typer.Option()],
    value: Annotated[str, typer.Option()],
) -> None:
    contributor = SmairtConfig.load(_root() / "smairt.yaml").active_contributor
    if not contributor:
        raise typer.BadParameter("select an active contributor first")
    _emit(
        edit_reference(_root(), identifier, field, value, contributor).model_dump(
            mode="json", exclude_none=True
        ),
        False,
    )


@reference_app.command("verify")
def reference_verify(identifier: Annotated[str, typer.Argument()]) -> None:
    contributor = SmairtConfig.load(_root() / "smairt.yaml").active_contributor
    if not contributor:
        raise typer.BadParameter("select an active contributor first")
    _emit(
        verify_reference(_root(), identifier, contributor).model_dump(
            mode="json", exclude_none=True
        ),
        False,
    )


@reference_app.command("export")
def reference_export(
    format_name: Annotated[str, typer.Option("--format")],
    output: Annotated[Path | None, typer.Option()] = None,
) -> None:
    """Export the reference index as BibTeX or CSL JSON."""
    content = export_references(_root(), format_name)
    if output:
        output.write_text(content, encoding="utf-8")
        console.print(output)
    else:
        console.print(content, markup=False)


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
    """Append a contributor-attributed correction without changing its target."""
    root = _root()
    console.print(amend_artifact(root, record, field, previous, corrected, reason))


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
    run: Annotated[str, typer.Option()],
    reason: Annotated[str, typer.Option()],
) -> None:
    """Retract accepted evidence and invalidate dependent records."""
    console.print(correct_run(_root(), "retract", run, reason))


@app.command("supersede")
def supersede_command(
    run: Annotated[str, typer.Option()],
    replacement_run: Annotated[str, typer.Option("--replacement-run")],
    reason: Annotated[str, typer.Option()],
) -> None:
    """Link old evidence to a verified replacement and invalidate dependents."""
    console.print(correct_run(_root(), "supersede", run, reason, replacement_run))


@paper_app.command("validate")
def paper_validate() -> None:
    """Reject paper elements not backed by current accepted run evidence."""
    errors = validate_paper(_root())
    _emit({"ok": not errors, "errors": errors}, False)
    if errors:
        raise typer.Exit(1)


@paper_app.command("status")
def paper_status(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    root = _root()
    claims = [
        json.loads(path.read_text()) for path in sorted((root / "paper/claims").glob("*.json"))
    ]
    payload = {
        "evidence_cards": len(list((root / "paper/evidence").glob("*.json"))),
        "claims": {
            state: sum(c.get("status") == state for c in claims)
            for state in ("proposed", "approved", "rejected", "superseded", "retracted")
        },
        "manuscript_started": (root / "paper/manuscript.md").exists(),
    }
    _emit(payload, as_json)


@paper_evidence_app.command("list")
def paper_evidence_list(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    root = _root()
    items = [
        json.loads(path.read_text()) for path in sorted((root / "paper/evidence").glob("*.json"))
    ]
    _emit(items, as_json)


@paper_evidence_app.command("review")
def paper_evidence_review(
    run: Annotated[str, typer.Option()],
    purpose: Annotated[str, typer.Option()],
    observed_result: Annotated[str, typer.Option()],
    limitations: Annotated[str, typer.Option()],
    decision: Annotated[str, typer.Option()],
    relevance: Annotated[str, typer.Option()] = "",
) -> None:
    console.print(
        create_evidence_card(
            _root(),
            run,
            purpose=purpose,
            observed_result=observed_result,
            limitations=limitations,
            decision=decision,
            relevance=relevance,
        )
    )


@paper_claim_app.command("propose")
def paper_claim_propose(
    statement: Annotated[str, typer.Option()],
    evidence: Annotated[list[str], typer.Option()],
    reference: Annotated[list[str] | None, typer.Option()] = None,
) -> None:
    console.print(create_claim(_root(), statement, evidence, reference))


def _claim_review_command(identifier: str, status: str, yes: bool) -> None:
    if not yes and not Confirm.ask(f"Mark {identifier} {status}?", default=False):
        raise typer.Exit()
    _emit(review_claim(_root(), identifier, status), False)


@paper_claim_app.command("approve")
def paper_claim_approve(
    identifier: Annotated[str, typer.Argument()],
    yes: Annotated[bool, typer.Option("--yes")] = False,
) -> None:
    _claim_review_command(identifier, "approved", yes)


@paper_claim_app.command("reject")
def paper_claim_reject(
    identifier: Annotated[str, typer.Argument()],
    yes: Annotated[bool, typer.Option("--yes")] = False,
) -> None:
    _claim_review_command(identifier, "rejected", yes)


@paper_app.command("begin")
def paper_begin(title: Annotated[str, typer.Option()]) -> None:
    console.print(begin_paper(_root(), title))


@paper_section_app.command("review")
def paper_section_review(
    section: Annotated[str, typer.Argument()],
    claim: Annotated[list[str], typer.Option()],
    yes: Annotated[bool, typer.Option("--yes")] = False,
) -> None:
    if not yes and not Confirm.ask(f"Mark {section} reviewed?", default=False):
        raise typer.Exit()
    _emit(review_section(_root(), section, claim), False)


@paper_app.command("build")
def paper_build(format_name: Annotated[str, typer.Option("--format")]) -> None:
    console.print(build_paper(_root(), format_name))


@summary_app.command("create")
def summary_create(
    source: Annotated[Path, typer.Argument()],
    content: Annotated[str, typer.Option()],
    shareable: Annotated[bool, typer.Option("--shareable")] = False,
    redaction_confirmed: Annotated[bool, typer.Option("--redaction-confirmed")] = False,
) -> None:
    console.print(
        create_summary(
            _root(),
            source,
            content,
            shareable=shareable,
            redaction_confirmed=redaction_confirmed,
        )
    )


@summary_app.command("list")
def summary_list(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    _emit(list_summaries(_root()), as_json)


@summary_app.command("compare")
def summary_compare(source_id: Annotated[str, typer.Argument()]) -> None:
    _emit([item for item in list_summaries(_root()) if item["source_id"] == source_id], False)


@summary_app.command("promote")
def summary_promote(identifier: Annotated[str, typer.Argument()]) -> None:
    console.print(promote_summary(_root(), identifier))


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
