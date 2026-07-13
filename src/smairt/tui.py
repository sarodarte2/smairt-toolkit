"""Terminal-native prompt workflows for project creation and maintenance."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import TypedDict, TypeVar

from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.shortcuts.choice_input import ChoiceInput
from rich.console import Console
from rich.panel import Panel

from smairt.credentials import delete_credential, set_credential
from smairt.diagnostics import doctor, setup_doctor
from smairt.guidance import next_guidance
from smairt.harnesses import configure_mcp, mcp_status
from smairt.integrations import (
    configure_openalex,
    configure_zotero,
    integration_health,
)
from smairt.migrations import apply_migration
from smairt.models import (
    DataClassification,
    EnvironmentMode,
    HarnessName,
    ProjectLicense,
    SafetyMode,
    SmairtConfig,
    ZoteroLibraryType,
    ZoteroMode,
)
from smairt.project import status
from smairt.provenance import add_contributor, use_contributor
from smairt.references import (
    add_doi_reference,
    attach_reference,
    copy_zotero_attachment,
    import_zotero_collection,
    import_zotero_item,
    load_index,
)
from smairt.scaffold import conda_environments, create_project
from smairt.settings import select_environment, update_project_settings
from smairt.utils import slugify
from smairt.zotero import ZoteroProvider

ORANGE = "#f28c28"
FIELD_SUGGESTIONS = (
    "Machine learning, Data science, Computational biology, Physics, Chemistry, Engineering"
)
console = Console()
T = TypeVar("T")


class WizardValues(TypedDict):
    """Retained values for every creation step."""

    destination: str
    name: str
    author: str
    email: str
    question: str
    description: str
    fields: str
    classification: DataClassification
    license: ProjectLicense
    environment: EnvironmentMode
    environment_name: str
    harness: HarnessName
    safety_mode: SafetyMode
    git: bool
    confirm_contributor: bool
    collaborators: list[tuple[str, str | None]]


class BackNavigation(Exception):
    """Signal Escape without treating ordinary navigation as an error."""


def _back_bindings() -> KeyBindings:
    """Bind Escape to a typed navigation signal for every prompt."""
    bindings = KeyBindings()

    @bindings.add("escape", eager=True)
    def go_back(event: KeyPressEvent) -> None:
        event.app.exit(exception=BackNavigation())

    return bindings


def _select(message: str, options: list[tuple[T, str]], default: T | None = None) -> T:
    """Select one inline option using arrows and Enter, with Escape as back."""
    chooser = ChoiceInput(
        message=message,
        options=options,
        default=default,
        symbol=">",
        key_bindings=_back_bindings(),
    )
    application = chooser._create_application()
    application.ttimeoutlen = 0.05
    return application.run()


def _text(message: str, default: str = "") -> str:
    """Read an editable inline value and preserve the supplied default."""
    session: PromptSession[str] = PromptSession()
    session.app.ttimeoutlen = 0.05
    return session.prompt(f"{message}: ", default=default, key_bindings=_back_bindings()).strip()


def _secret(message: str) -> str:
    """Read a masked credential without retaining it in terminal history."""
    session: PromptSession[str] = PromptSession()
    return session.prompt(f"{message}: ", is_password=True, key_bindings=_back_bindings()).strip()


def _yes_no(message: str, default: bool = True) -> bool:
    """Ask one explicit inline yes/no question."""
    return _select(
        message,
        [(True, "Yes"), (False, "No")],
        default=default,
    )


def _pause() -> None:
    """Keep a result readable before redrawing the next menu."""
    with suppress(BackNavigation):
        _text("Press Enter to continue")


def _header(title: str, subtitle: str = "") -> None:
    """Render a compact terminal-native heading without clearing scrollback."""
    body = f"[bold {ORANGE}]{title}[/]"
    if subtitle:
        body += f"\n[dim]{subtitle}[/dim]"
    console.print(Panel.fit(body, border_style=ORANGE, padding=(0, 2)))


def _preflight_destination(destination: Path, *, allow_existing: bool) -> None:
    """Reject unsafe destinations before a creation confirmation is shown."""
    resolved = destination.expanduser().resolve()
    if (resolved / "smairt.yaml").exists():
        raise FileExistsError("destination is already a SMAIRT project; use 'smairt menu'")
    if (
        resolved.exists()
        and any(resolved.iterdir())
        and not (resolved / ".git").exists()
        and not allow_existing
    ):
        raise FileExistsError(
            "destination contains files; choose an empty folder or use 'smairt init'"
        )


def run_new_project(
    destination: Path | None = None, *, allow_existing: bool = False
) -> Path | None:
    """Run a retained-state creation workflow directly in the shell transcript."""
    values: WizardValues = {
        "destination": str(destination or Path.cwd()),
        "name": "",
        "author": "",
        "email": "",
        "question": "",
        "description": "",
        "fields": "",
        "classification": DataClassification.UNPUBLISHED,
        "license": ProjectLicense.MIT,
        "environment": EnvironmentMode.NONE,
        "environment_name": "",
        "harness": HarnessName.CODEX,
        "safety_mode": SafetyMode.STANDARD,
        "git": True,
        "confirm_contributor": True,
        "collaborators": [],
    }
    step = 0
    while True:
        try:
            if step == 0:
                _header("SMAIRT · New Project", "Step 1 of 5 · Location")
                values["destination"] = _text("Destination", str(values["destination"]))
                values["name"] = _text("Project name", str(values["name"]))
                if not values["name"]:
                    raise ValueError("project name is required")
                _preflight_destination(Path(values["destination"]), allow_existing=allow_existing)
                step = 1
            elif step == 1:
                _header("SMAIRT · New Project", "Step 2 of 5 · Research identity")
                values["question"] = _text(
                    "Initial research question (optional)", values["question"]
                )
                values["description"] = _text(
                    "Project description (optional)", values["description"]
                )
                console.print(f"[dim]Suggestions: {FIELD_SUGGESTIONS}[/dim]")
                values["fields"] = _text(
                    "Fields of study, comma separated (optional)", str(values["fields"])
                )
                step = 2
            elif step == 2:
                _header("SMAIRT · New Project", "Step 3 of 5 · People")
                values["author"] = _text("Primary researcher", str(values["author"]))
                if not values["author"]:
                    raise ValueError("primary researcher is required")
                values["email"] = _text("Email (optional)", str(values["email"]))
                values["confirm_contributor"] = _yes_no(
                    "Register this researcher as the active contributor?",
                    bool(values["confirm_contributor"]),
                )
                collaborators = list(values["collaborators"])
                while _yes_no("Add another collaborator?", False):
                    collaborator_name = _text("Collaborator name")
                    collaborator_email = _text("Collaborator email (optional)")
                    if not collaborator_name:
                        raise ValueError("collaborator name is required")
                    identifiers = {slugify(str(item[0])) for item in collaborators}
                    identifiers.add(slugify(str(values["author"])))
                    if slugify(collaborator_name) in identifiers:
                        raise ValueError("collaborator names must be unique")
                    collaborators.append((collaborator_name, collaborator_email or None))
                values["collaborators"] = collaborators
                step = 3
            elif step == 3:
                _header("SMAIRT · New Project", "Step 4 of 5 · Policy and tools")
                values["classification"] = _select(
                    "Data classification",
                    [(item, item.value.title()) for item in DataClassification],
                    values["classification"],
                )
                values["license"] = _select(
                    "Project license",
                    [(item, item.value) for item in ProjectLicense],
                    values["license"],
                )
                values["environment"] = _select(
                    "Project environment",
                    [
                        (EnvironmentMode.NONE, "No managed environment"),
                        (EnvironmentMode.NEW_CONDA, "Create a new Conda environment"),
                    ],
                    values["environment"],
                )
                if values["environment"] is EnvironmentMode.NEW_CONDA:
                    default_name = values["environment_name"] or (
                        f"smairt-{slugify(values['name'])}"
                    )
                    values["environment_name"] = _text("Conda environment name", default_name)
                values["harness"] = _select(
                    "Coding harness",
                    [(item, item.value.title()) for item in HarnessName],
                    values["harness"],
                )
                values["safety_mode"] = _select(
                    "Safety mode",
                    [(item, item.value.title()) for item in SafetyMode],
                    values["safety_mode"],
                )
                values["git"] = _yes_no("Initialize Git?", bool(values["git"]))
                step = 4
            else:
                _header("SMAIRT · New Project", "Step 5 of 5 · Review")
                console.print(
                    f"[bold]{values['name']}[/] at "
                    f"{Path(values['destination']).expanduser()}\n"
                    f"Researcher: {values['author']} · Fields: {values['fields'] or 'not set'}\n"
                    f"Data: {values['classification'].value} · License: {values['license'].value}\n"
                    f"Environment: {values['environment'].value} · "
                    f"Harness: {values['harness'].value}\n"
                    f"Safety: {values['safety_mode'].value} · Git: {values['git']}"
                )
                action = _select(
                    "Review",
                    [
                        ("create", "Create project"),
                        ("back", "Change choices"),
                        ("cancel", "Cancel"),
                    ],
                    "create",
                )
                if action == "cancel":
                    return None
                if action == "back":
                    step = 3
                    continue
                target = Path(values["destination"]).expanduser().resolve()
                fields = [item.strip() for item in str(values["fields"]).split(",") if item.strip()]
                with console.status("[bold]Creating project…[/bold]", spinner="dots"):
                    create_project(
                        target,
                        name=values["name"],
                        author=values["author"],
                        author_email=values["email"] or None,
                        question=values["question"] or None,
                        description=values["description"] or None,
                        fields_of_study=fields,
                        license_name=values["license"],
                        classification=values["classification"],
                        initialize_git=bool(values["git"]),
                        environment_mode=values["environment"],
                        environment_name=values["environment_name"] or None,
                        create_environment=values["environment"] is EnvironmentMode.NEW_CONDA,
                        harness=values["harness"],
                        safety_mode=values["safety_mode"].value,
                        confirm_contributor=bool(values["confirm_contributor"]),
                        allow_existing=allow_existing,
                    )
                for saved_name, saved_email in values["collaborators"]:
                    add_contributor(target, saved_name, saved_email)
                _header("Project created", str(target))
                console.print(f"Resume later with: [bold]cd {target} && smairt[/bold]")
                if _select(
                    "Next",
                    [(True, "Open project dashboard"), (False, "Return to shell")],
                    True,
                ):
                    run_project_menu(target)
                return target
        except BackNavigation:
            if step == 0:
                return None
            step -= 1
        except (FileExistsError, OSError, ValueError) as exc:
            console.print(f"[red]Cannot continue:[/] {exc}")


def _show_guidance(root: Path, section: str) -> None:
    """Show bounded workflow guidance rather than duplicating expert commands."""
    guidance = next_guidance(root)
    recommended = guidance.get("recommended")
    _header(f"{section}", "Status and command handoff")
    if isinstance(recommended, dict):
        console.print(f"[bold]Recommended:[/] {recommended.get('label')}")
        console.print(f"[cyan]{recommended.get('command') or 'smairt next --json'}[/cyan]")
    else:
        console.print("[cyan]smairt next --json[/cyan]")
    _pause()


def _settings_menu(root: Path) -> None:
    """Edit schema-v3 project metadata without hiding migration requirements."""
    while True:
        config = SmairtConfig.load(root / "smairt.yaml")
        _header("Project Settings", f"Schema v{config.schema_version}")
        try:
            action = _select(
                "Settings",
                [
                    ("edit", "Edit project details"),
                    ("show", "Show current settings"),
                    ("back", "Back"),
                ],
            )
            if action == "back":
                return
            if action == "show":
                console.print(config.project.model_dump(mode="json"))
                _pause()
                continue
            if config.schema_version < 3:
                console.print("Schema v3 is required for fields and license settings.")
                if not _yes_no("Apply the backed-up v2 to v3 migration now?", True):
                    continue
                apply_migration(root, config.active_contributor)
                config = SmairtConfig.load(root / "smairt.yaml")
            name = _text("Project name", config.project.name)
            author = _text("Author or researcher", config.project.author)
            question = _text("Initial question (optional)", config.project.question or "")
            description = _text("Description (optional)", config.project.description or "")
            console.print(f"[dim]Suggestions: {FIELD_SUGGESTIONS}[/dim]")
            fields_text = _text(
                "Fields of study, comma separated",
                ", ".join(config.project.fields_of_study),
            )
            license_name = _select(
                "Project license",
                [(item, item.value) for item in ProjectLicense],
                config.project.license,
            )
            if _yes_no("Save these project settings?", True):
                fields = [item.strip() for item in fields_text.split(",") if item.strip()]
                update_project_settings(
                    root,
                    name=name,
                    author=author,
                    question=question or None,
                    description=description or None,
                    fields_of_study=fields,
                    license_name=license_name,
                )
                console.print("[green]Project settings saved.[/green]")
        except BackNavigation:
            return
        except (OSError, ValueError) as exc:
            console.print(f"[red]Cannot save settings:[/] {exc}")


def _people_menu(root: Path) -> None:
    """List, add, and select contributor identities without rewriting history."""
    while True:
        config = SmairtConfig.load(root / "smairt.yaml")
        _header("People", f"Active: {config.active_contributor or 'not selected'}")
        for contributor in config.contributors:
            marker = "*" if contributor.id == config.active_contributor else " "
            console.print(f"{marker} {contributor.name} ({contributor.id})")
        try:
            action = _select(
                "People",
                [
                    ("add", "Add collaborator"),
                    ("use", "Select active contributor"),
                    ("back", "Back"),
                ],
            )
            if action == "back":
                return
            if action == "add":
                name = _text("Collaborator name")
                email = _text("Email (optional)")
                contributor = add_contributor(root, name, email or None)
                console.print(f"[green]Added {contributor.name}.[/green]")
            elif not config.contributors:
                console.print("[yellow]Add a contributor first.[/yellow]")
            else:
                selected = _select(
                    "Active contributor",
                    [(item.id, item.name) for item in config.contributors],
                    config.active_contributor,
                )
                use_contributor(root, selected)
        except BackNavigation:
            return
        except (OSError, ValueError) as exc:
            console.print(f"[red]Cannot update people:[/] {exc}")


def _environment_menu(root: Path) -> None:
    """Select no environment, an existing Conda environment, or create one."""
    config = SmairtConfig.load(root / "smairt.yaml")
    _header("Environment", f"Current: {config.environment.mode.value}")
    try:
        with console.status("Discovering local Conda environments…", spinner="dots"):
            environments = conda_environments()
        options: list[tuple[str, str]] = [("none", "No managed environment")]
        options.extend(
            (f"existing:{item['prefix']}", f"Use existing: {item['name']}") for item in environments
        )
        options.append(("new", "Create a new Conda environment"))
        options.append(("back", "Back"))
        selected = _select("Environment", options)
        if selected == "back":
            return
        if selected == "none":
            select_environment(root, mode=EnvironmentMode.NONE)
        elif selected == "new":
            name = _text("New Conda environment name", f"smairt-{config.project.slug}")
            with console.status("Creating Conda environment…", spinner="dots"):
                select_environment(root, mode=EnvironmentMode.NEW_CONDA, name=name, create=True)
        else:
            prefix = selected.split(":", 1)[1]
            select_environment(
                root,
                mode=EnvironmentMode.EXISTING_CONDA,
                name=Path(prefix).name,
                prefix=prefix,
            )
        console.print("[green]Environment selection saved.[/green]")
    except BackNavigation:
        return
    except (OSError, ValueError) as exc:
        console.print(f"[red]Cannot update environment:[/] {exc}")


def _integrations_menu(root: Path) -> None:
    """Configure non-secret integration state and masked credential profiles."""
    while True:
        config = SmairtConfig.load(root / "smairt.yaml")
        _header("Integrations & API keys", f"Zotero: {config.integrations.zotero.mode.value}")
        try:
            action = _select(
                "Integrations",
                [
                    ("status", "Show backend and non-secret status"),
                    ("zotero", "Configure read-only Zotero"),
                    ("openalex", "Configure OpenAlex profile"),
                    ("credential", "Set or delete a masked API key"),
                    ("test", "Explicitly test Zotero connection"),
                    ("mcp", "Configure read-only agent access"),
                    ("back", "Back"),
                ],
            )
            if action == "back":
                return
            if config.schema_version < 4:
                console.print("Schema v4 is required for integrations.")
                if _yes_no("Apply the backed-up migration now?", True):
                    apply_migration(root, config.active_contributor)
                continue
            if action == "status":
                console.print(integration_health(root))
                _pause()
            elif action == "zotero":
                zotero_config = config.integrations.zotero
                mode = _select(
                    "Zotero connection",
                    [(item, item.value) for item in ZoteroMode],
                    zotero_config.mode,
                )
                library_id = _text("Library ID (Web mode)", zotero_config.library_id or "")
                library_type = _select(
                    "Library type",
                    [(item, item.value) for item in ZoteroLibraryType],
                    zotero_config.library_type,
                )
                profile = _text("Credential profile", zotero_config.credential.profile)
                configure_zotero(
                    root,
                    mode=mode,
                    library_id=library_id or None,
                    library_type=library_type,
                    profile=profile,
                    environment_variable=zotero_config.credential.environment_variable
                    or "ZOTERO_API_KEY",
                    mcp_access_enabled=_yes_no(
                        "Allow attributed read-only Zotero metadata through MCP?",
                        zotero_config.mcp_access_enabled,
                    ),
                    confirm_agent_access=_yes_no(
                        "Confirm agent access for this contributor?",
                        False,
                    )
                    if config.data.classification is DataClassification.PRIVATE
                    else False,
                )
            elif action == "openalex":
                openalex_config = config.integrations.openalex
                profile = _text("Credential profile", openalex_config.credential.profile)
                env_var = _text(
                    "Environment variable",
                    openalex_config.credential.environment_variable or "OPENALEX_API_KEY",
                )
                configure_openalex(
                    root,
                    enabled=_yes_no("Enable OpenAlex supplementation?", openalex_config.enabled),
                    profile=profile,
                    environment_variable=env_var,
                )
            elif action == "credential":
                provider = _select("Provider", [("openalex", "OpenAlex"), ("zotero", "Zotero")])
                configured = (
                    config.integrations.openalex.credential
                    if provider == "openalex"
                    else config.integrations.zotero.credential
                )
                profile = _text("Credential profile", configured.profile)
                operation = _select(
                    "Credential", [("set", "Set masked value"), ("delete", "Delete")]
                )
                if operation == "delete":
                    delete_credential(provider, profile)
                    console.print("[green]Credential deleted if it existed.[/green]")
                    continue
                secret = _secret(f"{provider} API key")
                set_credential(provider, profile, secret)
                console.print("[green]Credential stored in the OS keyring.[/green]")
            elif action == "test":
                with console.status("Contacting Zotero…", spinner="dots"):
                    collections = ZoteroProvider(root).collections(1)
                console.print({"ok": True, "collections_returned": len(collections)})
            else:
                harness = config.harness.active
                if harness is HarnessName.CLINE:
                    raise ValueError("Cline MCP configuration is deferred")
                enabled = harness in config.integrations.mcp.enabled_harnesses
                configure_mcp(root, harness, not enabled)
                console.print(mcp_status(root))
        except BackNavigation:
            return
        except (OSError, RuntimeError, ValueError) as exc:
            console.print(f"[red]Cannot update integration:[/] {exc}")
        _pause()


def _references_menu(root: Path) -> None:
    """Import and review references through the same transactional CLI services."""
    while True:
        records = load_index(root)
        _header("References", f"{len(records)} indexed record(s)")
        try:
            action = _select(
                "References",
                [
                    ("list", "Review metadata"),
                    ("doi", "Import DOI metadata"),
                    ("zotero-item", "Import Zotero item"),
                    ("zotero-collection", "Import Zotero collection"),
                    ("zotero-pdf", "Copy one local Zotero PDF"),
                    ("attach", "Attach a local PDF"),
                    ("back", "Back"),
                ],
            )
            if action == "back":
                return
            if action == "list":
                for record in records:
                    console.print(
                        f"[bold]{record.id}[/] · {record.title} · "
                        f"{record.verification_status.value}"
                    )
                _pause()
                continue
            if action == "doi":
                record = add_doi_reference(
                    root,
                    _text("DOI"),
                    use_openalex=_yes_no("Supplement missing fields with OpenAlex?", False),
                    confirm_remote=_yes_no("Confirm this metadata network request?", True),
                )
            elif action == "zotero-item":
                record = import_zotero_item(root, _text("Zotero item key"))
            elif action == "zotero-collection":
                key = _text("Zotero collection key")
                limit_text = _text("Maximum items (1-1000)", "500")
                imported = import_zotero_collection(root, key, limit=int(limit_text))
                console.print(f"[green]Imported {len(imported)} record(s).[/green]")
                _pause()
                continue
            elif action == "zotero-pdf":
                item_key = _text("Parent Zotero item key")
                attachment_key = _text("Zotero attachment key")
                if not _yes_no("Copy this one attachment into the project?", False):
                    continue
                record = copy_zotero_attachment(root, item_key, attachment_key, confirmed=True)
            else:
                identifier = _text("Reference ID")
                record = attach_reference(root, identifier, Path(_text("PDF path")))
            console.print(f"[green]Saved {record.id}.[/green]")
        except BackNavigation:
            return
        except (OSError, RuntimeError, ValueError) as exc:
            console.print(f"[red]Cannot update references:[/] {exc}")
        _pause()


def _health_menu(root: Path) -> None:
    """Run local validation and doctor checks from one small submenu."""
    try:
        action = _select(
            "Health",
            [
                ("validate", "Validate project"),
                ("doctor", "Run doctor"),
                ("back", "Back"),
            ],
        )
        if action == "validate":
            payload = status(root)["validation"]
        elif action == "doctor":
            payload = doctor(root)
        else:
            return
        console.print(payload)
        _pause()
    except BackNavigation:
        return


def run_project_menu(root: Path) -> None:
    """Run the nested project workflow hub directly beneath the shell prompt."""
    root = root.resolve()
    while True:
        config = SmairtConfig.load(root / "smairt.yaml")
        current = status(root)
        validation = current["validation"]
        _header(
            config.project.name,
            f"{'Healthy' if validation['ok'] else 'Needs attention'} · "
            f"Contributor: {config.active_contributor or 'not selected'} · Esc goes back",
        )
        try:
            action = _select(
                "What would you like to do?",
                [
                    ("next", "Recommended next step"),
                    ("research", "Research workflow"),
                    ("references", "References"),
                    ("settings", "Project settings"),
                    ("people", "People and collaborators"),
                    ("environment", "Environment"),
                    ("integrations", "Integrations & API keys"),
                    ("safety", "Safety and harness"),
                    ("health", "Validate and doctor"),
                    ("exit", "Return to shell"),
                ],
            )
        except BackNavigation:
            return
        if action == "exit":
            return
        if action in {"next", "research", "safety"}:
            _show_guidance(root, action.title())
        elif action == "references":
            _references_menu(root)
        elif action == "settings":
            _settings_menu(root)
        elif action == "people":
            _people_menu(root)
        elif action == "environment":
            _environment_menu(root)
        elif action == "integrations":
            _integrations_menu(root)
        else:
            _health_menu(root)


def run_setup_menu() -> None:
    """Show installation health without requiring an initialized project."""
    _header("SMAIRT Setup", "Conda is optional; Git and uv support the tool installation path")
    console.print(setup_doctor(check_github=False))
    _pause()


def run_contextual_menu() -> None:
    """Open the project dashboard or the pre-project start hub."""
    from smairt.project import find_project

    try:
        root = find_project()
    except FileNotFoundError:
        root = None
    if root is not None:
        run_project_menu(root)
        return
    while True:
        _header("SMAIRT", "Scientific Method with AI Research Toolkit")
        try:
            action = _select(
                "Start",
                [
                    ("new", "Create a new project"),
                    ("init", "Initialize the current folder"),
                    ("setup", "Check tool setup"),
                    ("help", "Show command help"),
                    ("exit", "Return to shell"),
                ],
            )
        except BackNavigation:
            return
        if action == "exit":
            return
        if action == "new":
            run_new_project()
        elif action == "init":
            run_new_project(Path.cwd(), allow_existing=True)
        elif action == "setup":
            run_setup_menu()
        else:
            console.print("Run [bold]smairt --help[/bold] for the complete command reference.")
            _pause()
