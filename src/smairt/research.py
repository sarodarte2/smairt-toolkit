"""Hypothesis, experiment, iteration, and decision lifecycle."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml

from smairt.models import Decision, SmairtConfig, utc_now
from smairt.utils import next_numeric_id, sha256_file, slugify

PROPOSAL_OPTION = """## Option {label}: [Distinct title]

### Hypothesis
[Specific, falsifiable statement]

### Reasoning and Evidence
[Reference indexed sources and distinguish inference]

### Falsifiable Prediction
[Expected observation]

### Null or Competing Explanation
[Alternative explanation]

### Required Data and Proposed Test
[Data, controls, unit of analysis, and test]

### Feasibility, Confounders, and Risks
[Practical feasibility and likely failure modes]

### Difference from Other Options
[Why this is scientifically distinct]
"""


def create_background(root: Path) -> Path:
    path = root / "background/initial_background.md"
    if "Status: DRAFT" not in path.read_text(encoding="utf-8"):
        raise FileExistsError("initial background already contains project content")
    question = (root / "background/initial_question.md").read_text(encoding="utf-8")
    description = (root / "background/project_description.md").read_text(encoding="utf-8")
    path.write_text(
        "# Initial Background\n\n"
        "Status: DRAFT\n\n"
        "## Initial Question\n\n"
        f"{question.splitlines()[-1]}\n\n"
        "## Project Description\n\n"
        f"{description.splitlines()[-1]}\n\n"
        "## Current Context\n\n"
        "[Codex: synthesize indexed local references with reference IDs and page ranges.]\n\n"
        "## What Is Known\n\n"
        "## What the Available Evidence Can Address\n\n"
        "## Limitations and Open Questions\n\n"
        "## Evidence Gaps\n\n"
        "## References Used\n",
        encoding="utf-8",
    )
    return path


def create_proposal_set(root: Path) -> Path:
    proposal_dir = root / "hypotheses/proposals"
    proposal_id = next_numeric_id(list(proposal_dir.glob("PROPOSAL_SET_*.md")), "PROPOSAL_SET_")
    background = root / "background/initial_background.md"
    reference_index = root / "references/index.yaml"
    content = [
        "---",
        f"id: {proposal_id}",
        "status: DRAFT",
        f"created_at: {utc_now()}",
        f"background_sha256: {sha256_file(background)}",
        f"reference_index_sha256: {sha256_file(reference_index)}",
        "---",
        "",
        f"# Hypothesis Proposal Set {proposal_id}",
        "",
        "Codex must complete all three options with meaningfully distinct scientific directions.",
        "",
    ]
    for label in ("A", "B", "C"):
        content.extend([PROPOSAL_OPTION.format(label=label), ""])
    path = proposal_dir / f"{proposal_id}.md"
    path.write_text("\n".join(content), encoding="utf-8")
    return path


def validate_proposal_set(path: Path) -> list[str]:
    content = path.read_text(encoding="utf-8")
    errors: list[str] = []
    for label in ("A", "B", "C"):
        if f"## Option {label}:" not in content:
            errors.append(f"missing option {label}")
    placeholders = (
        "[Specific, falsifiable statement]",
        "[Reference indexed sources and distinguish inference]",
        "[Expected observation]",
    )
    if any(placeholder in content for placeholder in placeholders):
        errors.append("proposal set still contains required placeholders")
    return errors


def find_hypothesis(root: Path, hypothesis_id: str) -> Path:
    matches = list((root / "hypotheses").glob(f"{hypothesis_id}_*.md"))
    if len(matches) != 1:
        raise FileNotFoundError(f"Hypothesis {hypothesis_id} not found")
    return matches[0]


def validate_hypothesis(path: Path) -> list[str]:
    content = path.read_text(encoding="utf-8")
    errors: list[str] = []
    required_sections = (
        "## Statement",
        "## Rationale",
        "## Falsifiable Prediction",
        "## Null or Competing Explanation",
        "## Required Data and Controls",
        "## Success and Failure Criteria",
        "## Known Confounders",
        "## Human Selection Rationale",
    )
    for section in required_sections:
        if section not in content:
            errors.append(f"missing section: {section.removeprefix('## ')}")
    if "[Complete" in content:
        errors.append("hypothesis still contains required completion placeholders")
    return errors


def activate_hypothesis(
    root: Path,
    proposal_set: Path,
    option: str,
    *,
    title: str,
    statement: str,
    selected_by: str,
    rationale: str,
) -> Path:
    option = option.upper()
    if option not in {"A", "B", "C", "CUSTOM"}:
        raise ValueError("option must be A, B, C, or CUSTOM")
    if option != "CUSTOM" and validate_proposal_set(proposal_set):
        raise ValueError("proposal set must be completed before activation")
    hypothesis_id = next_numeric_id(
        list((root / "hypotheses").glob("HYPOTHESIS_*.md")), "HYPOTHESIS_"
    )
    slug = slugify(title)
    background = root / "background/initial_background.md"
    references = root / "references/index.yaml"
    content = f"""---
