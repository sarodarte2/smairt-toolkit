"""Tests for schema-v2 attribution, safety, contracts, and run integrity."""

import json
from pathlib import Path

import yaml

from smairt.contracts import check_contracts, export_contracts
from smairt.corrections import correct_run
from smairt.harnesses import harness_status, install_harness
from smairt.integrity import verify_run
from smairt.migrations import apply_migration, migration_plan, rollback_migration
from smairt.models import DataClassification, EnvironmentMode, ReferenceRecord, SmairtConfig
from smairt.paper import begin_paper, build_paper
from smairt.provenance import add_contributor, load_events, record_event, use_contributor
from smairt.references import edit_reference, normalize_doi, save_index, verify_reference
from smairt.runner import run_experiment
from smairt.safety import set_safety_mode
from smairt.scaffold import create_project
from smairt.summaries import create_summary, list_summaries, promote_summary


def project(tmp_path: Path) -> Path:
    root = tmp_path / "v2"
    create_project(
        root,
        name="V2 Project",
        author="Researcher",
        classification=DataClassification.UNPUBLISHED,
        initialize_git=False,
        environment_mode=EnvironmentMode.NONE,
    )
    return root


def test_contributors_events_and_safety_are_explicit(tmp_path: Path) -> None:
    root = project(tmp_path)
    assert SmairtConfig.load(root / "smairt.yaml").contributors == []
    contributor = add_contributor(root, "Ada Researcher", "ada@example.org")
    use_contributor(root, contributor.id)
    record_event(root, "test.recorded", artifact_ids=["artifact-1"])
    assert load_events(root)[0]["actor"] == contributor.id
    assert (root / "docs/PROJECT_HISTORY.md").exists()
    assert set_safety_mode(root, "strict")["mode"] == "strict"


def test_run_manifest_detects_mutation_and_contracts_export(tmp_path: Path) -> None:
    root = project(tmp_path)
    experiment = root / "experiments/EXPERIMENT_001_smoke/iterations/ITERATION_001"
    experiment.mkdir(parents=True)
    (experiment.parent.parent / "experiment.yaml").write_text(
        "id: EXPERIMENT_001\ntitle: Smoke\npurpose: Verify integrity\nentrypoint: run.py\n"
    )
    (experiment / "config.yaml").write_text("seed: 1\n")
    (experiment / "run.py").write_text(
        "from pathlib import Path\nimport os\n"
        "Path(os.environ['SMAIRT_RESULTS_DIR'], 'value.txt').write_text('original')\n"
    )
    run = run_experiment(root, experiment_id="EXPERIMENT_001", iteration_id="ITERATION_001")
    assert verify_run(root, run.run_id)["ok"]
    artifact = next((root / run.results_directory).glob("artifacts/value.txt"))
    artifact.write_text("changed")
    assert not verify_run(root, run.run_id)["ok"]

    destination = root / ".smairt/contracts/v1"
    assert len(export_contracts(destination)) == 14
    assert check_contracts(destination)["ok"]


def test_zoo_and_cline_adapters_preserve_local_edits(tmp_path: Path) -> None:
    root = project(tmp_path)
    assert install_harness(root, "zoo")["installed"]
    assert (root / ".roo/rules-code/01-research-code.md").exists()
    assert install_harness(root, "cline")["installed"]
    assert (root / ".clinerules/research-code.md").exists()
    assert (root / ".cline/workflows/smairt-next.md").exists()

    managed = root / ".roo/rules/01-smairt.md"
    managed.write_text(managed.read_text() + "Local policy.\n")
    assert ".roo/rules/01-smairt.md" in harness_status(root, "zoo")["modified"]
    try:
        install_harness(root, "zoo", upgrade=True)
    except ValueError as exc:
        assert "locally modified" in str(exc)
    else:
        raise AssertionError("adapter upgrade overwrote a local edit")


def test_v1_migration_preview_apply_and_safe_rollback(tmp_path: Path) -> None:
    root = project(tmp_path)
    config_path = root / "smairt.yaml"
    config = SmairtConfig.load(config_path)
    config.schema_version = 1
    config.dump(config_path)
    assert migration_plan(root)["applicable"]
    apply_migration(root)
    assert SmairtConfig.load(config_path).schema_version == 2
    assert rollback_migration(root)["rolled_back"]
    assert yaml.safe_load(config_path.read_text())["schema_version"] == 1


def test_summaries_are_hash_scoped_and_promotable(tmp_path: Path) -> None:
    root = project(tmp_path)
    contributor = add_contributor(root, "Summary Author")
    use_contributor(root, contributor.id)
    source = root / "background/project_description.md"
    summary_path = create_summary(root, source, "Concise source summary.")
    summary = list_summaries(root)[0]
    assert summary["fresh"]
    assert promote_summary(root, summary["id"]).exists()
    source.write_text(source.read_text() + "Changed.\n")
    assert not list_summaries(root)[0]["fresh"]
    assert summary_path.exists()


def test_paper_markdown_and_docx_builds_are_versioned(tmp_path: Path) -> None:
    root = project(tmp_path)
    contributor = add_contributor(root, "Paper Author")
    use_contributor(root, contributor.id)
    claim = root / "paper/claims/claim-ready.json"
    claim.write_text(
        '{"id":"claim-ready","status":"approved","evidence_ids":[],"reference_ids":[]}\n'
    )
    manuscript = begin_paper(root, "A Reproducible Study")
    assert manuscript.exists()
    markdown = build_paper(root, "md")
    docx = build_paper(root, "docx")
    assert markdown.read_text().startswith("# A Reproducible Study")
    assert docx.read_bytes().startswith(b"PK")


def test_correction_clears_active_evidence_and_marks_card_stale(tmp_path: Path) -> None:
    root = project(tmp_path)
    contributor = add_contributor(root, "Correcting Author")
    use_contributor(root, contributor.id)
    run_id = "RUN_OLD"
    run_path = root / "results/EXPERIMENT_001/ITERATION_001" / run_id / "run.json"
    run_path.parent.mkdir(parents=True)
    run_path.write_text('{"run_id":"RUN_OLD"}\n')
    selection = root / "analysis/EXPERIMENT_001/selection.yaml"
    selection.parent.mkdir(parents=True)
    selection.write_text("run_id: RUN_OLD\nstatus: ACCEPTED\n")
    evidence = root / "paper/evidence/evidence-run_old.json"
    evidence.write_text('{"id":"evidence-run_old","run_id":"RUN_OLD","status":"current"}\n')
    config = SmairtConfig.load(root / "smairt.yaml")
    config.active.accepted_run = run_id
    config.dump(root / "smairt.yaml")
    assert correct_run(root, "retract", run_id, "Invalid calibration").exists()
    assert SmairtConfig.load(root / "smairt.yaml").active.accepted_run is None
    assert json.loads(evidence.read_text())["status"] == "retracted"


def test_reference_edit_and_explicit_verification(tmp_path: Path) -> None:
    root = project(tmp_path)
    record = ReferenceRecord(
        id="reference-1",
        title="Original",
        authors=["Ada Author"],
        year=2024,
        doi="10.1000/example",
        local_path="pdfs/example.pdf",
        sha256="0" * 64,
        citation_key="author-2024-original",
    )
    save_index(root, [record])
    assert normalize_doi("https://doi.org/10.1000/EXAMPLE") == "10.1000/example"
    edited = edit_reference(root, record.id, "title", "Corrected", "ada")
    assert edited.edit_history[-1]["previous"] == "Original"
    verified = verify_reference(root, record.id, "ada")
    assert verified.verification_status == "verified"
