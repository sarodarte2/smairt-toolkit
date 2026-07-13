"""Tests for adaptive workflow guidance, readable code, and safe upgrades."""

from pathlib import Path

import yaml

from smairt.code_quality import build_code_index, validate_code
from smairt.guidance import next_guidance
from smairt.models import DataClassification, Decision
from smairt.paper import create_claim, create_evidence_card, review_claim
from smairt.research import create_background, create_experiment, record_decision
from smairt.runner import run_experiment
from smairt.scaffold import create_project
from smairt.upgrade import upgrade_project


def make_project(tmp_path: Path) -> Path:
    """Create a small valid project shared by guidance and upgrade tests."""
    root = tmp_path / "guided"
    create_project(
        root,
        name="Guided Research",
        author="Researcher",
        question="What can the evidence support?",
        classification=DataClassification.UNPUBLISHED,
        initialize_git=False,
        confirm_contributor=True,
    )
    return root


def test_guidance_advances_from_setup_to_background(tmp_path: Path) -> None:
    """Verify durable artifacts advance guidance through early research stages."""
    root = make_project(tmp_path)
    initial = next_guidance(root)
    assert initial["stage"] == "project_setup"
    assert initial["recommended"]["id"] == "add_references"

    (root / "references/index.yaml").write_text(
        yaml.safe_dump(
            {
                "references": [
                    {
                        "id": "reference_001",
                        "title": "Example",
                        "local_path": "pdfs/example.pdf",
                        "sha256": "0" * 64,
                    }
                ]
            }
        )
    )
    indexed = next_guidance(root)
    assert indexed["stage"] == "references_indexed"
    create_background(root)
    assert next_guidance(root)["stage"] == "background_draft"


def test_numbered_entrypoint_is_indexed_and_warning_oriented(tmp_path: Path) -> None:
    """Verify generated code is numbered, parseable, indexed, and warning-oriented."""
    root = make_project(tmp_path)
    experiment = create_experiment(root, title="Readable Baseline", purpose="Test wiring")
    metadata = yaml.safe_load((experiment / "experiment.yaml").read_text())
    assert metadata["entrypoint"] == "script_001_readable_baseline.py"
    script = experiment / "iterations/ITERATION_001" / metadata["entrypoint"]
    assert "Inputs:" in script.read_text()
    assert "def main() -> None:" in script.read_text()

    index = build_code_index(root)
    assert index["modules"][0]["path"].endswith(metadata["entrypoint"])
    findings = validate_code(root)
    assert any(item["code"] == "code.placeholder" for item in findings)
    assert all(item["severity"] == "warning" for item in findings)


def test_upgrade_previews_backs_up_and_preserves_research(tmp_path: Path) -> None:
    """Verify managed guidance upgrades preserve authored scientific content."""
    root = make_project(tmp_path)
    contribution = root / "prompts/intellectual_contribution.md"
    contribution.write_text("Researcher-authored contribution.\n")
    agents = root / "AGENTS.md"
    agents.write_text(agents.read_text() + "\nLocal laboratory guidance.\n")
    skill = root / ".agents/skills/smairt-research/SKILL.md"
    skill.write_text("Local edited guidance.\n")

    preview = upgrade_project(root)
    assert not preview["applied"]
    assert any(item["path"].endswith("SKILL.md") for item in preview["changes"])
    assert "Local laboratory guidance." in agents.read_text()

    applied = upgrade_project(root, apply=True)
    assert applied["applied"]
    assert contribution.read_text() == "Researcher-authored contribution.\n"
    backup = root / str(applied["backup"]) / ".agents/skills/smairt-research/SKILL.md"
    assert backup.read_text() == "Local edited guidance.\n"
    assert "Local laboratory guidance." in agents.read_text()
    assert upgrade_project(root)["changes"] == []


def test_guidance_advances_from_accepted_run_into_paper_workflow(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    create_experiment(root, title="Evidence", purpose="Generate accepted evidence")
    run = run_experiment(root, experiment_id="EXPERIMENT_001", iteration_id="ITERATION_001")
    record_decision(
        root,
        experiment_id="EXPERIMENT_001",
        iteration_id="ITERATION_001",
        run_id=run.run_id,
        decision=Decision.ACCEPT,
        rationale="Verified evidence run.",
        decided_by="Researcher",
    )
    assert next_guidance(root)["stage"] == "evidence_review"

    evidence = create_evidence_card(
        root,
        run.run_id,
        purpose="Exercise guidance",
        observed_result="The run completed.",
        limitations="Smoke-only evidence.",
        decision="ACCEPT",
    )
    assert next_guidance(root)["stage"] == "claim_proposal"
    claim = create_claim(root, "The workflow completed.", [evidence.stem])
    assert next_guidance(root)["stage"] == "claim_review"
    review_claim(root, claim.stem, "approved")
    assert next_guidance(root)["stage"] == "paper_ready"