id: {hypothesis_id}
status: ACTIVE
proposal_set: {proposal_set.stem}
selected_option: {option}
selected_by: {json.dumps(selected_by)}
selected_at: {utc_now()}
background_sha256: {sha256_file(background)}
reference_index_sha256: {sha256_file(references)}
---

# {hypothesis_id}: {title}

## Statement
{statement}

## Rationale
[Complete from the selected proposal and human edits.]

## Falsifiable Prediction
[Complete before running the linked experiment.]

## Null or Competing Explanation
[Complete before running the linked experiment.]

## Required Data and Controls

## Success and Failure Criteria

## Known Confounders

## Human Selection Rationale
{rationale}
"""
    path = root / "hypotheses" / f"{hypothesis_id}_{slug}.md"
    path.write_text(content, encoding="utf-8")
    config = SmairtConfig.load(root / "smairt.yaml")
    config.active.hypothesis = hypothesis_id
    config.dump(root / "smairt.yaml")
    contribution = root / "prompts/intellectual_contribution.md"
    with contribution.open("a", encoding="utf-8") as stream:
        stream.write(
            f"\n## {utc_now()} — Activated {hypothesis_id}\n"
            f"- Selected by: {selected_by}\n- Proposal: {proposal_set.stem}, option {option}\n"
            f"- Rationale: {rationale}\n"
        )
    return path


def create_experiment(
    root: Path,
    *,
    title: str,
    hypothesis_id: str | None = None,
    purpose: str | None = None,
) -> Path:
    if not hypothesis_id and not purpose:
        raise ValueError("link a hypothesis or provide an exploratory purpose")
    if hypothesis_id:
        find_hypothesis(root, hypothesis_id)
    experiment_id = next_numeric_id(
        list((root / "experiments").glob("EXPERIMENT_*")), "EXPERIMENT_"
    )
    path = root / "experiments" / f"{experiment_id}_{slugify(title)}"
    iteration = path / "iterations/ITERATION_001"
    iteration.mkdir(parents=True)
    metadata = {
        "id": experiment_id,
        "title": title,
        "hypothesis": hypothesis_id,
        "purpose": purpose,
        "created_at": utc_now(),
        "status": "ACTIVE",
    }
    (path / "experiment.yaml").write_text(yaml.safe_dump(metadata, sort_keys=False))
    (iteration / "config.yaml").write_text(
        "seed: 1024\ndata: {}\nparameters: {}\n", encoding="utf-8"
    )
    (iteration / "run.py").write_text(
        '"""Experiment entrypoint. Read config/output paths from SMAIRT environment variables."""\n'
        "import os\n"
        "from pathlib import Path\n\n"
        "RESULTS_DIR = Path(os.environ[\"SMAIRT_RESULTS_DIR\"])\n"
        "FIGURES_DIR = Path(os.environ[\"SMAIRT_FIGURES_DIR\"])\n\n"
        "def main():\n"
        "    RESULTS_DIR.mkdir(parents=True, exist_ok=True)\n"
        "    FIGURES_DIR.mkdir(parents=True, exist_ok=True)\n"
        "    print(\"TODO: implement experiment\")\n\n"
        "if __name__ == \"__main__\":\n"
        "    main()\n",
        encoding="utf-8",
    )
    analysis = root / "analysis" / experiment_id
    analysis.mkdir(parents=True)
    (analysis / "ANALYSIS_ITERATION_001.md").write_text(
        f"# Analysis: {experiment_id} / ITERATION_001\n\n"
        "## Executive Summary\n\n## Observed Results\n\n## Interpretation\n\n"
        "## Limitations and Confounders\n\n## Decision\n\n## Next Steps\n",
        encoding="utf-8",
    )
    config = SmairtConfig.load(root / "smairt.yaml")
    config.active.experiment = experiment_id
    config.active.iteration = "ITERATION_001"
    config.dump(root / "smairt.yaml")
    return path


def new_iteration(root: Path, experiment_id: str, source_id: str) -> Path:
    experiment = next((root / "experiments").glob(f"{experiment_id}_*"), None)
    if experiment is None:
        raise FileNotFoundError(experiment_id)
    iterations = experiment / "iterations"
    source = iterations / source_id
    if not source.exists():
        raise FileNotFoundError(source)
    iteration_id = next_numeric_id(list(iterations.glob("ITERATION_*")), "ITERATION_")
    destination = iterations / iteration_id
    destination.mkdir()
    for name in ("config.yaml", "run.py"):
        if (source / name).exists():
            shutil.copy2(source / name, destination / name)
    (destination / "CHANGE.md").write_text(
        f"# Changes from {source_id}\n\n[Record the scientific or methodological change.]\n"
    )
    analysis = root / "analysis" / experiment_id / f"ANALYSIS_{iteration_id}.md"
    analysis.write_text(
        f"# Analysis: {experiment_id} / {iteration_id}\n\n## Changes\n\n"
        "## Results\n\n## Interpretation\n\n## Decision\n"
    )
    config = SmairtConfig.load(root / "smairt.yaml")
    config.active.experiment = experiment_id
    config.active.iteration = iteration_id
    config.dump(root / "smairt.yaml")
    return destination


def record_decision(
    root: Path,
    *,
    experiment_id: str,
    iteration_id: str,
    run_id: str,
    decision: Decision,
    rationale: str,
    decided_by: str,
) -> Path:
    run_path = root / "results" / experiment_id / iteration_id / run_id / "run.json"
    if not run_path.exists():
        raise FileNotFoundError(f"Run record not found: {run_path.relative_to(root)}")
    analysis_dir = root / "analysis" / experiment_id
    analysis_dir.mkdir(parents=True, exist_ok=True)
    path = analysis_dir / "decisions.yaml"
    payload = yaml.safe_load(path.read_text()) if path.exists() else {"decisions": []}
    payload["decisions"].append(
        {
            "run_id": run_id,
            "iteration_id": iteration_id,
            "decision": decision.value,
            "rationale": rationale,
            "decided_by": decided_by,
            "decided_at": utc_now(),
        }
    )
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    if decision is Decision.ACCEPT:
        (analysis_dir / "selection.yaml").write_text(
            yaml.safe_dump(
                {
                    "experiment_id": experiment_id,
                    "iteration_id": iteration_id,
                    "run_id": run_id,
                    "status": "ACCEPTED",
                    "selected_at": utc_now(),
                    "selected_by": decided_by,
                    "rationale": rationale,
                },
                sort_keys=False,
            )
        )
        config = SmairtConfig.load(root / "smairt.yaml")
        config.active.accepted_run = run_id
        config.dump(root / "smairt.yaml")
    return path


def amend_record(path: Path, *, field: str, previous: str, corrected: str, reason: str) -> None:
    amendment = path.with_suffix(path.suffix + ".amendments.yaml")
    payload = yaml.safe_load(amendment.read_text()) if amendment.exists() else {"amendments": []}
    payload["amendments"].append(
        {
            "field": field,
            "previous": previous,
            "corrected": corrected,
            "reason": reason,
            "recorded_at": utc_now(),
        }
    )
    amendment.write_text(yaml.safe_dump(payload, sort_keys=False))
