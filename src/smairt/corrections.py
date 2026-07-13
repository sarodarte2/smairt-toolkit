"""Versioned amendments, retractions, and run supersession records."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import yaml

from smairt.integrity import verify_run
from smairt.locking import mutating
from smairt.models import EvidenceCard, RunRecord, RunStatus, SmairtConfig, utc_now
from smairt.provenance import git_state, require_contributor, stage_event
from smairt.transactions import FileTransaction
from smairt.utils import sha256_file, validate_identifier


def _run_path(root: Path, run_id: str) -> Path:
    validate_identifier(run_id, label="run ID")
    matches = list((root / "results").glob(f"EXPERIMENT_*/ITERATION_*/{run_id}/run.json"))
    if len(matches) != 1:
        raise ValueError(f"missing or ambiguous run: {run_id}")
    return matches[0]


def _verified_replacement(root: Path, run_id: str) -> RunRecord:
    """Require a completed, internally consistent, integrity-locked replacement run."""
    path = _run_path(root, run_id)
    record = RunRecord.model_validate_json(path.read_text(encoding="utf-8"))
    if record.run_id != run_id:
        raise ValueError("replacement run record does not match its requested ID")
    if (record.experiment_id, record.iteration_id) != (path.parents[2].name, path.parents[1].name):
        raise ValueError("replacement run relationships do not match its result path")
    if record.status is not RunStatus.COMPLETED or record.exit_code != 0:
        raise ValueError("replacement run must be successfully completed")
    config = SmairtConfig.load(root / "smairt.yaml")
    if config.git.enabled and record.environment.get("git_capture_status") != "ok":
        raise ValueError("replacement run requires known Git provenance")
    if not verify_run(root, run_id)["ok"]:
        raise ValueError("replacement run failed integrity verification")
    return record


@mutating("run correction")
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
        if replacement_run == target_run:
            raise ValueError("replacement run must differ from target run")
        _verified_replacement(root, replacement_run)
    correction_id = f"correction-{uuid4().hex}"
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
    transaction = FileTransaction(root, f"run {action}")
    transaction.stage_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    corrected_status = {"retract": "RETRACTED", "supersede": "SUPERSEDED"}[action]
    for selection in (root / "analysis").glob("*/selection.yaml"):
        selected = yaml.safe_load(selection.read_text()) or {}
        if selected.get("run_id") == target_run and selected.get("status") == "ACCEPTED":
            selected.update(
                status=corrected_status, status_reason=reason, replacement_run=replacement_run
            )
            transaction.stage_text(selection, yaml.safe_dump(selected, sort_keys=False))
    config = SmairtConfig.load(root / "smairt.yaml")
    if config.active.accepted_run == target_run:
        config.active.accepted_run = None
        transaction.stage_text(
            root / "smairt.yaml",
            yaml.safe_dump(config.model_dump(mode="json", exclude_none=True), sort_keys=False),
        )
    for evidence in (root / "paper/evidence").glob("*.json"):
        card = EvidenceCard.model_validate_json(evidence.read_text(encoding="utf-8"))
        if card.run_id == target_run and card.status.value == "current":
            updated_data = card.model_dump(mode="json")
            updated_data.update(
                status={"retract": "retracted", "supersede": "superseded"}[action],
                replacement_run=replacement_run,
                correction_id=correction_id,
            )
            updated = EvidenceCard.model_validate(updated_data)
            transaction.stage_text(
                evidence, json.dumps(updated.model_dump(mode="json"), indent=2) + "\n"
            )
    stage_event(
        root,
        transaction,
        f"run.{action}ed",
        artifact_ids=[target_run],
        supersedes=target_run if action == "supersede" else None,
        details={"replacement_run": replacement_run, "reason": reason},
    )
    transaction.commit()
    return path


@mutating("artifact amend")
def amend_artifact(
    root: Path, target: Path, field: str, previous: str, corrected: str, reason: str
) -> Path:
    """Append a contributor-attributed correction without mutating its target."""
    contributor = require_contributor(root)
    target = target.resolve()
    target.relative_to(root.resolve())
    identifier = f"amendment-{uuid4().hex}"
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
    transaction = FileTransaction(root, "artifact amend")
    transaction.stage_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    stage_event(
        root,
        transaction,
        "artifact.amended",
        artifact_ids=[str(target.relative_to(root))],
        details={"amendment": identifier, "reason": reason},
    )
    transaction.commit()
    return path
