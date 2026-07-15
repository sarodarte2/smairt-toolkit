"""Schema-8 completion, science, Semantic Scholar, and Slurm boundaries."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import httpx
import pytest
import yaml

from smairt.completion import PROJECT_ACTIONS, project_identifiers
from smairt.diagnostics import doctor
from smairt.hpc import load_job, submit_slurm
from smairt.literature import SemanticScholarProvider
from smairt.local_setup import (
    ConnectionProfile,
    SlurmProfile,
    configure_profile,
    configure_slurm_profile,
    load_custom_logo,
    load_user_setup,
    save_custom_logo,
)
from smairt.local_setup import (
    test_profile as check_profile,
)
from smairt.migrations import migration_plan
from smairt.models import ComputeMode, ComputeResources, DataClassification, Decision, SmairtConfig
from smairt.paper import create_claim, create_evidence_card, review_claim
from smairt.references import add_doi_reference
from smairt.research import (
    activate_hypothesis,
    create_background,
    create_experiment,
    create_proposal_set,
    record_decision,
    validate_background,
    validate_hypothesis,
    validate_proposal_set,
)
from smairt.runner import run_experiment
from smairt.scaffold import create_project
from smairt.science import validate_protocol
from smairt.updates import apply_project_updates, project_update_plan


def project(tmp_path: Path) -> Path:
    """Create a schema-8 project without external services."""
    root = tmp_path / "v8"
    create_project(
        root,
        name="V8",
        author="Researcher",
        classification=DataClassification.UNPUBLISHED,
        initialize_git=False,
        confirm_contributor=True,
    )
    return root


def complete_protocol(path: Path) -> None:
    """Replace the generated draft with a compact valid protocol fixture."""
    path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "status": "ready",
                "question_or_purpose": "Verify a deterministic analysis.",
                "design": "Seeded single-run validation",
                "unit_of_analysis": "one generated result",
                "inputs": [{"name": "configuration", "unit": "dimensionless"}],
                "primary_outcome": {"name": "completion", "unit": "boolean"},
                "secondary_outcomes": [],
                "controls": ["fixed seed"],
                "replication_rationale": "One deterministic smoke run is sufficient.",
                "randomization_and_blinding": "Not applicable: deterministic smoke test.",
                "exclusions_and_missing_data": "No exclusions; missing output fails.",
                "analysis_method": "Execute and verify declared output.",
                "assumptions": ["Python is available"],
                "uncertainty_measure": "Not applicable: deterministic result.",
                "multiple_comparisons": "Not applicable: one outcome.",
                "seed": 1024,
                "success_criteria": "Command exits zero.",
                "failure_criteria": "Command exits nonzero.",
                "falsifier": "Missing declared output.",
                "stopping_rule": "Stop after one completed run.",
                "declared_outputs": ["artifacts/results.json"],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def test_completion_catalog_and_project_ids_are_local(tmp_path: Path) -> None:
    root = project(tmp_path)
    create_experiment(root, title="Local IDs", purpose="Completion fixture")
    assert {item.value for item in PROJECT_ACTIONS} >= {"next", "references", "health"}
    assert project_identifiers(root, "experiment") == ["EXPERIMENT_001"]
    assert project_identifiers(root, "unknown") == []


def test_user_setup_v3_migrates_appearance_without_project_state(tmp_path: Path) -> None:
    setup = tmp_path / "user-setup/setup.yaml"
    setup.parent.mkdir(parents=True)
    setup.write_text("schema_version: 3\nmotion: off\nprofiles: {}\n")

    config = load_user_setup()

    assert config.schema_version == 5
    assert config.appearance.motion == "off"
    assert config.appearance.theme == "scientific"
    assert config.appearance.mark == "none"


def test_user_setup_v4_migrates_logo_and_provider_scoped_profiles(tmp_path: Path) -> None:
    setup = tmp_path / "user-setup/setup.yaml"
    setup.parent.mkdir(parents=True)
    setup.write_text(
        yaml.safe_dump(
            {
                "schema_version": 4,
                "appearance": {"theme": "pnnl", "logo": "pnnl-mark"},
                "profiles": {
                    "default": {
                        "provider": "zotero",
                        "credential_profile": "default",
                        "mode": "local",
                    }
                },
            },
            sort_keys=False,
        )
    )

    config = load_user_setup()

    assert config.schema_version == 5
    assert config.appearance.mark == "pnnl"
    assert config.profiles["zotero"]["default"].mode.value == "local"


def test_each_provider_can_own_a_default_profile(tmp_path: Path) -> None:
    configure_profile("default", ConnectionProfile(provider="zotero", mode="local"))
    configure_profile("default", ConnectionProfile(provider="openalex"))
    configure_profile("default", ConnectionProfile(provider="semantic_scholar"))
    configure_profile(
        "default",
        ConnectionProfile(provider="unpaywall", contact_email="researcher@example.org"),
    )

    assert set(load_user_setup().profiles) == {
        "zotero",
        "openalex",
        "semantic_scholar",
        "unpaywall",
    }


def test_semantic_scholar_profile_test_supports_public_access(monkeypatch) -> None:
    configure_profile("default", ConnectionProfile(provider="semantic_scholar"))
    monkeypatch.setattr(
        "smairt.credentials.resolve_credential", lambda *_args, **_kwargs: (None, None)
    )

    class Response:
        def __init__(self) -> None:
            self.status_code = 200
            self.headers: dict[str, str] = {}

        @staticmethod
        def json() -> dict[str, object]:
            return {"data": []}

    monkeypatch.setattr(httpx, "get", lambda *_args, **_kwargs: Response())

    result = check_profile("semantic_scholar", "default")

    assert result["ok"] is True
    assert result["access_mode"] == "public"


def test_custom_ascii_logo_rejects_terminal_injection(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="control"):
        save_custom_logo("SAFE\x00UNSAFE")
    with pytest.raises(ValueError, match="escape"):
        save_custom_logo("SAFE\x1b[2J")
    save_custom_logo(" /\\\n/  \\")
    assert load_custom_logo() == " /\\\n/  \\"


def test_documented_demo_reaches_one_supported_approved_claim(tmp_path: Path, monkeypatch) -> None:
    """Keep the human walkthrough's fixtures scientifically and mechanically coherent."""
    root = project(tmp_path)
    example = Path(__file__).parents[1] / "examples/enzyme-kinetics-demo"
    monkeypatch.setattr(
        "smairt.references._fetch_crossref",
        lambda _doi: {
            "message": {
                "title": ["The original Michaelis constant"],
                "author": [{"family": "Michaelis"}],
                "published": {"date-parts": [[2011]]},
            }
        },
    )
    reference = add_doi_reference(root, "10.1021/bi201284u")
    assert reference.id == "doi-a04d8aaf11d84cfac807"
    create_background(root)
    shutil.copyfile(example / "initial_background.md", root / "background/initial_background.md")
    assert validate_background(root) == []

    proposals = create_proposal_set(root)
    shutil.copyfile(example / "proposal_options.md", proposals)
    assert validate_proposal_set(proposals) == []
    hypothesis = activate_hypothesis(
        root,
        proposals,
        "A",
        title="Nonlinear Michaelis-Menten recovery",
        statement="Nonlinear fitting recovers the declared Vmax and Km within tolerance.",
        selected_by="Researcher",
        rationale="Direct bounded correctness test.",
    )
    text = hypothesis.read_text()
    text = text.replace("[Complete from the selected proposal and human edits.]", "Native fit.")
    text = text.replace(
        "[Complete before running the linked experiment.]",
        "Declared parameter ranges must be recovered.",
        1,
    ).replace(
        "[Complete before running the linked experiment.]",
        "At least one predeclared check fails.",
        1,
    )
    text = text.replace(
        "## Required Data and Controls\n",
        "## Required Data and Controls\nAll triplicates and blanks.\n",
    )
    text = text.replace(
        "## Success and Failure Criteria\n",
        "## Success and Failure Criteria\nAll checks pass or the demo fails.\n",
    )
    text = text.replace("## Known Confounders\n", "## Known Confounders\nSynthetic fixture.\n")
    hypothesis.write_text(text)
    assert validate_hypothesis(hypothesis) == []

    experiment = create_experiment(
        root,
        title="Enzyme Kinetics",
        hypothesis_id="HYPOTHESIS_001",
        purpose="Recover independently declared parameters",
        enforce_protocol=True,
    )
    iteration = experiment / "iterations/ITERATION_001"
    for name in ("data.csv", "expected-results.json", "protocol.yaml"):
        shutil.copyfile(example / name, iteration / name)
    shutil.copyfile(example / "analysis.py", iteration / "script_001_enzyme_kinetics.py")
    run = run_experiment(root, experiment_id="EXPERIMENT_001", iteration_id="ITERATION_001")
    result = json.loads((root / run.results_directory / "artifacts/results.json").read_text())
    assert result["correct"] and result["vmax_umol_min"] == 120.0 and result["km_mM"] == 2.5
    analysis = root / "analysis/EXPERIMENT_001/ANALYSIS_ITERATION_001.md"
    analysis.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(example / "ANALYSIS_ITERATION_001.md", analysis)
    record_decision(
        root,
        experiment_id="EXPERIMENT_001",
        iteration_id="ITERATION_001",
        run_id=run.run_id,
        decision=Decision.ACCEPT,
        rationale="Every predeclared check passed.",
        decided_by="Researcher",
    )
    evidence = create_evidence_card(
        root,
        run.run_id,
        purpose="Correctness demo",
        observed_result="Declared parameters were recovered.",
        limitations="Synthetic deterministic fixture.",
        decision="ACCEPT",
    )
    claim = create_claim(root, "The demo recovered its declared parameters.", [evidence.stem])
    reviewed = review_claim(root, claim.stem, "approved")
    assert reviewed["status"] == "approved"


