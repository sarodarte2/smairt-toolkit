"""State-aware workflow guidance shared by the CLI and coding agents."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from smairt.models import SmairtConfig
from smairt.references import load_index
from smairt.research import (
    find_hypothesis,
    validate_background,
    validate_hypothesis,
    validate_proposal_set,
)


def _action(
    identifier: str,
    label: str,
    *,
    kind: str,
    recommended: bool = False,
    requires_human: bool = False,
    command: str | None = None,
    read: list[str] | None = None,
    prompt: str | None = None,
) -> dict[str, Any]:
    """Construct one stable Codex action with command, reading, or prompt metadata."""
    return {
        "id": identifier,
        "label": label,
        "kind": kind,
        "recommended": recommended,
        "requires_human": requires_human,
        "command": command,
        "read": read or [],
        "prompt": prompt,
    }


def _proposal_choices(path: Path) -> list[dict[str, Any]]:
    """Extract dynamic A/B/C hypothesis titles and add an explicit custom option."""
    content = path.read_text(encoding="utf-8")
    choices = []
    for label, title in re.findall(r"^## Option ([ABC]):\s*(.+)$", content, flags=re.MULTILINE):
        choices.append(
            _action(
                f"select_hypothesis_{label.lower()}",
                f"Option {label}: {title.strip()}",
                kind="human_choice",
                requires_human=True,
                read=[str(path)],
            )
        )
    choices.append(
        _action(
            "edit_or_custom_hypothesis",
            "Edit an option or provide a custom hypothesis",
            kind="human_choice",
            requires_human=True,
            read=[str(path)],
        )
    )
    return choices


def next_guidance(root: Path) -> dict[str, Any]:
    """Derive the next useful research action from durable project artifacts."""
    config = SmairtConfig.load(root / "smairt.yaml")
    references = load_index(root)
    background = root / "background/initial_background.md"
    proposals = sorted((root / "hypotheses/proposals").glob("PROPOSAL_SET_*.md"))
    experiments = sorted((root / "experiments").glob("EXPERIMENT_*"))
    if experiments:
        hypothesis = (
            find_hypothesis(root, config.active.hypothesis) if config.active.hypothesis else None
        )
        return _active_experiment_guidance(root, config, experiments, hypothesis)

    if not references:
        return _guidance(
            "project_setup",
            "Project setup is complete.",
            [
                _action(
                    "add_references",
                    "Add and index relevant reference PDFs",
                    kind="prompt",
                    recommended=True,
                    prompt="Help me select and add a small set of relevant papers.",
                ),
                _action(
                    "review_question",
                    "Review the initial question and description",
                    kind="read",
                    read=["background/initial_question.md", "background/project_description.md"],
                ),
                _action(
                    "create_background_without_refs",
                    "Start a provisional background without references",
                    kind="command",
                    command="smairt background create",
                ),
            ],
        )
    if background.read_text(encoding="utf-8").strip() == "# Initial Background\n\nStatus: DRAFT":
        return _guidance(
            "references_indexed",
            f"{len(references)} reference(s) are indexed.",
            [
                _action(
                    "create_background",
                    "Create the initial-background workspace",
                    kind="command",
                    recommended=True,
                    command="smairt background create",
                ),
                _action(
                    "review_references",
                    "Review indexed reference metadata",
                    kind="read",
                    read=["references/index.yaml"],
                ),
            ],
        )
    if validate_background(root):
        return _guidance(
            "background_draft",
            "The initial-background workspace is ready.",
            [
                _action(
                    "complete_background",
                    "Synthesize the initial background from indexed references",
                    kind="prompt",
                    recommended=True,
                    read=["background/initial_background.md", "references/index.yaml"],
                    prompt=(
                        "Complete the initial background with reference IDs and page ranges; "
                        "separate evidence, inference, limitations, and gaps."
                    ),
                ),
                _action(
                    "review_background",
                    "Open and review the background draft",
                    kind="read",
                    read=["background/initial_background.md"],
                ),
            ],
        )
    if not proposals:
        return _guidance(
            "background_complete",
            "The initial background is complete.",
            [
                _action(
                    "create_proposals",
                    "Create a three-option hypothesis proposal set",
                    kind="command",
                    recommended=True,
                    command="smairt hypothesis proposals new",
                ),
                _action(
                    "review_background",
                    "Review the completed background first",
                    kind="read",
                    read=["background/initial_background.md"],
                ),
            ],
        )
    latest_proposal = proposals[-1]
    if validate_proposal_set(latest_proposal):
        return _guidance(
            "proposal_draft",
            f"{latest_proposal.name} is ready for development.",
            [
                _action(
                    "complete_proposals",
                    "Develop exactly three distinct hypothesis options",
                    kind="prompt",
                    recommended=True,
                    read=[str(latest_proposal), "background/initial_background.md"],
                    prompt=(
                        "Complete options A, B, and C with distinct reasoning, predictions, "
                        "alternatives, data, tests, feasibility, and confounders."
                    ),
                ),
                _action(
                    "review_proposal_template",
                    "Open the proposal set",
                    kind="read",
                    read=[str(latest_proposal)],
                ),
            ],
        )
    if not config.active.hypothesis:
        return _guidance(
            "proposal_complete",
            "Three hypothesis options are ready for review.",
            _proposal_choices(latest_proposal),
        )
    hypothesis = find_hypothesis(root, config.active.hypothesis)
    if validate_hypothesis(hypothesis):
        return _guidance(
            "hypothesis_selected",
            f"{config.active.hypothesis} was selected by the researcher.",
            [
                _action(
                    "complete_hypothesis",
                    "Complete the selected hypothesis before execution",
                    kind="prompt",
                    recommended=True,
                    read=[str(hypothesis)],
                    prompt=(
                        "Complete every required hypothesis section using the selected proposal "
                        "and preserve the human rationale."
                    ),
                ),
                _action(
                    "review_hypothesis",
                    "Read the selected hypothesis",
                    kind="read",
                    read=[str(hypothesis)],
                ),
            ],
        )
    if not experiments:
        return _guidance(
            "hypothesis_ready",
            f"{config.active.hypothesis} is complete and test-ready.",
            [
                _action(
                    "choose_experiment_route",
                    "Compare three experimental routes",
                    kind="human_choice",
                    recommended=True,
                    requires_human=True,
                    read=[str(hypothesis)],
                    prompt=(
                        "Offer three distinct experimental routes with rationale, tradeoffs, "
                        "required data, controls, and expected evidence."
                    ),
                ),
                _action(
                    "review_hypothesis",
                    "Read the hypothesis before choosing",
                    kind="read",
                    read=[str(hypothesis)],
                ),
            ],
        )
    return _active_experiment_guidance(root, config, experiments, hypothesis)


def _active_experiment_guidance(
    root: Path,
    config: SmairtConfig,
    experiments: list[Path],
    hypothesis: Path | None,
) -> dict[str, Any]:
    """Prioritize active experiment, run, and decision artifacts over setup suggestions."""
    if hypothesis and validate_hypothesis(hypothesis):
        return _guidance(
            "hypothesis_selected",
            f"{config.active.hypothesis} is linked to an experiment but is incomplete.",
            [
                _action(
                    "complete_hypothesis",
                    "Complete the linked hypothesis before execution",
                    kind="prompt",
                    recommended=True,
                    read=[str(hypothesis)],
                    prompt=(
                        "Complete every required hypothesis section before running the experiment."
                    ),
                ),
                _action(
                    "review_hypothesis",
                    "Read the linked hypothesis",
                    kind="read",
                    read=[str(hypothesis)],
                ),
            ],
        )
    active_experiment = _experiment(root, config.active.experiment) or experiments[-1]
    metadata = yaml.safe_load((active_experiment / "experiment.yaml").read_text()) or {}
    iteration_id = config.active.iteration or "ITERATION_001"
    iteration = active_experiment / "iterations" / iteration_id
    runs = (
        sorted((root / "results" / str(metadata["id"]) / iteration_id).glob("RUN_*"))
        if (root / "results" / str(metadata["id"]) / iteration_id).exists()
        else []
    )
    if not runs:
        return _guidance(
            "experiment_ready",
            f"{metadata['id']} / {iteration_id} is ready for implementation and review.",
            [
                _action(
                    "implement_experiment",
                    "Implement and review the experiment code",
                    kind="prompt",
                    recommended=True,
                    read=[
                        str(iteration.relative_to(root)),
                        *([str(hypothesis)] if hypothesis else []),
                    ],
                    prompt=(
                        "Implement the registered experiment entrypoint using SMAIRT code "
                        "conventions, then run code validation."
                    ),
                ),
                _action(
                    "review_code",
                    "Open the generated experiment skeleton",
                    kind="read",
                    read=[str(iteration.relative_to(root))],
                ),
                _action(
                    "validate_code",
                    "Validate code readability and traceability",
                    kind="command",
                    command="smairt code validate",
                ),
            ],
        )
    decisions = root / "analysis" / str(metadata["id"]) / "decisions.yaml"
    if not decisions.exists():
        latest_run = runs[-1]
        return _guidance(
            "run_complete",
            f"{latest_run.name} completed and its provenance bundle was recorded.",
            [
                _action(
                    "interpret_run",
                    "Interpret the run and prepare a human decision",
                    kind="prompt",
                    recommended=True,
                    read=[
                        str(latest_run.relative_to(root)),
                        str((root / "analysis" / str(metadata["id"])).relative_to(root)),
                    ],
                    prompt=(
                        "Separate observations, derived results, interpretation, limitations, "
                        "and confounders; then ask me to ACCEPT, REVISE, ABANDON, or mark BLOCKED."
                    ),
                ),
                _action(
                    "review_run",
                    "Inspect the run bundle",
                    kind="read",
                    read=[str(latest_run.relative_to(root))],
                ),
            ],
        )
    return _guidance(
        "decision_recorded",
        f"A research decision is recorded for {metadata['id']}.",
        [
            _action(
                "review_next_direction",
                "Review the decision and choose the next research direction",
                kind="human_choice",
                recommended=True,
                requires_human=True,
                read=[str(decisions.relative_to(root))],
            ),
            _action(
                "new_iteration",
                "Create a revised iteration",
                kind="command",
                command=f"smairt iteration new --experiment {metadata['id']} --from {iteration_id}",
            ),
            _action(
                "paper_evidence",
                "Review accepted evidence for the paper",
                kind="prompt",
                prompt=(
                    "Review accepted evidence and suggest whether any result belongs in the "
                    "paper manifest."
                ),
            ),
        ],
    )


def _experiment(root: Path, identifier: str | None) -> Path | None:
    """Resolve the currently active experiment when an identifier is available."""
    return next((root / "experiments").glob(f"{identifier}_*"), None) if identifier else None


def _guidance(stage: str, completed: str, actions: list[dict[str, Any]]) -> dict[str, Any]:
    """Package a completed stage and bounded adaptive action list for Codex."""
    return {
        "stage": stage,
        "completed": completed,
        "recommended": next(
            (item for item in actions if item["recommended"]), actions[0] if actions else None
        ),
        "actions": actions[:4],
    }
