"""Command-line integration tests for creation, discovery, and guided state."""

import json
from pathlib import Path

from typer.testing import CliRunner

from smairt.cli import app

runner = CliRunner()


def test_version_and_noninteractive_creation(tmp_path: Path) -> None:
    """Verify version output and the complete non-interactive creation path."""
    version = runner.invoke(app, ["--version"])
    assert version.exit_code == 0
    assert "0.1.0" in version.stdout

    destination = tmp_path / "cli-project"
    result = runner.invoke(
        app,
        [
            "new",
            str(destination),
            "--name",
            "CLI Project",
            "--author",
            "Manual Author",
            "--classification",
            "unpublished",
            "--no-git",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert (destination / "smairt.yaml").exists()

    status_result = runner.invoke(app, ["status", "--json"], catch_exceptions=False)
    assert status_result.exit_code == 2


def test_status_json_from_project(tmp_path: Path, monkeypatch) -> None:
    """Verify JSON status includes manual identity and state-aware guidance."""
    destination = tmp_path / "status-project"
    created = runner.invoke(
        app,
        [
            "new",
            str(destination),
            "--name",
            "Status Project",
            "--author",
            "Researcher",
            "--no-git",
        ],
    )
    assert created.exit_code == 0
    monkeypatch.chdir(destination)
    result = runner.invoke(app, ["status", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["project"]["author"] == "Researcher"
    assert payload["stage"] == "project_setup"
    assert payload["guidance"]["recommended"]["id"] == "add_references"

    next_result = runner.invoke(app, ["next", "--json"])
    assert next_result.exit_code == 0
    assert json.loads(next_result.stdout)["stage"] == "project_setup"


def test_noninteractive_init_preserves_existing_directory(tmp_path: Path) -> None:
    """Ensure adopting reviewed work never removes an existing research file."""
    destination = tmp_path / "existing"
    destination.mkdir()
    notes = destination / "notes.md"
    notes.write_text("Existing notes.\n")
    result = runner.invoke(
        app,
        ["init", str(destination), "--name", "Existing", "--author", "Researcher"],
    )
    assert result.exit_code == 0, result.stdout
    assert notes.read_text() == "Existing notes.\n"
    assert (destination / "smairt.yaml").exists()


def test_start_project_alias_reaches_wizard(monkeypatch, tmp_path: Path) -> None:
    """Ensure the friendly alias opens the wizard with safe creation semantics."""
    observed: dict[str, object] = {}

    def fake_wizard(destination: Path | None, *, allow_existing: bool = False) -> None:
        """Capture wizard arguments without starting an interactive application."""
        observed.update(destination=destination, allow_existing=allow_existing)

    monkeypatch.setattr("smairt.cli.run_new_project", fake_wizard)
    destination = tmp_path / "friendly"
    result = runner.invoke(app, ["start", "project", str(destination)])
    assert result.exit_code == 0, result.stdout
    assert observed == {"destination": destination, "allow_existing": False}
