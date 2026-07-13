"""Provider-neutral model capability tiers for economical harness use."""

from __future__ import annotations

from pathlib import Path

from smairt.models import SmairtConfig

TASK_TIERS = {
    "metadata": "cheap",
    "validation": "cheap",
    "summary": "cheap",
    "run": "cheap",
    "code": "balanced",
    "planning": "strong",
    "interpretation": "strong",
    "paper": "strong",
}

TIER_PURPOSE = {
    "cheap": "Mechanical normalization, summarization, formatting, and deterministic checks.",
    "balanced": "Routine implementation and bounded code changes with normal verification.",
    "strong": "Scientific reasoning, ambiguous planning, difficult debugging, and synthesis.",
}


def recommend_model(root: Path, task: str) -> dict[str, object]:
    """Return a harness-specific recommendation without storing provider credentials."""
    if task not in TASK_TIERS:
        raise ValueError(f"unknown task {task!r}; choose {', '.join(TASK_TIERS)}")
    config = SmairtConfig.load(root / "smairt.yaml")
    tier = TASK_TIERS[task]
    harness = config.harness.active.value
    actions = {
        "codex": "Choose an available Codex model and reasoning effort matching this tier.",
        "zoo": "Bind this tier to a Zoo API profile for the active mode in the Prompts tab.",
        "cline": "Use the matching Cline Plan/Act model or CLI --config profile.",
    }
    return {
        "task": task,
        "tier": tier,
        "purpose": TIER_PURPOSE[tier],
        "harness": harness,
        "action": actions[harness],
        "credentials_stored": False,
    }