def test_semantic_scholar_normalizes_provisional_results(tmp_path: Path) -> None:
    root = project(tmp_path)

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "api.semanticscholar.org"
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "paperId": "s2-paper",
                        "externalIds": {"DOI": "10.1000/example"},
                        "title": "A bounded result",
                        "authors": [{"name": "Ada Researcher"}],
                        "year": 2026,
                        "venue": "Journal",
                        "citationCount": 3,
                        "url": "https://www.semanticscholar.org/paper/s2-paper",
                        "abstract": "Available",
                    }
                ]
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = SemanticScholarProvider(root, client=client).search("bounded", 1)[0]
    assert result.provider == "semantic_scholar"
    assert result.doi == "10.1000/example"
    assert result.discovery_method == "search"
    assert result.abstract_available


def test_new_protocol_blocks_until_ready(tmp_path: Path) -> None:
    root = project(tmp_path)
    experiment = create_experiment(
        root,
        title="Protocol",
        purpose="Enforce design",
        enforce_protocol=True,
    )
    protocol = experiment / "iterations/ITERATION_001/protocol.yaml"
    assert validate_protocol(protocol)
    with pytest.raises(ValueError, match="Scientific protocol is incomplete"):
        run_experiment(root, experiment_id="EXPERIMENT_001", iteration_id="ITERATION_001")
    complete_protocol(protocol)
    assert not validate_protocol(protocol)
    run = run_experiment(
        root,
        experiment_id="EXPERIMENT_001",
        iteration_id="ITERATION_001",
        command=[sys.executable, "-c", "print('ready')"],
    )
    assert run.protocol_sha256


