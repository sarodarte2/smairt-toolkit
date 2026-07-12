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
    validate_proposal_set,
)
from smairt.runner import run_experiment
from smairt.scaffold import create_project


def project(tmp_path: Path) -> Path:
    root = tmp_path / "research"
    create_project(
        root,
        name="Feasibility",
        author="Researcher",
        question="Is the approach feasible?",
        classification=DataClassification.UNPUBLISHED,
        initialize_git=False,
        environment_mode=EnvironmentMode.NONE,
    )
    return root


def complete_proposals(path: Path) -> None:
    content = path.read_text()
    content = content.replace("[Specific, falsifiable statement]", "A measurable prediction")
    content = content.replace(
        "[Reference indexed sources and distinguish inference]", "Reasoning from reference_001"
    )
    content = content.replace("[Expected observation]", "A held-out difference")
    path.write_text(content)


def test_full_research_and_paper_provenance(tmp_path: Path) -> None:
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
    experiment = create_experiment(root, title="Baseline", hypothesis_id="HYPOTHESIS_001")
    assert experiment.name.startswith("EXPERIMENT_001")
    record = run_experiment(
        root,
        experiment_id="EXPERIMENT_001",
        iteration_id="ITERATION_001",
        command=[sys.executable, "run.py"],
    )
    assert record.exit_code == 0
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
