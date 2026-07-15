"""Schema-v5 privacy, routing, prompt, and project-discovery UX contracts."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from smairt.cli import app
from smairt.integrations import configure_zotero
from smairt.local_setup import load_bindings, load_user_setup, setup_config_path
from smairt.migrations import apply_migration
from smairt.models import (
    DataClassification,
    EnvironmentMode,
    SmairtConfig,
    ZoteroLibraryType,
    ZoteroMode,
)
from smairt.project import find_project, is_prohibited, validate_project
from smairt.scaffold import create_project

runner = CliRunner()


def project(tmp_path: Path, *, schema: int = 6) -> Path:
    """Create one isolated project, optionally rewriting it as a legacy v4 fixture."""
    root = tmp_path / "project"
    create_project(
        root,
        name="Private Connections",
        author="Researcher",
        classification=DataClassification.UNPUBLISHED,
        initialize_git=False,
        confirm_contributor=True,
    )
    if schema == 4:
        path = root / "smairt.yaml"
        payload = yaml.safe_load(path.read_text())
        payload["schema_version"] = 4
        payload["integrations"]["openalex"] = {
            "enabled": True,
            "credential": {
                "profile": "legacy-openalex",
                "environment_variable": "OPENALEX_API_KEY",
            },
        }
        payload["integrations"]["zotero"] = {
            "mode": "web",
            "library_id": "private-library-id",
            "library_type": "user",
            "credential": {
                "profile": "legacy-zotero",
                "environment_variable": "ZOTERO_API_KEY",
            },
            "mcp_access_enabled": False,
        }
        path.write_text(yaml.safe_dump(payload, sort_keys=False))
    elif schema == 5:
        path = root / "smairt.yaml"
        payload = yaml.safe_load(path.read_text())
        payload["schema_version"] = 5
        path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return root


def test_bare_smairt_is_splash_and_menu_outside_project_explains(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Keep package identity and project menus as separate entry points."""
    monkeypatch.chdir(tmp_path)
    splash = runner.invoke(app, [])
    assert splash.exit_code == 0
    assert "PNNL Computational Biology contributors" in splash.stdout
    assert "smairt new" in splash.stdout and "smairt setup" in splash.stdout
    menu = runner.invoke(app, ["menu"])
    assert menu.exit_code == 2
    assert tmp_path.name in menu.stdout and "smairt new" in menu.stdout


def test_menu_can_open_an_existing_project_by_path(tmp_path: Path, monkeypatch) -> None:
    """Let researchers resume a known project without changing shell directories."""
    root = project(tmp_path)
    opened: list[Path] = []
    monkeypatch.chdir(tmp_path.parent)
    monkeypatch.setattr("smairt.cli.run_project_menu", opened.append)
    result = runner.invoke(app, ["menu", str(root)])
    assert result.exit_code == 0, result.stdout
    assert opened == [root]


def test_project_discovery_stops_at_inner_git_worktree(tmp_path: Path) -> None:
    """Prevent a broad ancestor project from capturing an unrelated Git checkout."""
    outer = project(tmp_path)
    checkout = outer / "unrelated-checkout"
    checkout.mkdir()
    subprocess.run(["git", "init"], cwd=checkout, check=True, capture_output=True)
    with pytest.raises(FileNotFoundError):
        find_project(checkout)
    assert find_project(outer / "background") == outer


def test_schema_v5_keeps_connection_identifiers_out_of_shared_files(tmp_path: Path) -> None:
    """Store library IDs in user setup and profile selection in ignored local state."""
    root = project(tmp_path)
    configure_zotero(
        root,
        mode=ZoteroMode.WEB,
        library_id="private-library-id",
        library_type=ZoteroLibraryType.USER,
        profile="lab",
    )
    shared = (root / "smairt.yaml").read_text()
    assert "private-library-id" not in shared
    assert "credential" not in yaml.safe_load(shared)["integrations"]["zotero"]
    assert load_bindings(root).providers["zotero"] == "lab"
    assert load_user_setup().profiles["lab"].library_id == "private-library-id"
    assert is_prohibited(".smairt/local/integrations.yaml")
    assert os.stat(setup_config_path()).st_mode & 0o777 == 0o600


def test_guided_v4_to_v5_migration_moves_connection_fields_local(tmp_path: Path) -> None:
    """Migrate connection IDs out of shared YAML while preserving provider policy."""
    root = project(tmp_path, schema=4)
    record = apply_migration(root, "researcher")
    assert record["from_version"] == 4 and record["to_version"] == 5
    config = SmairtConfig.load(root / "smairt.yaml")
    assert config.schema_version == 5
    shared = (root / "smairt.yaml").read_text()
    assert "private-library-id" not in shared and "legacy-zotero" not in shared
    assert load_user_setup().profiles["legacy-zotero"].library_id == "private-library-id"
    assert load_bindings(root).providers == {
        "openalex": "legacy-openalex",
        "zotero": "legacy-zotero",
    }


def test_v5_to_v6_migration_enables_five_harness_contract(tmp_path: Path) -> None:
    """Upgrade durable harness vocabulary without changing scientific records."""
    root = project(tmp_path, schema=5)
    record = apply_migration(root, "researcher")
    assert record["from_version"] == 5 and record["to_version"] == 6
    assert SmairtConfig.load(root / "smairt.yaml").schema_version == 6


def test_next_prompt_is_copyable_and_preserves_human_gates(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Expose the context-aware handoff as plain terminal text."""
    root = project(tmp_path)
    monkeypatch.chdir(root)
    result = runner.invoke(app, ["next", "--prompt"])
    assert result.exit_code == 0
    assert "SMAIRT project stage:" in result.stdout
    assert "Do not select hypotheses" in result.stdout
    invalid = runner.invoke(app, ["next", "--prompt", "--json"])
    assert invalid.exit_code == 2


def test_conda_default_is_project_slug_without_smairt_prefix(tmp_path: Path) -> None:
    """Use the researcher-facing slug for new Conda environments."""
    root = tmp_path / "conda-project"
    create_project(
        root,
        name="RNA Signals",
        author="Researcher",
        classification=DataClassification.UNPUBLISHED,
        initialize_git=False,
        environment_mode=EnvironmentMode.NEW_CONDA,
        create_environment=False,
    )
    config = SmairtConfig.load(root / "smairt.yaml")
    assert config.environment.name == "rna-signals"
    assert "name: rna-signals" in (root / "environment/environment.yml").read_text()


def test_staged_secret_scan_reports_only_path(tmp_path: Path) -> None:
    """Block credential-like staged content without reflecting its value."""
    root = tmp_path / "git-project"
    create_project(
        root,
        name="Git Project",
        author="Researcher",
        classification=DataClassification.UNPUBLISHED,
        initialize_git=True,
    )
    sentinel = "super-private-sentinel-value"
    suspect = root / "notes.txt"
    suspect.write_text(f"OPENALEX_API_KEY={sentinel}\n")
    subprocess.run(["git", "add", "notes.txt"], cwd=root, check=True)
    report = validate_project(root, staged=True)
    assert not report.ok
    rendered = str(report.as_dict())
    assert "notes.txt" in rendered and sentinel not in rendered
