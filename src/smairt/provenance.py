"""Contributor registry and append-only project event provenance."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any
from uuid import uuid4

from smairt.locking import mutating
from smairt.models import Contributor, ProjectEvent, SmairtConfig, utc_now
from smairt.transactions import FileTransaction
from smairt.utils import atomic_write, ensure_no_symlink, sha256_file, slugify


def git_state(root: Path) -> dict[str, Any]:
    """Capture current Git commit and working-tree cleanliness."""
    if not (root / ".git").exists():
        return {"commit": None, "dirty": False}
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True)
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True
    )
    return {
        "commit": commit.stdout.strip() if commit.returncode == 0 else None,
        "dirty": bool(status.stdout.strip()),
    }


@mutating("contributor add")
def add_contributor(
    root: Path, name: str, email: str | None = None, *, source: str = "manual"
) -> Contributor:
    """Register an explicitly supplied contributor identity."""
    config = SmairtConfig.load(root / "smairt.yaml")
    identifier = slugify(name)
    if any(item.id == identifier for item in config.contributors):
        raise ValueError(f"contributor already exists: {identifier}")
    contributor = Contributor(id=identifier, name=name, email=email, source=source)
    config.contributors.append(contributor)
    config.dump(root / "smairt.yaml")
    return contributor


@mutating("contributor use")
def use_contributor(root: Path, identifier: str) -> Contributor:
    """Select a registered contributor for consequential project actions."""
    config = SmairtConfig.load(root / "smairt.yaml")
    contributor = next((item for item in config.contributors if item.id == identifier), None)
    if contributor is None:
        raise ValueError(f"unknown contributor: {identifier}")
    config.active_contributor = identifier
    config.dump(root / "smairt.yaml")
    return contributor


def require_contributor(root: Path) -> Contributor:
    """Return the confirmed active contributor or reject the action."""
    config = SmairtConfig.load(root / "smairt.yaml")
    contributor = next((c for c in config.contributors if c.id == config.active_contributor), None)
    if contributor is None:
        raise ValueError("confirm and select an active contributor first")
    return contributor


@mutating("event record")
def record_event(
    root: Path,
    action: str,
    *,
    artifact_ids: list[str] | None = None,
    hashes: dict[str, str] | None = None,
    supersedes: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Atomically append a validated event and refresh readable project history."""
    transaction = FileTransaction(root, f"event {action}")
    payload = stage_event(
        root,
        transaction,
        action,
        artifact_ids=artifact_ids,
        hashes=hashes,
        supersedes=supersedes,
        details=details,
    )
    transaction.commit()
    return payload


def stage_event(
    root: Path,
    transaction: FileTransaction,
    action: str,
    *,
    artifact_ids: list[str] | None = None,
    hashes: dict[str, str] | None = None,
    supersedes: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Stage one event and its derived history in an existing state transaction."""
    actor = require_contributor(root)
    events = root / ".smairt/events" / actor.id
    event_id = f"event-{uuid4().hex}"
    event = ProjectEvent.model_validate(
        {
            "schema_version": 1,
            "id": event_id,
            "timestamp": utc_now(),
            "actor": actor.id,
            "action": action,
            "artifact_ids": artifact_ids or [],
            "hashes": hashes or {},
            "git": git_state(root),
            "supersedes": supersedes,
            "details": details or {},
        }
    )
    payload = event.model_dump(mode="json")
    history = _history_content([*load_events(root), payload])
    transaction.stage_text(
        events / f"{event_id}.json", json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )
    transaction.stage_text(root / "docs/PROJECT_HISTORY.md", history)
    return payload


def load_events(root: Path) -> list[dict[str, Any]]:
    """Load validated event streams, rejecting corruption and duplicate IDs."""
    events: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in sorted((root / ".smairt/events").glob("*/*.json")):
        event = ProjectEvent.model_validate_json(path.read_text(encoding="utf-8"))
        if event.id in seen:
            raise ValueError(f"duplicate event ID: {event.id}")
        seen.add(event.id)
        events.append(event.model_dump(mode="json"))
    return sorted(events, key=lambda item: str(item["timestamp"]))


def _history_content(events: list[dict[str, Any]]) -> str:
    """Render validated events into the deterministic human-readable history."""
    lines = ["# Project History", "", "Generated from immutable contributor-scoped events.", ""]
    for event in sorted(events, key=lambda item: str(item["timestamp"])):
        artifacts = ", ".join(event["artifact_ids"]) or "none"
        lines += [
            f"## {event['timestamp']} — {event['action']}",
            "",
            f"- Contributor: `{event['actor']}`",
            f"- Artifacts: {artifacts}",
            f"- Git commit: `{event['git'].get('commit') or 'none'}`",
            f"- Working tree dirty: `{event['git'].get('dirty', False)}`",
            "",
        ]
    return "\n".join(lines)


@mutating("history generate")
def generate_history(root: Path) -> Path:
    """Regenerate the readable project history from machine event records."""
    path = root / "docs/PROJECT_HISTORY.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(path, _history_content(load_events(root)))
    return path


def artifact_hashes(root: Path, paths: list[Path]) -> dict[str, str]:
    """Return checksums only for regular, root-contained, non-symlink artifacts."""
    hashes: dict[str, str] = {}
    for requested in paths:
        path = ensure_no_symlink(root, requested)
        if path.is_file():
            hashes[str(path.relative_to(root.resolve()))] = sha256_file(path)
    return hashes
