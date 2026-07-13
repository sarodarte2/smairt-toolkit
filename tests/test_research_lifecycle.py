"""End-to-end tests for hypothesis, experiment, run, decision, and paper links."""

import sys
from pathlib import Path

import yaml

from smairt.models import DataClassification, Decision, EnvironmentMode
from smairt.paper import validate_paper
from smairt.research import (
    activate_hypothesis,
    create_background,
    create_experiment,
    create_proposal_set,
    new_iteration,
    record_decision,
    validate_hypothesis,
    validate_proposal_set,
)
from smairt.runner import run_experiment
from smairt.scaffold import create_project


def project(tmp_path: Path) -> Path:
    """Create a valid project fixture for full research-lifecycle tests."""
    root = tmp_path / "research"
    create_project(
        root,
        name="Feasibility",
        author="Researcher",
        question="Is the approach feasible?",
        classification=DataClassification.UNPUBLISHED,
        initialize_git=False,
        environment_mode=EnvironmentMode.NONE,
        confirm_contributor=True,
    )
    return root


def complete_proposals(path: Path) -> None:
    """Replace every proposal placeholder with distinct test content."""
    content = path.read_text()
    for label, title in zip(
        ("A", "B", "C"), ("Direct fit", "Robust fit", "Design study"), strict=True
    ):
        content = content.replace(
            f"## Option {label}: [Distinct title]", f"## Option {label}: {title}"
        )
    content = content.replace("[Specific, falsifiable statement]", "A measurable prediction")
    content = content.replace(
        "[Reference indexed sources and distinguish inference]", "Reasoning from reference_001"
    )
    content = content.replace("[Expected observation]", "A held-out difference")
    content = content.replace("[Alternative explanation]", "A competing mechanism")
    content = content.replace(
        "[Data, controls, unit of analysis, and test]", "Replicated data with controls"
    )
    content = content.replace(
        "[Practical feasibility and likely failure modes]", "Feasible with known confounders"
    )
    content = content.replace(
        "[Why this is scientifically distinct]", "Tests a distinct scientific mechanism"
    )
    path.write_text(content)


def test_full_research_and_paper_provenance(tmp_path: Path) -> None:
    """Exercise the complete hypothesis-to-accepted-paper-evidence chain."""
    root = project(tmp_path)
    create_background(root)
    background = root / "background/initial_background.md"
    background.write_text(background.read_text().replace("[Codex:", "[Completed:"))
    proposals = create_proposal_set(root)
    complete_proposals(proposals)
    assert validate_proposal_set(proposals) == []
    hypothesis = activate_hypothesis(
        root,
        proposals,
        "A",
        title="Grouped validation",
        statement="Grouped validation preserves a measurable signal.",
        selected_by="Researcher",
        rationale="Most feasible option.",
    )
    assert hypothesis.exists()
    hypothesis.write_text(
        hypothesis.read_text()
        .replace("[Complete from the selected proposal and human edits.]", "Selected rationale.")
        .replace(
            "[Complete before running the linked experiment.]",
            "A measurable held-out observation.",
        )
        .replace(
            "## Required Data and Controls\n\n",
            "## Required Data and Controls\nReplicated held-out measurements.\n\n",
        )
        .replace(
            "## Success and Failure Criteria\n\n",
            "## Success and Failure Criteria\nPredefined recovery error threshold.\n\n",
        )
        .replace(
            "## Known Confounders\n\n",
            "## Known Confounders\nMeasurement noise and split leakage.\n\n",
        )
    )
    assert validate_hypothesis(hypothesis) == []
    experiment = create_experiment(root, title="Baseline", hypothesis_id="HYPOTHESIS_001")
    assert experiment.name.startswith("EXPERIMENT_001")
    record = run_experiment(
        root,
        experiment_id="EXPERIMENT_001",
        iteration_id="ITERATION_001",
    )
    assert record.exit_code == 0
    assert record.command[-1] == "script_001_baseline.py"
    record_decision(
        root,
        experiment_id="EXPERIMENT_001",
        iteration_id="ITERATION_001",
        run_id=record.run_id,
        decision=Decision.ACCEPT,
        rationale="Deterministic smoke result passed.",
        decided_by="Researcher",
    )
    (root / "paper/manifest.yaml").write_text(
        yaml.safe_dump({"elements": [{"id": "figure_1", "run_id": record.run_id}]})
    )
    assert validate_paper(root) == []
    assert new_iteration(root, "EXPERIMENT_001", "ITERATION_001").name == "ITERATION_002"


def test_research_links_and_decisions_must_reference_real_records(tmp_path: Path) -> None:
    """Reject experiments and decisions whose durable source records are missing."""
    root = project(tmp_path)
    try:
        create_experiment(root, title="Missing", hypothesis_id="HYPOTHESIS_404")
    except FileNotFoundError as exc:
        assert "HYPOTHESIS_404" in str(exc)
    else:
        raise AssertionError("missing hypothesis link was accepted")

    create_experiment(root, title="Exploration", purpose="Check pipeline wiring")
    try:
        record_decision(
            root,
            experiment_id="EXPERIMENT_001",
            iteration_id="ITERATION_001",
            run_id="RUN_MISSING",
            decision=Decision.ACCEPT,
            rationale="Should fail.",
            decided_by="Researcher",
        )
    except FileNotFoundError as exc:
        assert "RUN_MISSING" in str(exc)
    else:
        raise AssertionError("decision without a run record was accepted")


def test_incomplete_hypothesis_blocks_execution(tmp_path: Path) -> None:
    """Keep the human-selected hypothesis completeness gate before execution."""
    root = project(tmp_path)
    create_background(root)
    proposals = create_proposal_set(root)
    complete_proposals(proposals)
    hypothesis = activate_hypothesis(
        root,
        proposals,
        "A",
        title="Incomplete hypothesis",
        statement="A measurable prediction.",
        selected_by="Researcher",
        rationale="Candidate direction.",
    )
    assert validate_hypothesis(hypothesis)
    create_experiment(root, title="Blocked experiment", hypothesis_id="HYPOTHESIS_001")
    try:
        run_experiment(
            root,
            experiment_id="EXPERIMENT_001",
            iteration_id="ITERATION_001",
            command=[sys.executable, "run.py"],
        )
    except ValueError as exc:
        assert "incomplete" in str(exc)
    else:
        raise AssertionError("incomplete hypothesis was allowed to run")
