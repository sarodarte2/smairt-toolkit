"""Hypothesis, experiment, iteration, and decision lifecycle."""

from __future__ import annotations

import json
import re
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
    """Expand the initial project framing into a source-grounded background workspace."""
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
    """Create and retain a three-option hypothesis proposal document."""
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
    """Check that proposal options are distinct, complete, and placeholder-free."""
    content = path.read_text(encoding="utf-8")
    errors: list[str] = []
    for label in ("A", "B", "C"):
        if f"## Option {label}:" not in content:
            errors.append(f"missing option {label}")
    titles = re.findall(r"^## Option [ABC]:\s*(.+)$", content, flags=re.MULTILINE)
    if len(titles) == 3 and len({title.strip().lower() for title in titles}) != 3:
        errors.append("proposal option titles must be distinct")
    if re.search(r"\[[^\]]+\]", content):
        errors.append("proposal set still contains required placeholders")
    required_subsections = (
        "Hypothesis",
        "Reasoning and Evidence",
        "Falsifiable Prediction",
        "Null or Competing Explanation",
        "Required Data and Proposed Test",
        "Feasibility, Confounders, and Risks",
        "Difference from Other Options",
    )
    for label in ("A", "B", "C"):
        option_match = re.search(
            rf"^## Option {label}:.*?(?=^## Option [ABC]:|\Z)",
            content,
            flags=re.MULTILINE | re.DOTALL,
        )
        option = option_match.group(0) if option_match else ""
        for subsection in required_subsections:
            body = _section_body(option, f"### {subsection}")
            if not body:
                errors.append(f"option {label} has empty section: {subsection}")
    return errors


def find_hypothesis(root: Path, hypothesis_id: str) -> Path:
    """Resolve exactly one canonical hypothesis file from its stable ID."""
    matches = list((root / "hypotheses").glob(f"{hypothesis_id}_*.md"))
    if len(matches) != 1:
        raise FileNotFoundError(f"Hypothesis {hypothesis_id} not found")
    return matches[0]


def validate_hypothesis(path: Path) -> list[str]:
    """Check whether a selected hypothesis is complete enough to govern a run."""
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
        elif not _section_body(content, section):
            errors.append(f"empty section: {section.removeprefix('## ')}")
    if "[Complete" in content:
        errors.append("hypothesis still contains required completion placeholders")
    return errors


def validate_background(root: Path) -> list[str]:
    """Validate structural completeness and indexed-reference grounding."""
    path = root / "background/initial_background.md"
    content = path.read_text(encoding="utf-8")
    errors: list[str] = []
    required = (
        "## Initial Question",
        "## Project Description",
        "## Current Context",
        "## What Is Known",
        "## What the Available Evidence Can Address",
        "## Limitations and Open Questions",
        "## Evidence Gaps",
        "## References Used",
    )
    for section in required:
        if not _section_body(content, section):
            errors.append(f"missing or empty section: {section.removeprefix('## ')}")
    if "[Codex:" in content or "[Not specified" in content:
        errors.append("background still contains required placeholders")
    indexed = {
        str(item.get("id"))
        for item in (yaml.safe_load((root / "references/index.yaml").read_text()) or {}).get(
            "references", []
        )
    }
    cited = set(re.findall(r"\breference_\d+\b", content))
    unknown = sorted(cited - indexed)
    if unknown:
        errors.append(f"background cites unknown reference IDs: {', '.join(unknown)}")
    if indexed and not cited:
        errors.append("background does not cite any indexed reference IDs")
    return errors


