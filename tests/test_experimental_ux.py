"""Experimental Home, profile, project-context, and coaching UX contracts."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from typer.testing import CliRunner

from smairt.cli import app
from smairt.local_setup import (
    StarterProfile,
    discard_project_draft,
    discovered_projects,
    load_project_draft,
    load_user_setup,
    normalize_field_of_study,
    normalize_fields_of_study,
    recent_projects,
    remember_project,
    save_project_draft,
    save_user_setup,
    setup_config_path,
)
from smairt.models import DataClassification, HarnessName, SmairtConfig
from smairt.scaffold import create_project
from smairt.tui import _project_command, _workflow_stage

runner = CliRunner()


def project(root: Path, name: str = "UX Project") -> Path:
    """Create one lightweight project fixture."""
    create_project(
        root,
        name=name,
        author="Contributor",
        classification=DataClassification.UNPUBLISHED,
        initialize_git=False,
        confirm_contributor=True,
    )
    return root


def test_setup_v6_migrates_to_nullable_v7_profile(tmp_path: Path) -> None:
    path = setup_config_path()
    path.parent.mkdir(parents=True)
    path.write_text("schema_version: 6\nappearance: {}\nprofiles: {}\n")

    setup = load_user_setup()

    assert setup.schema_version == 7
    assert setup.starter_profile == StarterProfile()
    assert setup.recent_projects == []


def test_profile_only_persists_explicit_values(tmp_path: Path) -> None:
    setup = load_user_setup()
    setup.starter_profile.contributor_name = "Ada Researcher"
    setup.starter_profile.fields_of_study = ["computational biology", "RNA-seq"]
    setup.starter_profile.assistant = HarnessName.CODEX
    save_user_setup(setup)

    loaded = load_user_setup().starter_profile

    assert loaded.contributor_name == "Ada Researcher"
    assert loaded.contributor_email is None
    assert loaded.project_parent is None
    assert loaded.fields_of_study == ["Computational Biology", "RNA-seq"]
    assert loaded.assistant is HarnessName.CODEX


def test_field_normalization_is_natural_and_deduplicated() -> None:
    assert normalize_field_of_study("  computational   biology ") == "Computational Biology"
    assert normalize_field_of_study("biology of aging") == "Biology of Aging"
    assert normalize_field_of_study("scrna-seq analysis") == "scRNA-seq Analysis"
    assert normalize_fields_of_study(["data science", "Data Science", "eQTL genetics"]) == [
        "Data Science",
        "eQTL Genetics",
    ]


def test_recent_and_one_level_discovery_are_bounded(tmp_path: Path) -> None:
    parent = tmp_path / "projects"
    first = project(parent / "first", "First")
    second = project(parent / "second", "Second")
    nested = project(parent / "group" / "nested", "Nested")
    setup = load_user_setup()
    setup.starter_profile.project_parent = str(parent)
    save_user_setup(setup)
    remember_project(second)
    remember_project(first)

    assert recent_projects() == [first, second]
    assert discovered_projects() == [first, second]
    assert nested not in discovered_projects()


def test_draft_is_owner_only_and_discardable() -> None:
    path = save_project_draft({"name": "Interrupted", "classification": "unpublished"})

    assert os.stat(path).st_mode & 0o777 == 0o600
    assert load_project_draft() and load_project_draft().values["name"] == "Interrupted"
    assert discard_project_draft()
    assert load_project_draft() is None


def test_noninteractive_new_requires_intent_and_accepts_explicit_bundle(tmp_path: Path) -> None:
    incomplete = runner.invoke(
        app,
        ["new", str(tmp_path / "incomplete"), "--name", "Incomplete", "--author", "A"],
    )
    assert incomplete.exit_code == 2
    assert "--accept-recommended" in incomplete.output

    complete = runner.invoke(
        app,
        [
            "new",
            str(tmp_path / "complete"),
            "--name",
            "Complete",
            "--author",
            "A",
            "--accept-recommended",
            "--confirm-contributor",
        ],
    )
    assert complete.exit_code == 0, complete.output
    config = SmairtConfig.load(tmp_path / "complete/smairt.yaml")
    assert config.project.license.value == "unspecified"
    assert config.harness.active is HarnessName.CODEX


def test_global_project_option_works_from_any_directory(tmp_path: Path, monkeypatch) -> None:
    root = project(tmp_path / "selected")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    result = runner.invoke(app, ["--project", str(root), "status", "--json"])

    assert result.exit_code == 0, result.output
    assert "UX Project" in result.output
    assert _project_command(root, "smairt background create").startswith("smairt --project")
    monkeypatch.chdir(root)
    assert _project_command(root, "smairt background create") == "smairt background create"


def test_workflow_stage_map_uses_plain_and_scientific_labels() -> None:
    assert _workflow_stage("project_setup") == ("Ground", "Background")
    assert _workflow_stage("proposal_complete") == ("Explore", "Hypothesis")
    assert _workflow_stage("experiment_ready") == ("Test", "Experiment and run")
    assert _workflow_stage("decision_recorded") == ("Interpret", "Decision and evidence")
    assert _workflow_stage("claim_review") == ("Share", "Claims and paper")


def test_saved_setup_yaml_contains_no_implicit_policy_defaults() -> None:
    setup = load_user_setup()
    save_user_setup(setup)
    payload = yaml.safe_load(setup_config_path().read_text())

    profile = payload["starter_profile"]
    assert "license" not in profile
    assert "classification" not in profile
    assert "environment" not in profile
    assert "git" not in profile
    assert "safety_mode" not in profile
