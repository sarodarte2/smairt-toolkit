"""Textual interfaces for project creation and maintenance."""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Footer, Header, Input, Label, Select, Static, Switch

from smairt.guidance import next_guidance
from smairt.models import DataClassification, EnvironmentMode, HarnessName, SmairtConfig
from smairt.project import status, update_project_identity
from smairt.scaffold import conda_environments, create_project
from smairt.utils import slugify

ORANGE = "#f28c28"


class NewProjectApp(App[Path | None]):
    """Keyboard-accessible wizard for previewing and creating one SMAIRT project."""

    TITLE = "SMAIRT · New Project"
    CSS = f"""
    Screen {{ align: center middle; background: #101820; color: #f4f4f4; }}
    #card {{ width: 96%; max-width: 78; min-width: 36; height: 92%; padding: 1 2;
             border: round {ORANGE}; }}
    .step {{ width: 100%; }}
    .title {{ color: {ORANGE}; text-style: bold; text-align: center; margin-bottom: 1; }}
    Label {{ margin-top: 1; }}
    Input, Select {{ width: 100%; }}
    #actions {{ height: auto; min-height: 3; margin-top: 1; align-horizontal: right; }}
    Button.-primary {{ background: {ORANGE}; color: #101820; text-style: bold; }}
    #message {{ color: {ORANGE}; margin-top: 1; }}
    """
    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        ("escape", "cancel", "Cancel"),
        ("ctrl+r", "refresh", "Refresh"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, destination: Path | None = None, *, allow_existing: bool = False):
        """Initialize local wizard state without blocking first paint."""
        super().__init__()
        self.destination = destination
        self.allow_existing = allow_existing
        self.previewing = False
        self.creating = False
        self.step = 0
        self.environment_options: list[tuple[str, str]] = [
            ("Create a new project Conda environment", EnvironmentMode.NEW_CONDA.value),
            ("No managed environment", EnvironmentMode.NONE.value),
        ]

    def compose(self) -> ComposeResult:
        """Build the project form, preview message, and guarded action buttons."""
        yield Header()
        with VerticalScroll(id="card"):
            yield Static("SMAIRT", classes="title")
            yield Static("Scientific Method with AI Research Toolkit", classes="title")
            yield Static("Step 1 of 4 · Location", id="step-title")
            with Vertical(classes="step", id="step-0"):
                yield Label("Destination")
                yield Input(value=str(self.destination or Path.cwd()), id="destination")
                yield Label("Project name")
                yield Input(placeholder="My research project", id="name")
                yield Label("Author or researcher (entered manually)")
                yield Input(placeholder="Your name", id="author")
            with Vertical(classes="step", id="step-1"):
                yield Label("Initial research question (optional)")
                yield Input(placeholder="Skip if the question is still developing", id="question")
                yield Label("Project description (optional)")
                yield Input(placeholder="A short description", id="description")
            with Vertical(classes="step", id="step-2"):
                yield Label("Data classification")
                yield Select(
                    [(item.value.title(), item.value) for item in DataClassification],
                    value=DataClassification.UNPUBLISHED.value,
                    id="classification",
                )
                yield Label("Project environment (discovering local Conda environments…)")
                yield Select(
                    self.environment_options,
                    value=EnvironmentMode.NONE.value,
                    id="environment",
                )
                yield Label("Coding harness")
                yield Select(
                    [(item.value.title(), item.value) for item in HarnessName],
                    value=HarnessName.CODEX.value,
                    id="harness",
                )
                yield Label("Safety mode (experimental; not compliance certification)")
                yield Select(
                    [
                        ("Standard — normal research collaboration", "standard"),
                        ("Strict — fail closed for sharing and release", "strict"),
                    ],
                    value="standard",
                    id="safety_mode",
                )
                with Horizontal():
                    yield Label("Confirm author as the active contributor")
                    yield Switch(value=True, id="confirm_contributor")
                with Horizontal():
                    yield Label("Initialize Git (recommended)")
                    yield Switch(value=True, id="git")
            with Vertical(classes="step", id="step-3"):
                yield Static("Review the project contract before creation.")
            yield Static("", id="message")
            with Horizontal(id="actions"):
                yield Button("Cancel", id="cancel")
                yield Button("Back", id="back")
                yield Button("Next", id="submit", variant="primary", classes="-primary")
        yield Footer()

    def on_mount(self) -> None:
        """Reveal the first step immediately and discover environments in a worker."""
        self._show_step(0)
        self.discover_environments()

    @work(thread=True, exclusive=True, group="environment-discovery")
    def discover_environments(self) -> None:
        """Discover Conda outside the event loop and update options when ready."""
        environments = conda_environments()
        options = [
            ("Create a new project Conda environment", EnvironmentMode.NEW_CONDA.value),
            *[
                (f"Use existing: {item['name']}", f"existing:{item['prefix']}")
                for item in environments
            ],
            ("No managed environment", EnvironmentMode.NONE.value),
        ]
        self.call_from_thread(self._set_environment_options, options)

    def _set_environment_options(self, options: list[tuple[str, str]]) -> None:
        """Install discovered choices while preserving the current selection."""
        select = self.query_one("#environment", Select)
        current = select.value
        select.set_options(options)
        if current in {value for _, value in options}:
            select.value = current

    def _show_step(self, step: int) -> None:
        """Show one step while preserving values in mounted hidden widgets."""
        self.step = max(0, min(3, step))
        titles = ("Location", "Research identity", "Policy and harness", "Review")
        for index in range(4):
            self.query_one(f"#step-{index}", Vertical).display = index == self.step
        self.query_one("#step-title", Static).update(
            f"Step {self.step + 1} of 4 · {titles[self.step]}"
        )
        self.query_one("#back", Button).disabled = self.step == 0 or self.creating
        self.query_one("#submit", Button).label = "Create" if self.step == 3 else "Next"
        self.previewing = self.step == 3

    def _values(self) -> dict[str, Any]:
        """Translate visible form values into validated scaffold arguments."""
        environment_value = str(self.query_one("#environment", Select).value)
        environment_mode = EnvironmentMode.NONE
        environment_prefix = None
        environment_name = None
        create_environment = False
        if environment_value == EnvironmentMode.NEW_CONDA.value:
            environment_mode = EnvironmentMode.NEW_CONDA
            create_environment = True
            environment_name = f"smairt-{slugify(self.query_one('#name', Input).value)}"
        elif environment_value.startswith("existing:"):
            environment_mode = EnvironmentMode.EXISTING_CONDA
            environment_prefix = environment_value.split(":", 1)[1]
            environment_name = Path(environment_prefix).name
        return {
            "destination": Path(self.query_one("#destination", Input).value),
            "name": self.query_one("#name", Input).value,
            "author": self.query_one("#author", Input).value,
            "question": self.query_one("#question", Input).value or None,
            "description": self.query_one("#description", Input).value or None,
            "classification": DataClassification(
                str(self.query_one("#classification", Select).value)
            ),
            "initialize_git": self.query_one("#git", Switch).value,
            "environment_mode": environment_mode,
            "environment_name": environment_name,
            "environment_prefix": environment_prefix,
            "create_environment": create_environment,
            "harness": HarnessName(str(self.query_one("#harness", Select).value)),
            "safety_mode": str(self.query_one("#safety_mode", Select).value),
            "confirm_contributor": self.query_one("#confirm_contributor", Switch).value,
            "allow_existing": self.allow_existing,
        }

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Navigate, prevent duplicate submission, and surface actionable errors."""
        if event.button.id == "cancel":
            if self.creating:
                self.query_one("#message", Static).update(
                    "Project creation is finishing; cancellation is disabled."
                )
                return
            self.exit(None)
            return
        if event.button.id == "back":
            self._show_step(self.step - 1)
            return
        if self.creating:
            return
        try:
            values = self._values()
            if not values["name"]:
                self.query_one("#name", Input).focus()
                raise ValueError("Project name is required")
            if not values["author"]:
                self.query_one("#author", Input).focus()
                raise ValueError("Manually entered author is required")
            if self.step == 0:
                destination = Path(values["destination"]).expanduser().resolve()
                if (destination / "smairt.yaml").exists():
                    raise FileExistsError(
                        "destination is already a SMAIRT project; use 'smairt menu' there"
                    )
                if (
                    destination.exists()
                    and any(destination.iterdir())
                    and not (destination / ".git").exists()
                    and not self.allow_existing
                ):
                    raise FileExistsError(
                        "destination contains files. Choose a new empty folder, or run "
                        "'smairt init' to adopt existing work"
                    )
            if self.step < 2:
                self._show_step(self.step + 1)
                return
            if self.step == 2:
                summary = (
                    f"Create {values['name']!r} at {values['destination']}\n"
                    f"Data: {values['classification'].value}; Environment: "
                    f"{values['environment_mode'].value}; Harness: {values['harness'].value}; "
                    f"Safety: {values['safety_mode']}; Git: {values['initialize_git']}\n"
                    "No hypothesis will be requested. Review and press Create."
                )
                self.query_one("#message", Static).update(summary)
                self._show_step(3)
                return
            # Disable the button before filesystem work so a repeated keypress
            # cannot start two scaffolds and leave a misleading partial project.
            self.creating = True
            self.query_one("#submit", Button).disabled = True
            self.query_one("#cancel", Button).disabled = True
            self.query_one("#back", Button).disabled = True
            self.query_one("#message", Static).update("Creating project…")
            self.create_in_worker(values)
        except Exception as exc:
            self.creating = False
            self.query_one("#submit", Button).disabled = False
            self.query_one("#message", Static).update(f"Cannot create project: {exc}")

    @work(thread=True, exclusive=True, group="project-creation")
    def create_in_worker(self, values: dict[str, Any]) -> None:
        """Create the scaffold without freezing keyboard input or repainting."""
        try:
            create_project(**values)
        except Exception as exc:
            self.call_from_thread(self._creation_failed, str(exc))
        else:
            self.call_from_thread(self.exit, Path(values["destination"]).resolve())

    def _creation_failed(self, message: str) -> None:
        """Re-enable creation after a recoverable worker failure."""
        self.creating = False
        self.query_one("#submit", Button).disabled = False
        self.query_one("#cancel", Button).disabled = False
        self.query_one("#back", Button).disabled = False
        self.query_one("#message", Static).update(f"Cannot create project: {message}")

    def action_cancel(self) -> None:
        """Exit the wizard without changing the destination."""
        if self.creating:
            self.query_one("#message", Static).update(
                "Project creation is finishing; cancellation is disabled."
            )
            return
        self.exit(None)

    async def action_quit(self) -> None:
        """Prevent the terminal from claiming cancellation during active creation."""
        if self.creating:
            self.query_one("#message", Static).update(
                "Project creation is finishing; quit is disabled."
            )
            return
        self.exit(None)

    def action_refresh(self) -> None:
        """Refresh local environment choices without network access."""
        self.discover_environments()


class ProjectMenuApp(App[None]):
    """Editable dashboard for manually maintained project identity and health."""

    TITLE = "SMAIRT · Project"
    CSS = f"""
    Screen {{ background: #101820; color: #f4f4f4; }}
    #body {{ margin: 1 3; padding: 1 2; border: round {ORANGE}; }}
    .title {{ color: {ORANGE}; text-style: bold; }}
    Input {{ width: 100%; }}
    #metadata {{ display: none; }}
    Button.-primary {{ background: {ORANGE}; color: #101820; }}
    #message {{ color: {ORANGE}; margin-top: 1; }}
    """

    def __init__(self, root: Path):
        """Load the authoritative project contract for display and editing."""
        super().__init__()
        self.root = root
        self.config = SmairtConfig.load(root / "smairt.yaml")

    def compose(self) -> ComposeResult:
        """Build editable identity fields and the compact health summary."""
        yield Header()
        with VerticalScroll(id="body"):
            yield Static(self.config.project.name, classes="title")
            yield Static("Loading local project state…", id="health")
            yield Static("", id="recommended")
            with Vertical(id="metadata"):
                yield Label("Project name")
                yield Input(value=self.config.project.name, id="name")
                yield Label("Author or researcher")
                yield Input(value=self.config.project.author, id="author")
                yield Label("Initial question")
                yield Input(value=self.config.project.question or "", id="question")
                yield Label("Description")
                yield Input(value=self.config.project.description or "", id="description")
            with Horizontal():
                yield Button("Refresh", id="refresh")
                yield Button("Validate", id="validate")
                yield Button("Details", id="details")
                yield Button("Save Details", id="save", classes="-primary")
                yield Button("Exit", id="exit")
            yield Static("", id="message")
        yield Footer()

    def on_mount(self) -> None:
        """Populate validation and artifact counts after widgets are available."""
        self.refresh_status()

    @work(thread=True, exclusive=True, group="dashboard-refresh")
    def refresh_status(self) -> None:
        """Compute validation and next actions without blocking the event loop."""
        current = status(self.root)
        guidance = next_guidance(self.root)
        self.call_from_thread(self._render_status, current, guidance)

    def _render_status(self, current: dict[str, Any], guidance: dict[str, Any]) -> None:
        """Render contributor, active state, safety, harness, and next action."""
        validation = current["validation"]
        counts = current["counts"]
        marker = "✓" if validation["ok"] else "!"
        self.query_one("#health", Static).update(
            f"{marker} validation · contributor "
            f"{current.get('active_contributor') or 'not selected'}\n"
            f"Active: {current.get('active') or 'none'}\n"
            f"Safety: {current['safety_mode']} / {current['data_classification']} · "
            f"Harness: {current['harness']['active']}\n"
            f"Artifacts: {counts['proposal_sets']} proposals · {counts['hypotheses']} hypotheses · "
            f"{counts['experiments']} experiments"
        )
        recommended = guidance.get("recommended")
        command = recommended.get("command") if isinstance(recommended, dict) else None
        label = (
            recommended.get("label") if isinstance(recommended, dict) else "Review project status"
        )
        self.query_one("#recommended", Static).update(
            f"Recommended next: {label}\nShell command: {command or 'smairt next --json'}"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle refresh, manual detail persistence, and clean application exit."""
        if event.button.id == "exit":
            self.exit()
        elif event.button.id == "refresh":
            self.refresh_status()
        elif event.button.id == "validate":
            self.refresh_status()
            self.query_one("#message", Static).update("Validation refreshed locally.")
        elif event.button.id == "details":
            metadata = self.query_one("#metadata", Vertical)
            metadata.display = not metadata.display
        elif event.button.id == "save":
            try:
                self.config = update_project_identity(
                    self.root,
                    name=self.query_one("#name", Input).value,
                    author=self.query_one("#author", Input).value,
                    question=self.query_one("#question", Input).value or None,
                    description=self.query_one("#description", Input).value or None,
                )
            except Exception as exc:
                self.query_one("#message", Static).update(f"Cannot save details: {exc}")
            else:
                self.query_one("#message", Static).update("Project details saved.")
                self.refresh_status()


def run_new_project(
    destination: Path | None = None, *, allow_existing: bool = False
) -> Path | None:
    """Run the creation wizard and return the new project path or cancellation."""
    return NewProjectApp(destination, allow_existing=allow_existing).run()


def run_project_menu(root: Path) -> None:
    """Open the editable dashboard for an existing project root."""
    ProjectMenuApp(root).run()
