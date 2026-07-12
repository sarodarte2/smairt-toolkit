"""Textual interfaces for project creation and maintenance."""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Button, Footer, Header, Input, Label, Select, Static, Switch

from smairt.models import DataClassification, EnvironmentMode, SmairtConfig
from smairt.project import status
from smairt.scaffold import conda_environments, create_project
from smairt.utils import slugify

ORANGE = "#f28c28"


class NewProjectApp(App[Path | None]):
    TITLE = "SMAIRT · New Project"
    CSS = f"""
    Screen {{ align: center middle; background: #101820; color: #f4f4f4; }}
    #card {{ width: 78; height: 92%; padding: 1 3; border: round {ORANGE}; }}
    .title {{ color: {ORANGE}; text-style: bold; text-align: center; margin-bottom: 1; }}
    Label {{ margin-top: 1; }}
    Input, Select {{ width: 100%; }}
    #actions {{ height: 3; margin-top: 1; align-horizontal: right; }}
    Button.-primary {{ background: {ORANGE}; color: #101820; text-style: bold; }}
    #message {{ color: {ORANGE}; margin-top: 1; }}
    """

    def __init__(self, destination: Path | None = None, *, allow_existing: bool = False):
        super().__init__()
        self.destination = destination
        self.allow_existing = allow_existing
        self.previewing = False
        self.creating = False
        environments = conda_environments()
        self.environment_options = [
            ("Create a new project Conda environment", EnvironmentMode.NEW_CONDA.value),
            *[
                (f"Use existing: {item['name']}", f"existing:{item['prefix']}")
                for item in environments
            ],
            ("No managed environment", EnvironmentMode.NONE.value),
        ]

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="card"):
            yield Static("SMAIRT", classes="title")
            yield Static("Scientific Method with AI Research Toolkit", classes="title")
            yield Label("Destination")
            yield Input(value=str(self.destination or Path.cwd()), id="destination")
            yield Label("Project name")
            yield Input(placeholder="My research project", id="name")
            yield Label("Author or researcher (entered manually)")
            yield Input(placeholder="Your name", id="author")
            yield Label("Initial research question (optional)")
            yield Input(placeholder="Skip if the question is still developing", id="question")
            yield Label("Project description (optional)")
            yield Input(placeholder="A short description", id="description")
            yield Label("Data classification")
            yield Select(
                [(item.value.title(), item.value) for item in DataClassification],
                value=DataClassification.UNPUBLISHED.value,
                id="classification",
            )
            yield Label("Project environment")
            yield Select(
                self.environment_options,
                value=EnvironmentMode.NONE.value,
                id="environment",
            )
            with Horizontal():
                yield Label("Initialize Git (recommended)")
                yield Switch(value=True, id="git")
            yield Static("", id="message")
            with Horizontal(id="actions"):
                yield Button("Cancel", id="cancel")
                yield Button("Preview", id="submit", variant="primary", classes="-primary")
        yield Footer()

    def _values(self) -> dict[str, object]:
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
            "allow_existing": self.allow_existing,
        }

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.exit(None)
            return
        if self.creating:
            return
        try:
            values = self._values()
            if not values["name"] or not values["author"]:
                raise ValueError("Project name and manually entered author are required")
            if not self.previewing:
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
                summary = (
                    f"Create {values['name']!r} at {values['destination']}\n"
                    f"Data: {values['classification'].value}; Environment: "
                    f"{values['environment_mode'].value}; Git: {values['initialize_git']}\n"
                    "No hypothesis will be requested. Review and press Create."
                )
                self.query_one("#message", Static).update(summary)
                self.query_one("#submit", Button).label = "Create"
                self.previewing = True
                return
            self.creating = True
            self.query_one("#submit", Button).disabled = True
            self.query_one("#message", Static).update("Creating project…")
            create_project(**values)
            self.exit(Path(values["destination"]).resolve())
        except Exception as exc:
            self.creating = False
            self.query_one("#submit", Button).disabled = False
            self.query_one("#message", Static).update(f"Cannot create project: {exc}")


class ProjectMenuApp(App[None]):
    TITLE = "SMAIRT · Project"
    CSS = f"""
    Screen {{ background: #101820; color: #f4f4f4; }}
    #body {{ margin: 1 3; padding: 1 2; border: round {ORANGE}; }}
    .title {{ color: {ORANGE}; text-style: bold; }}
    Input {{ width: 100%; }}
    Button.-primary {{ background: {ORANGE}; color: #101820; }}
    #message {{ color: {ORANGE}; margin-top: 1; }}
    """

    def __init__(self, root: Path):
        super().__init__()
        self.root = root
        self.config = SmairtConfig.load(root / "smairt.yaml")

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="body"):
            yield Static(self.config.project.name, classes="title")
            yield Static("", id="health")
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
                yield Button("Save Details", id="save", classes="-primary")
                yield Button("Exit", id="exit")
            yield Static("", id="message")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_status()

    def refresh_status(self) -> None:
        current = status(self.root)
        validation = current["validation"]
        counts = current["counts"]
        marker = "✓" if validation["ok"] else "!"
        self.query_one("#health", Static).update(
            f"{marker} validation · {counts['proposal_sets']} proposal sets · "
            f"{counts['hypotheses']} hypotheses · {counts['experiments']} experiments"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "exit":
            self.exit()
        elif event.button.id == "refresh":
            self.refresh_status()
        elif event.button.id == "save":
            self.config.project.name = self.query_one("#name", Input).value
            self.config.project.author = self.query_one("#author", Input).value
            self.config.project.question = self.query_one("#question", Input).value or None
            self.config.project.description = self.query_one("#description", Input).value or None
            self.config.dump(self.root / "smairt.yaml")
            self.query_one("#message", Static).update("Project details saved.")
            self.refresh_status()


def run_new_project(
    destination: Path | None = None, *, allow_existing: bool = False
) -> Path | None:
    return NewProjectApp(destination, allow_existing=allow_existing).run()


def run_project_menu(root: Path) -> None:
    ProjectMenuApp(root).run()
