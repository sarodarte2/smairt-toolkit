"""Contributor registry and append-only project event provenance."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any
from uuid import uuid4

from smairt.models import Contributor, SmairtConfig, utc_now
from smairt.utils import atomic_write, sha256_file, slugify


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


def record_event(
    root: Path,
    action: str,
    *,
    artifact_ids: list[str] | None = None,
    hashes: dict[str, str] | None = None,
    supersedes: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append an immutable contributor-scoped event and refresh project history."""
    actor = require_contributor(root)
    stamp = utc_now()
    events = root / ".smairt/events" / actor.id
    events.mkdir(parents=True, exist_ok=True)
    event_id = f"event-{uuid4().hex}"
    payload = {
        "schema_version": 1,
        "id": event_id,
        "timestamp": stamp,
        "actor": actor.id,
        "action": action,
        "artifact_ids": artifact_ids or [],
        "hashes": hashes or {},
        "git": git_state(root),
        "supersedes": supersedes,
        "details": details or {},
    }
    atomic_write(events / f"{event_id}.json", json.dumps(payload, indent=2) + "\n")
    generate_history(root)
    return payload


def load_events(root: Path) -> list[dict[str, Any]]:
    """Load all contributor event streams in timestamp order."""
    return sorted(
        (json.loads(p.read_text()) for p in (root / ".smairt/events").glob("*/*.json")),
        key=lambda item: item["timestamp"],
    )


def generate_history(root: Path) -> Path:
    """Regenerate the readable project history from machine event records."""
    path = root / "docs/PROJECT_HISTORY.md"
    lines = ["# Project History", "", "Generated from immutable contributor-scoped events.", ""]
    for event in load_events(root):
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
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(path, "\n".join(lines))
    return path


def artifact_hashes(root: Path, paths: list[Path]) -> dict[str, str]:
    """Return root-relative checksums for existing artifact paths."""
    return {str(path.relative_to(root)): sha256_file(path) for path in paths if path.is_file()}
