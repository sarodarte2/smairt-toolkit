"""Terminal-native workflow tests for navigation, state, and project creation."""

from pathlib import Path

import pytest
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from smairt.models import ProjectLicense, SmairtConfig
from smairt.tui import BackNavigation, _preflight_destination, _select, run_new_project


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
        input_stream.send_text("\x1b")
        with pytest.raises(BackNavigation):
            _select("Choose", [("first", "First")])
        input_stream.send_text("\x03")
        with pytest.raises(KeyboardInterrupt):
            _select("Choose", [("first", "First")])
    assert not output.entered_alternate_screen


def test_new_project_workflow_creates_v4_project(monkeypatch, tmp_path: Path) -> None:
    """Create through retained-state steps and verify metadata and managed license."""
    target = tmp_path / "terminal-project"

    def answer_text(message: str, default: str = "") -> str:
        answers = {
            "Destination": str(target),
            "Project name": "Terminal Study",
            "Primary researcher": "Researcher",
            "Email (optional)": "researcher@example.org",
            "Fields of study, comma separated (optional)": "Biology, biology, Genomics",
        }
        return answers.get(message, default)

    def answer_select(message: str, options, default=None):
        answers = {
            "Register this researcher as the active contributor?": True,
            "Add another collaborator?": False,
            "Project license": ProjectLicense.MIT,
            "Initialize Git?": False,
            "Review": "create",
            "Next": False,
        }
        return answers.get(message, default if default is not None else options[0][0])

    monkeypatch.setattr("smairt.tui._text", answer_text)
    monkeypatch.setattr("smairt.tui._select", answer_select)

    assert run_new_project(target) == target
    config = SmairtConfig.load(target / "smairt.yaml")
    assert config.schema_version == 4
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
        if message == "Primary researcher":
            return "Researcher"
        if message == "Initial research question (optional)" and not escaped:
            escaped = True
            raise BackNavigation
        return default

    def answer_select(message: str, options, default=None):
        answers = {
            "Register this researcher as the active contributor?": True,
            "Add another collaborator?": False,
            "Initialize Git?": False,
            "Review": "cancel",
        }
        return answers.get(message, default if default is not None else options[0][0])

    monkeypatch.setattr("smairt.tui._text", answer_text)
    monkeypatch.setattr("smairt.tui._select", answer_select)

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
