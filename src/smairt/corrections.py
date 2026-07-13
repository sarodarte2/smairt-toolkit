"""Versioned amendments, retractions, and run supersession records."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from smairt.models import SmairtConfig, utc_now
from smairt.provenance import git_state, record_event, require_contributor
from smairt.utils import sha256_file


def _run_path(root: Path, run_id: str) -> Path:
    matches = list((root / "results").glob(f"EXPERIMENT_*/ITERATION_*/{run_id}/run.json"))
    if len(matches) != 1:
        raise ValueError(f"missing or ambiguous run: {run_id}")
    return matches[0]


def correct_run(
    root: Path,
    action: str,
    target_run: str,
    reason: str,
    replacement_run: str | None = None,
) -> Path:
    """Append a correction and invalidate dependent active evidence."""
    if action not in {"retract", "supersede"}:
        raise ValueError("action must be retract or supersede")
    contributor = require_contributor(root)
    target = _run_path(root, target_run)
    if action == "supersede":
        if not replacement_run:
            raise ValueError("supersession requires a replacement run")
        _run_path(root, replacement_run)
        if replacement_run == target_run:
            raise ValueError("replacement run must differ from target run")
    correction_id = f"correction-{utc_now().replace(':', '').replace('+', '_')}"
    payload = {
        "schema_version": 1,
        "id": correction_id,
        "action": action,
        "target_run": target_run,
        "replacement_run": replacement_run,
        "reason": reason,
        "contributor": contributor.id,
        "timestamp": utc_now(),
        "git": git_state(root),
        "target_sha256": sha256_file(target),
    }
    path = root / ".smairt/corrections" / contributor.id / f"{correction_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")
    for selection in (root / "analysis").glob("*/selection.yaml"):
        selected = yaml.safe_load(selection.read_text()) or {}
        if selected.get("run_id") == target_run and selected.get("status") == "ACCEPTED":
            selected.update(
                status=action.upper() + "D", status_reason=reason, replacement_run=replacement_run
            )
            selection.write_text(yaml.safe_dump(selected, sort_keys=False))
    config = SmairtConfig.load(root / "smairt.yaml")
    if config.active.accepted_run == target_run:
        config.active.accepted_run = None
        config.dump(root / "smairt.yaml")
    for evidence in (root / "paper/evidence").glob("*.json"):
        card = json.loads(evidence.read_text())
        if card.get("run_id") == target_run and card.get("status") == "current":
            card.update(
                status={"retract": "retracted", "supersede": "superseded"}[action],
                replacement_run=replacement_run,
                correction_id=correction_id,
            )
            evidence.write_text(json.dumps(card, indent=2) + "\n")
    record_event(
        root,
        f"run.{action}ed",
        artifact_ids=[target_run],
        supersedes=target_run if action == "supersede" else None,
        details={"replacement_run": replacement_run, "reason": reason},
    )
    return path


def amend_artifact(
    root: Path, target: Path, field: str, previous: str, corrected: str, reason: str
) -> Path:
    contributor = require_contributor(root)
    target = target.resolve()
    target.relative_to(root.resolve())
    identifier = f"amendment-{utc_now().replace(':', '').replace('+', '_')}"
    payload = {
        "schema_version": 1,
        "id": identifier,
        "action": "amend",
        "target": str(target.relative_to(root)),
        "target_sha256": sha256_file(target),
        "field": field,
        "previous": previous,
        "corrected": corrected,
        "reason": reason,
        "contributor": contributor.id,
        "timestamp": utc_now(),
        "git": git_state(root),
    }
    path = root / ".smairt/corrections" / contributor.id / f"{identifier}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")
    record_event(
        root,
        "artifact.amended",
        artifact_ids=[str(target.relative_to(root))],
        details={"amendment": identifier, "reason": reason},
    )
    return path
