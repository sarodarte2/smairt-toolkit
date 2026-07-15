"""Schema-8 completion, science, Semantic Scholar, and Slurm boundaries."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import httpx
import pytest
import yaml

from smairt.completion import PROJECT_ACTIONS, project_identifiers
from smairt.hpc import load_job, submit_slurm
from smairt.literature import SemanticScholarProvider
from smairt.local_setup import SlurmProfile, configure_slurm_profile, load_user_setup
from smairt.migrations import migration_plan
from smairt.models import ComputeMode, ComputeResources, DataClassification, SmairtConfig
from smairt.research import create_experiment
from smairt.runner import run_experiment
from smairt.scaffold import create_project
from smairt.science import validate_protocol


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