def _section_body(content: str, heading: str) -> str:
    """Extract Markdown content beneath one level-two or level-three heading."""
    match = re.search(
        rf"^{re.escape(heading)}\s*$\n(.*?)(?=^#{{2,3}}\s|\Z)",
        content,
        flags=re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() if match else ""


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
    """Record an explicit human selection as the canonical active hypothesis."""
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
    # Activation is a human intellectual contribution, so update both the
    # machine-readable pointer and the append-only contribution log.
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
    """Create a numbered experiment, readable entrypoint, and first iteration."""
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
    script_name = (
        f"script_{experiment_id.removeprefix('EXPERIMENT_')}_{slugify(title).replace('-', '_')}.py"
    )
    metadata = {
        "id": experiment_id,
        "title": title,
        "hypothesis": hypothesis_id,
        "purpose": purpose,
        "created_at": utc_now(),
        "status": "ACTIVE",
        "entrypoint": script_name,
    }
    (path / "experiment.yaml").write_text(yaml.safe_dump(metadata, sort_keys=False))
    (iteration / "config.yaml").write_text(
        "seed: 1024\ndata: {}\nparameters: {}\n", encoding="utf-8"
    )
    (iteration / script_name).write_text(
        _experiment_script(
            experiment_id=experiment_id,
            iteration_id="ITERATION_001",
            title=title,
            hypothesis_id=hypothesis_id,
            purpose=purpose,
        ),
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
    """Copy the prior method into a new iteration while preserving the old one."""
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
    metadata = yaml.safe_load((experiment / "experiment.yaml").read_text()) or {}
    entrypoint = str(metadata.get("entrypoint", "run.py"))
    for name in ("config.yaml", entrypoint):
        if (source / name).exists():
            shutil.copy2(source / name, destination / name)
    copied_entrypoint = destination / entrypoint
    if copied_entrypoint.exists():
        content = copied_entrypoint.read_text(encoding="utf-8")
        copied_entrypoint.write_text(
            content.replace(f"Iteration: {source_id}", f"Iteration: {iteration_id}"),
            encoding="utf-8",
        )
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


def _experiment_script(
    *,
    experiment_id: str,
    iteration_id: str,
    title: str,
    hypothesis_id: str | None,
    purpose: str | None,
) -> str:
    """Render the novice-readable Python skeleton for a new experiment."""
    scientific_link = f"Hypothesis: {hypothesis_id}" if hypothesis_id else f"Purpose: {purpose}"
    return f'''#!/usr/bin/env python3
"""{experiment_id}: {title}

Iteration: {iteration_id}
{scientific_link}
Depends on: iteration config.yaml and declared project data
Inputs: define and validate inputs in load_inputs()
Outputs: artifacts in SMAIRT_RESULTS_DIR and figures in SMAIRT_FIGURES_DIR

Keep this module readable to a novice researcher. Explain scientific assumptions and
non-obvious transformations, and keep configurable values in config.yaml.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

# === SMAIRT PATHS AND CONFIGURATION ===
CONFIG_PATH = Path(os.environ["SMAIRT_CONFIG_PATH"])
RESULTS_DIR = Path(os.environ["SMAIRT_RESULTS_DIR"])
FIGURES_DIR = Path(os.environ["SMAIRT_FIGURES_DIR"])


def load_configuration(config_path: Path) -> dict[str, Any]:
    """Load and validate the iteration configuration before analysis begins."""
    configuration = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {{}}
    if "seed" not in configuration:
        raise ValueError("config.yaml must define a deterministic seed")
    return configuration


def run_analysis(configuration: dict[str, Any]) -> None:
    """Execute the scientific analysis and write declared result artifacts."""
    # TODO: implement experiment using descriptive variables and explicit units.
    print(f"Configured deterministic seed: {{configuration['seed']}}")


def main() -> None:
    """Validate configuration, run the analysis, and report output locations."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    configuration = load_configuration(CONFIG_PATH)

    print("=" * 72)
    print("Experiment: {experiment_id} — {title}")
    print("Iteration: {iteration_id}")
    print("{scientific_link}")
    print("=" * 72)

    run_analysis(configuration)

    print("=" * 72)
    print(f"Results directory: {{RESULTS_DIR}}")
    print(f"Figures directory: {{FIGURES_DIR}}")
    print("Experiment execution complete")


if __name__ == "__main__":
    main()
'''


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
    """Append a human research decision and update accepted evidence when appropriate."""
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
    # Acceptance creates a single current selection used by paper provenance.
    # Other decisions remain in the append-only history without elevating a run.
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
    """Append a metadata correction beside a record without rewriting history."""
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
