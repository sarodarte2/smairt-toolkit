"""CLI integration coverage for v2 diagnostics, adapters, context, and exports."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from smairt.cli import app

runner = CliRunner()


def invoke_ok(arguments: list[str]):
    """Invoke a CLI command and fail with its captured output when unsuccessful."""
    result = runner.invoke(app, arguments)
    assert result.exit_code == 0, result.stdout
    return result


def test_v2_diagnostic_and_harness_commands(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "cli-v2"
    invoke_ok(
        [
            "new",
            str(root),
            "--name",
            "CLI V2",
            "--author",
            "Researcher",
            "--confirm-contributor",
            "--harness",
            "zoo",
            "--no-git",
        ]
    )
    monkeypatch.chdir(root)

    assert json.loads(invoke_ok(["status", "--json"]).stdout)["data"]["harness"]["active"] == "zoo"
    invoke_ok(["next", "--json"])
    invoke_ok(["validate", "--json"])
    invoke_ok(["code", "index"])
    invoke_ok(["code", "validate", "--json"])
    invoke_ok(["upgrade"])
    invoke_ok(["env", "status", "--json"])
    assert json.loads(invoke_ok(["contributor", "list", "--json"]).stdout)["data"]["active"]
    assert (
        json.loads(invoke_ok(["safety", "status", "--json"]).stdout)["data"]["mode"] == "standard"
    )
    assert json.loads(invoke_ok(["harness", "status", "--json"]).stdout)["data"]["active"]
    assert len(json.loads(invoke_ok(["harness", "list", "--json"]).stdout)["data"]) == 3

    preview = invoke_ok(["harness", "select", "cline", "--dry-run"])
    assert "create_or_update" in preview.stdout
    invoke_ok(["harness", "select", "cline"])
    assert (
        json.loads(invoke_ok(["harness", "status", "--json"]).stdout)["data"]["harness"] == "cline"
    )

    model = json.loads(invoke_ok(["model", "recommend", "--task", "metadata", "--json"]).stdout)[
        "data"
    ]
    assert model["tier"] == "cheap"
    capsule = json.loads(
        invoke_ok(
            ["context", "--task", "planning", "--token-budget", "20000", "--save", "--json"]
        ).stdout
    )["data"]
    assert capsule["capsule_path"].startswith(".smairt/local/context/")

    assert json.loads(invoke_ok(["migrate", "plan", "--json"]).stdout)["data"]["detected"] == "v4"
    invoke_ok(["contract", "export"])
    invoke_ok(["contract", "check"])
    invoke_ok(["reference", "list", "--json"])
    invoke_ok(["reference", "scan", "--json"])
    invoke_ok(["reference", "export", "--format", "bibtex"])
    invoke_ok(["summary", "list", "--json"])
    invoke_ok(["summary", "compare", "background-project-description-md"])
    invoke_ok(["paper", "status", "--json"])
    invoke_ok(["paper", "evidence", "list", "--json"])
    invoke_ok(["paper", "validate"])
    invoke_ok(["history", "--json"])
    invoke_ok(["doctor", "--json"])
    invoke_ok(["contributor", "add", "--name", "Second Researcher"])
    invoke_ok(["contributor", "use", "second-researcher"])
    invoke_ok(["safety", "attest", "--visibility", "private", "--yes"])
    invoke_ok(["safety", "set", "strict", "--yes"])
    release = runner.invoke(app, ["safety", "release-check", "--json"])
    # Strict mode fails closed until an explicit, fresh visibility observation exists.
    assert release.exit_code == 1
    assert not json.loads(release.stdout)["ok"]


def test_cli_renders_model_policy_error_without_traceback(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "errors"
    invoke_ok(
        [
            "new",
            str(root),
            "--name",
            "Errors",
            "--author",
            "Researcher",
            "--confirm-contributor",
            "--no-git",
        ]
    )
    monkeypatch.chdir(root)
    result = runner.invoke(app, ["model", "recommend", "--task", "impossible"])
    assert result.exit_code == 2
    output = result.output
    assert "unknown task" in output
    assert "Traceback" not in output
