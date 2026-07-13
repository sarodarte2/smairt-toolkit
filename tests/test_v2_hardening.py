"""End-to-end hardening tests for v2 publication, metadata, and correction gates."""

from __future__ import annotations

import json
import subprocess
import sys
from importlib.resources import files
from pathlib import Path

import pytest
import yaml

from smairt.contracts import check_contracts, export_contracts
from smairt.corrections import correct_run
from smairt.models import DataClassification, Decision, ReferenceRecord
from smairt.paper import (
    begin_paper,
    build_paper,
    create_claim,
    create_evidence_card,
    create_outline,
    draft_section,
    review_claim,
    review_section,
    validate_paper,
)
from smairt.references import enrich_openalex, enrich_reference, load_index, save_index
from smairt.research import create_experiment, record_decision
from smairt.runner import run_experiment
from smairt.safety import refresh_repository_visibility, safety_policy_findings, safety_status
from smairt.scaffold import create_project
from smairt.summaries import create_summary, promote_summary, supersede_summary


def make_project(tmp_path: Path, classification=DataClassification.UNPUBLISHED) -> Path:
    """Create a contributor-confirmed v2 project for consequential actions."""
    root = tmp_path / "hardening"
    create_project(
        root,
        name="Hardening",
        author="Researcher",
        classification=classification,
        initialize_git=False,
        confirm_contributor=True,
    )
    return root


def accepted_run(root: Path) -> str:
    """Execute and accept one exploratory smoke experiment."""
    create_experiment(root, title="Evidence", purpose="Exercise publication gates")
    run = run_experiment(root, experiment_id="EXPERIMENT_001", iteration_id="ITERATION_001")
    record_decision(
        root,
        experiment_id="EXPERIMENT_001",
        iteration_id="ITERATION_001",
        run_id=run.run_id,
        decision=Decision.ACCEPT,
        rationale="Verified smoke evidence.",
        decided_by="Researcher",
    )
    return run.run_id


def test_complete_evidence_claim_and_paper_build(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    run_id = accepted_run(root)
    evidence_path = create_evidence_card(
        root,
        run_id,
        purpose="Verify the path",
        observed_result="The deterministic run completed.",
        limitations="This is a smoke result.",
        decision="ACCEPT",
    )
    claim_path = create_claim(
        root, "The workflow completed deterministically.", [evidence_path.stem]
    )
    review_claim(root, claim_path.stem, "approved")
    assert create_outline(root).exists()
    begin_paper(root, "Verified Workflow")
    sections = ("Abstract", "Introduction", "Methods", "Results", "Discussion", "References")
    for section in sections:
        draft_section(root, section, f"Reviewed {section.lower()} prose.", [claim_path.stem])
        review_section(root, section, [claim_path.stem])
    assert validate_paper(root) == []
    assert build_paper(root, "md").exists()
    assert build_paper(root, "docx", line_numbering=True).exists()


def test_claim_approval_rejects_stale_evidence_and_citations(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    stale = root / "paper/evidence/evidence-stale.json"
    stale.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "id": "evidence-stale",
                "run_id": "RUN_NONE",
                "purpose": "Negative approval test",
                "observed_result": "No current result",
                "limitations": "Synthetic stale evidence",
                "decision": "RETRACTED",
                "contributor": "researcher",
                "status": "retracted",
                "created_at": "2026-01-01T00:00:00+00:00",
                "run_record_sha256": "0" * 64,
            }
        )
        + "\n"
    )
    claim = create_claim(root, "Unsupported statement.", [stale.stem], ["missing-reference"])
    try:
        review_claim(root, claim.stem, "approved")
    except ValueError as exc:
        assert "stale evidence" in str(exc)
        assert "unverified citation" in str(exc)
    else:
        raise AssertionError("unsupported claim was approved")