def test_v7_projects_plan_a_schema_8_migration(tmp_path: Path) -> None:
    root = project(tmp_path)
    config = SmairtConfig.load(root / "smairt.yaml")
    config.schema_version = 7
    config.dump(root / "smairt.yaml")
    assert migration_plan(root)["to_version"] == 8


def test_unified_update_plan_explains_v6_to_v8(tmp_path: Path) -> None:
    root = project(tmp_path)
    config = SmairtConfig.load(root / "smairt.yaml")
    config.schema_version = 6
    config.dump(root / "smairt.yaml")

    plan = project_update_plan(root)

    assert plan["project_schema"]["steps"] == [
        {"from_version": 6, "to_version": 7},
        {"from_version": 7, "to_version": 8},
    ]
    assert plan["updates_available"]


def test_doctor_separates_health_updates_and_sharing(tmp_path: Path) -> None:
    root = project(tmp_path)
    config = SmairtConfig.load(root / "smairt.yaml")
    config.schema_version = 7
    config.dump(root / "smairt.yaml")

    report = doctor(root)

    assert report["ok"]
    assert report["health_state"] == "action_recommended"
    assert report["recommended_updates"]["project_schema"]["target"] == 8
    assert report["sharing_readiness"] == report["release"]


def test_unified_update_applies_every_schema_step(tmp_path: Path) -> None:
    root = project(tmp_path)
    config = SmairtConfig.load(root / "smairt.yaml")
    config.schema_version = 6
    config.dump(root / "smairt.yaml")

    receipt = apply_project_updates(root)

    assert [item["to_version"] for item in receipt["migrations"]] == [7, 8]
    assert SmairtConfig.load(root / "smairt.yaml").schema_version == 8
    assert receipt["final"]["project_schema"]["status"] == "current"


