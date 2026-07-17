"""Terminal-native workflow tests for navigation, state, and project creation."""

from pathlib import Path

import pytest
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput
from prompt_toolkit.output.base import Size

from smairt.local_setup import AppearanceConfig
from smairt.models import (
    DataClassification,
    EnvironmentMode,
    HarnessName,
    ProjectLicense,
    SafetyMode,
    SmairtConfig,
)
from smairt.tui import (
    SMAIRT_LOGO,
    THEMES,
    BackNavigation,
    _appearance_values,
    _preflight_destination,
    _responsive_layout,
    _select,
    run_new_project,
)


def test_responsive_layout_breakpoints_and_wide_cap() -> None:
    cases = {
        (60, 18): ("narrow", 60),
        (80, 24): ("compact", 80),
        (103, 51): ("compact", 103),
        (119, 30): ("compact", 119),
        (120, 30): ("wide", 120),
        (180, 50): ("wide", 132),
        (340, 60): ("wide", 132),
    }
    for size, expected in cases.items():
        assert _responsive_layout(*size) == expected


def test_named_themes_and_secondary_marks_never_replace_smairt(monkeypatch) -> None:
    """Keep neutral brand identity separate from named color palettes."""
    expected_themes = {
        "scientific",
        "pnnl",
        "utep",
        "matrix",
        "dracula",
        "nord",
        "solarized",
        "amber",
        "high-contrast",
        "monochrome",
    }
    assert expected_themes <= set(THEMES)
    assert len(SMAIRT_LOGO.splitlines()) == 5
    monkeypatch.setattr("smairt.tui.load_custom_logo", lambda: "CUSTOM\nMARK")
    assert _appearance_values(AppearanceConfig(mark="custom"))[2] == "CUSTOM\nMARK"
    assert _appearance_values(AppearanceConfig(mark="none"))[2] == ""
    monkeypatch.setenv("NO_COLOR", "1")
    assert _appearance_values(AppearanceConfig(theme="matrix"))[:2] == THEMES["monochrome"][:2]


def test_choice_uses_arrows_enter_and_escape() -> None:
    """Exercise Prompt Toolkit's real key processing without an alternate screen."""

    class TrackingOutput(DummyOutput):
        entered_alternate_screen = False

        def enter_alternate_screen(self) -> None:
            self.entered_alternate_screen = True

    output = TrackingOutput()
    with (
        create_pipe_input() as input_stream,
        create_app_session(input=input_stream, output=output),
    ):
        input_stream.send_text("\x1b[B\r")
        assert _select("Choose", [("first", "First"), ("second", "Second")]) == "second"
        input_stream.send_text("\x1b[A\r")
        with pytest.raises(BackNavigation):
            _select("Back is selectable", [("first", "First"), ("second", "Second")])
        input_stream.send_text("\x1b[B\x1b[B\r")
        with pytest.raises(BackNavigation):
            _select("Move down to Back", [("first", "First"), ("second", "Second")])
        input_stream.send_text("\x1b[B\x1b[B\x1b[B\r")
        assert _select("Wrap after Back", [("first", "First"), ("second", "Second")]) == "first"
        input_stream.send_text("\x1b")
        with pytest.raises(BackNavigation):
            _select("Choose", [("first", "First")])
        input_stream.send_text("\x03")
        with pytest.raises(KeyboardInterrupt):
            _select("Choose", [("first", "First")])
    assert not output.entered_alternate_screen


@pytest.mark.parametrize(
    ("columns", "rows"),
    [(60, 18), (80, 24), (103, 51), (119, 30), (120, 30), (180, 50), (340, 60)],
)
def test_choice_renders_at_acceptance_sizes(columns: int, rows: int) -> None:
    """Render and accept a choice at every supported responsive acceptance size."""

    class SizedOutput(DummyOutput):
        def get_size(self) -> Size:
            return Size(rows=rows, columns=columns)

    with (
        create_pipe_input() as input_stream,
        create_app_session(input=input_stream, output=SizedOutput()),
    ):
        input_stream.send_text("\r")
        assert _select("Responsive choice", [("first", "First"), ("back", "Back")]) == "first"