def test_supersession_requires_and_records_verified_replacement(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    old_run = accepted_run(root)
    replacement = run_experiment(
        root, experiment_id="EXPERIMENT_001", iteration_id="ITERATION_001"
    ).run_id
    correction = correct_run(
        root, "supersede", old_run, "Corrected execution", replacement_run=replacement
    )
    payload = json.loads(correction.read_text())
    assert payload["replacement_run"] == replacement
    selection = yaml.safe_load((root / "analysis/EXPERIMENT_001/selection.yaml").read_text())
    assert selection["status"] == "SUPERSEDED"


def test_supersession_rejects_failed_replacement_with_valid_manifest(tmp_path: Path) -> None:
    """A manifest proves integrity, not that an execution produced usable evidence."""
    root = make_project(tmp_path)
    old_run = accepted_run(root)
    failed = run_experiment(
        root,
        experiment_id="EXPERIMENT_001",
        iteration_id="ITERATION_001",
        command=[sys.executable, "-c", "raise SystemExit(9)"],
    )
    with pytest.raises(ValueError, match="successfully completed"):
        correct_run(
            root,
            "supersede",
            old_run,
            "Invalid replacement",
            replacement_run=failed.run_id,
        )


class FakeResponse:
    """Minimal context-managed HTTP response for deterministic enrichment tests."""

    def __init__(self, payload: dict[str, object]):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode()


def test_crossref_and_openalex_enrichment_preserve_snapshots(tmp_path: Path, monkeypatch) -> None:
    root = make_project(tmp_path)
    save_index(
        root,
        [
            ReferenceRecord(
                id="ref",
                title="Local title",
                authors=["Local Author"],
                doi="10.1000/example",
                local_path="pdfs/ref.pdf",
                sha256="0" * 64,
            )
        ],
    )
    crossref = {
        "message": {
            "title": ["Crossref title"],
            "author": [{"given": "Ada", "family": "Author"}],
            "container-title": ["Journal"],
            "publisher": "Publisher",
        }
    }
    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: FakeResponse(crossref))
    assert enrich_reference(root, "ref").title == "Crossref title"
    openalex = {
        "id": "https://openalex.org/W1",
        "publication_date": "2024-01-02",
        "primary_location": {"landing_page_url": "https://example.org", "source": {}},
    }
    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: FakeResponse(openalex))
    enriched = enrich_openalex(root, "ref", "test-key")
    assert enriched.identifiers["openalex"].endswith("W1")
    assert len(load_index(root)[0].source_provenance) == 2
    assert len(list((root / "references/provenance/ref").glob("*.json"))) == 2


def test_summary_supersession_updates_canonical_pointer(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    source = root / "background/project_description.md"
    previous = create_summary(root, source, "Initial summary")
    promote_summary(root, previous.stem)
    source.write_text(source.read_text() + "\nNew evidence.\n")
    replacement = create_summary(root, source, "Updated summary")
    supersede_summary(root, previous.stem, replacement.stem)
    canonical = next((root / "summaries/canonical").glob("*.json"))
    assert json.loads(canonical.read_text())["summary_id"] == replacement.stem


def test_contract_checker_reports_corrupt_fixture(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    destination = root / "contracts"
    export_contracts(destination)
    (destination / "fixtures/cline.json").write_text("not json")
    report = check_contracts(destination)
    assert not report["ok"]
    assert "invalid fixture JSON" in report["findings"][0]


def test_packaged_skill_matches_contributor_skill() -> None:
    """Keep the distributable scaffold resource aligned with the repository skill."""
    package = files("smairt.resources")
    assert (
        package.joinpath("smairt-research.md").read_text()
        == Path("skills/smairt-research/SKILL.md").read_text()
    )
    assert (
        package.joinpath("workflow.md").read_text()
        == Path("skills/smairt-research/references/workflow.md").read_text()
    )
    assert (
        package.joinpath("openai-agent.yaml").read_text()
        == Path("skills/smairt-research/agents/openai.yaml").read_text()
    )


def test_observed_visibility_overrides_conflicting_attestation(tmp_path: Path, monkeypatch) -> None:
    """Treat authenticated host visibility as authoritative and report disagreement."""
    root = make_project(tmp_path)
    config = yaml.safe_load((root / "smairt.yaml").read_text())
    config["repository_attestation"] = {
        "acknowledged": True,
        "visibility": "private",
        "contributor_id": config["active_contributor"],
        "acknowledged_at": "2026-01-01T00:00:00Z",
    }
    (root / "smairt.yaml").write_text(yaml.safe_dump(config, sort_keys=False))

    def fake_run(command, **kwargs):
        output = "git@github.com:org/project.git\n" if command[0] == "git" else "PUBLIC\n"
        return subprocess.CompletedProcess(command, 0, stdout=output, stderr="")

    monkeypatch.setattr("smairt.safety.shutil.which", lambda command: f"/usr/bin/{command}")
    monkeypatch.setattr("smairt.safety.subprocess.run", fake_run)
    refresh_repository_visibility(root)
    assert safety_status(root)["repository_visibility"] == "public"
    assert safety_status(root)["repository_visibility_mismatch"]
    assert any(
        finding["code"] == "repository.visibility-mismatch"
        for finding in safety_policy_findings(root)
    )