def test_native_slurm_submission_uses_typed_profile(tmp_path: Path, monkeypatch) -> None:
    root = project(tmp_path)
    experiment = create_experiment(
        root,
        title="Slurm",
        purpose="Submission boundary",
        enforce_protocol=True,
    )
    complete_protocol(experiment / "iterations/ITERATION_001/protocol.yaml")
    configure_slurm_profile(
        "native",
        SlurmProfile(mode=ComputeMode.NATIVE, remote_root="/shared/smairt-jobs"),
    )

    def fake_run(command, **kwargs):
        del kwargs
        assert command[0] == "sbatch"
        assert "--parsable" in command
        return subprocess.CompletedProcess(command, 0, stdout="12345\n", stderr="")

    monkeypatch.setattr("smairt.hpc.subprocess.run", fake_run)
    job = submit_slurm(
        root,
        experiment_id="EXPERIMENT_001",
        iteration_id="ITERATION_001",
        command=[sys.executable, "-c", "print('cluster')"],
        resources=ComputeResources(cpus=2, memory_mib=2048, wall_minutes=10),
    )
    assert job.scheduler_job_id == "12345"
    assert load_job(root, job.run_id)[1] == job
    assert load_user_setup().default_compute_profile == "native"
    run_payload = json.loads((root / job.local_run_directory / "run.json").read_text())
    assert run_payload["status"] == "started"
    assert (root / job.local_run_directory / "protocol.snapshot.yaml").is_file()


def test_slurm_launch_failure_is_a_terminal_manifested_run(tmp_path: Path, monkeypatch) -> None:
    """Never leave a reserved HPC run permanently started after submit failure."""
    root = project(tmp_path)
    experiment = create_experiment(
        root,
        title="Failed Slurm",
        purpose="Atomic launch failure",
        enforce_protocol=True,
    )
    complete_protocol(experiment / "iterations/ITERATION_001/protocol.yaml")
    configure_slurm_profile(
        "native",
        SlurmProfile(mode=ComputeMode.NATIVE, remote_root="/shared/smairt-jobs"),
    )

    def fail_submit(command, **kwargs):
        del command, kwargs
        raise RuntimeError("scheduler unavailable")

    monkeypatch.setattr("smairt.hpc.subprocess.run", fail_submit)
    with pytest.raises(RuntimeError, match="scheduler unavailable"):
        submit_slurm(
            root,
            experiment_id="EXPERIMENT_001",
            iteration_id="ITERATION_001",
            command=[sys.executable, "-c", "print('cluster')"],
            resources=ComputeResources(),
        )
    run_json = next((root / "results").glob("*/*/*/run.json"))
    payload = json.loads(run_json.read_text())
    assert payload["status"] == "failed"
    assert payload["environment"]["launch_failed"] is True
    assert (run_json.parent / "manifest.json").is_file()
    assert not (run_json.parent / "job.json").exists()


def test_demo_analysis_recovers_declared_parameters(tmp_path: Path) -> None:
    """Keep the public demo's numerical correctness inside the release gate."""
    demo = Path(__file__).parents[1] / "examples/enzyme-kinetics-demo"
    run_dir = tmp_path / "run"
    environment = os.environ.copy()
    environment["SMAIRT_RESULTS_DIR"] = str(run_dir / "artifacts")
    completed = subprocess.run(
        [sys.executable, str(demo / "analysis.py")],
        cwd=demo,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    result = json.loads((run_dir / "artifacts/results.json").read_text())
    assert result["correct"] is True
    assert result["vmax_umol_min"] == 120.0
    assert result["km_mM"] == 2.5
    assert (run_dir / "result-summary.yaml").is_file()