def test_wide_layout_escapes_logo_and_dynamic_text(monkeypatch) -> None:
    """Render the real wide header without treating logo text as HTML markup."""

    class WideOutput(DummyOutput):
        def get_size(self) -> Size:
            return Size(rows=30, columns=120)

    monkeypatch.setattr("smairt.tui._SCREEN_TITLE", "Methods < Results")
    monkeypatch.setattr("smairt.tui._SCREEN_SUBTITLE", "R&D")
    with (
        create_pipe_input() as input_stream,
        create_app_session(input=input_stream, output=WideOutput()),
    ):
        input_stream.send_text("\r")
        assert _select("Choose <one>", [("first", "First")]) == "first"


def test_new_project_workflow_creates_current_project(monkeypatch, tmp_path: Path) -> None:
    """Create through retained-state steps and verify metadata and managed license."""
    target = tmp_path / "terminal-project"

    def answer_text(message: str, default: str = "") -> str:
        answers = {
            "Parent directory": str(tmp_path),
            "Project folder": target.name,
            "Project name": "Terminal Study",
            "Active contributor": "Researcher",
            "Contributor email (optional)": "researcher@example.org",
        }
        return answers.get(message, default)

    def answer_select(message: str, options, default=None):
        answers = {
            "Confirm this person as the active contributor?": True,
            "Review": "create",
            "Next": "shell",
        }
        return answers.get(message, default if default is not None else options[0][0])

    def answer_required(message: str, options, *_args):
        answers = {
            "Data classification": DataClassification.UNPUBLISHED,
            "Project license": ProjectLicense.MIT,
            "Project environment": EnvironmentMode.NONE,
            "AI assistant": HarnessName.CODEX,
            "Safety mode": SafetyMode.STANDARD,
            "Initialize Git?": False,
        }
        return answers[message]

    monkeypatch.setattr("smairt.tui._text", answer_text)
    monkeypatch.setattr("smairt.tui._select", answer_select)
    monkeypatch.setattr("smairt.tui._required_select", answer_required)
    monkeypatch.setattr(
        "smairt.tui._select_profile_fields", lambda _current: ["Biology", "genomics"]
    )

    assert run_new_project(tmp_path) == target
    config = SmairtConfig.load(target / "smairt.yaml")
    assert config.schema_version == 8
    assert config.project.fields_of_study == ["Biology", "Genomics"]
    assert config.project.license is ProjectLicense.MIT
    assert config.contributors[0].email == "researcher@example.org"
    assert (target / "LICENSE").read_text().startswith("MIT License")
    assert (target / ".smairt/license.json").is_file()


def test_new_project_escape_preserves_previous_values(monkeypatch, tmp_path: Path) -> None:
    """Escape moves back one step and supplies prior values as editable defaults."""
    target = tmp_path / "retained"
    observed_name_defaults: list[str] = []
    escaped = False

    def answer_text(message: str, default: str = "") -> str:
        nonlocal escaped
        if message == "Destination":
            return str(target)
        if message == "Project name":
            observed_name_defaults.append(default)
            return default or "Retained Study"
        if message == "Active contributor":
            return "Researcher"
        if message == "Initial research question (optional)" and not escaped:
            escaped = True
            raise BackNavigation
        return default

    def answer_select(message: str, options, default=None):
        answers = {
            "Confirm this person as the active contributor?": True,
            "Review": "cancel",
            "Keep this draft for later?": False,
        }
        return answers.get(message, default if default is not None else options[0][0])

    monkeypatch.setattr("smairt.tui._text", answer_text)
    monkeypatch.setattr("smairt.tui._select", answer_select)
    monkeypatch.setattr("smairt.tui._select_profile_fields", lambda current: current)
    choices = iter(
        [
            DataClassification.UNPUBLISHED,
            ProjectLicense.UNSPECIFIED,
            EnvironmentMode.NONE,
            HarnessName.CODEX,
            SafetyMode.STANDARD,
            False,
        ]
    )
    monkeypatch.setattr("smairt.tui._required_select", lambda *_args: next(choices))

    assert run_new_project(target) is None
    assert observed_name_defaults == ["", "Retained Study"]


def test_nonempty_destination_is_rejected_before_writes(tmp_path: Path) -> None:
    """Keep an existing non-project folder untouched unless init is explicit."""
    target = tmp_path / "nonempty"
    target.mkdir()
    (target / "notes.txt").write_text("research notes")
    with pytest.raises(FileExistsError, match="contains files"):
        _preflight_destination(target, allow_existing=False)
    assert not (target / "smairt.yaml").exists()
