"""Schema-v3 project settings, migration, license, and environment tests."""

import subprocess
from pathlib import Path

import pytest
import yaml

from smairt.diagnostics import doctor
from smairt.licenses import render_license
from smairt.migrations import apply_migration, migration_plan
from smairt.models import (
    DataClassification,
    EnvironmentMode,
    ProjectLicense,
    SmairtConfig,
)
from smairt.scaffold import conda_environments, create_conda_environment, create_project
from smairt.settings import select_environment, update_project_settings


def project(tmp_path: Path) -> Path:
    """Create one contributor-confirmed schema-v3 project."""
    root = tmp_path / "project"
    create_project(
        root,
        name="Settings",
        author="Researcher",
        classification=DataClassification.UNPUBLISHED,
        initialize_git=False,
        confirm_contributor=True,
    )
    return root


@pytest.mark.parametrize("license_name", list(ProjectLicense))
def test_every_project_license_choice_is_renderable(license_name: ProjectLicense) -> None:
    """Render a root license for every explicit choice except unspecified."""
    content = render_license(license_name, "Researcher")
    if license_name is ProjectLicense.UNSPECIFIED:
        assert content is None
    else:
        assert content and "Researcher" in content


def test_settings_deduplicate_fields_and_protect_modified_license(tmp_path: Path) -> None:
    """Normalize free-form fields and refuse to overwrite researcher-edited legal text."""
    root = project(tmp_path)
    update_project_settings(
        root,
        name="Settings",
        author="Researcher",
        question=None,
        description=None,
        fields_of_study=["Biology", " biology ", "Genomics"],
        license_name=ProjectLicense.BSD_3_CLAUSE,
    )
    config = SmairtConfig.load(root / "smairt.yaml")
    assert config.project.fields_of_study == ["Biology", "Genomics"]
    assert config.project.license is ProjectLicense.BSD_3_CLAUSE
    (root / "LICENSE").write_text("researcher-owned license\n")
    with pytest.raises(ValueError, match="modified"):
        update_project_settings(
            root,
            name="Settings",
            author="Researcher",
            question=None,
            description=None,
            fields_of_study=config.project.fields_of_study,
            license_name=ProjectLicense.MIT,
        )
    assert (root / "LICENSE").read_text() == "researcher-owned license\n"


def test_v2_migrates_transactionally_to_unspecified_v3(tmp_path: Path) -> None:
    """Preserve v2 readability and avoid implying a license during migration."""
    root = project(tmp_path)
    config_path = root / "smairt.yaml"
    payload = yaml.safe_load(config_path.read_text())
    payload["schema_version"] = 2
    payload["project"].pop("fields_of_study")
    payload["project"].pop("license")
    config_path.write_text(yaml.safe_dump(payload, sort_keys=False))
    (root / "LICENSE").unlink()
    (root / ".smairt/license.json").unlink()

    loaded = SmairtConfig.load(config_path)
    assert loaded.schema_version == 2
    assert doctor(root)["warnings"]
    assert migration_plan(root)["detected"] == "v2"
    record = apply_migration(root, loaded.active_contributor)
    migrated = SmairtConfig.load(config_path)
    assert record["to_version"] == 3
    assert migrated.project.license is ProjectLicense.UNSPECIFIED
    assert migrated.project.fields_of_study == []
    assert (root / record["backup"]).is_file()


def test_environment_selection_and_conda_failures(monkeypatch, tmp_path: Path) -> None:
    """Keep no-environment usable and turn absent or timed-out Conda into recovery errors."""
    root = project(tmp_path)
    selected = select_environment(root, mode=EnvironmentMode.NONE)
    assert selected.mode is EnvironmentMode.NONE

    monkeypatch.setattr("smairt.scaffold.shutil.which", lambda _name: None)
    assert conda_environments() == []
    with pytest.raises(RuntimeError, match="not installed"):
        create_conda_environment("missing")

    monkeypatch.setattr("smairt.scaffold.shutil.which", lambda _name: "/usr/bin/conda")

    def timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(["conda"], 5)

    monkeypatch.setattr("smairt.scaffold.subprocess.run", timeout)
    assert conda_environments() == []
    with pytest.raises(RuntimeError, match="timed out"):
        create_conda_environment("slow")
