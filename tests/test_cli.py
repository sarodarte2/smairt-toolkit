import json
from pathlib import Path

from typer.testing import CliRunner

from smairt.cli import app

runner = CliRunner()


def test_version_and_noninteractive_creation(tmp_path: Path) -> None:
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
