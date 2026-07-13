"""Immutable contributor-scoped source summaries with promotion and invalidation."""

from __future__ import annotations

import json
from pathlib import Path

from smairt.models import SmairtConfig, utc_now
from smairt.provenance import record_event, require_contributor
from smairt.utils import sha256_file, slugify, write_json


def create_summary(
    root: Path,
    source: Path,
    content: str,
    *,
    shareable: bool = False,
    redaction_confirmed: bool = False,
) -> Path:
    """Create an immutable summary keyed by contributor, source, and source hash."""
    contributor = require_contributor(root)
    config = SmairtConfig.load(root / "smairt.yaml")
    source = source.resolve()
    source.relative_to(root.resolve())
    protected = config.data.classification.value in {"private", "controlled"}
    strict_protected = config.safety_mode == "strict" and protected
    if strict_protected and shareable != redaction_confirmed:
        raise ValueError("Strict mode tracking requires shareable and confirmed redaction")
    tracked = not strict_protected or (shareable and redaction_confirmed)
    digest = sha256_file(source)
    source_id = slugify(str(source.relative_to(root)))
    directory = root / ("summaries" if tracked else ".smairt/local/summaries") / contributor.id
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{source_id}-{digest[:12]}.json"
    if path.exists():
        raise ValueError("summary already exists for contributor and source hash")
    payload = {
        "schema_version": 1,
        "id": path.stem,
        "contributor": contributor.id,
        "source_id": source_id,
        "source_path": str(source.relative_to(root)),
        "source_sha256": digest,
        "content": content,
        "shareable": shareable,
        "redaction_confirmed": redaction_confirmed,
        "tracked": tracked,
        "status": "current",
        "created_at": utc_now(),
    }
    write_json(path, payload)
    record_event(root, "summary.created", artifact_ids=[payload["id"]])
    return path


def list_summaries(root: Path) -> list[dict[str, object]]:
    """List tracked and local summaries with current source freshness."""
    paths = [
        path
        for path in (root / "summaries").glob("*/*.json")
        if path.parent.name not in {"canonical", "supersessions"}
    ]
    paths += list((root / ".smairt/local/summaries").glob("*/*.json"))
    items = []
    for path in sorted(paths):
        item = json.loads(path.read_text())
        item["artifact_path"] = str(path.relative_to(root))
        source = root / item["source_path"]
        item["fresh"] = source.exists() and sha256_file(source) == item["source_sha256"]
        items.append(item)
    return items


def promote_summary(root: Path, identifier: str) -> Path:
    """Promote one fresh tracked contributor summary as canonical context."""
    contributor = require_contributor(root)
    summary = next((item for item in list_summaries(root) if item["id"] == identifier), None)
    if summary is None:
        raise ValueError(f"unknown summary: {identifier}")
    if not summary["fresh"]:
        raise ValueError("stale summaries cannot be promoted")
    if not summary["tracked"]:
        raise ValueError("local protected summaries cannot be promoted")
    path = root / "summaries/canonical" / f"{summary['source_id']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "summary_id": identifier,
        "source_id": summary["source_id"],
        "source_sha256": summary["source_sha256"],
        "promoted_by": contributor.id,
        "promoted_at": utc_now(),
    }
    write_json(path, payload)
    record_event(root, "summary.promoted", artifact_ids=[identifier])
    return path


def supersede_summary(root: Path, previous_id: str, replacement_id: str) -> Path:
    """Link an older contributor summary to a fresh replacement without rewriting either."""
    contributor = require_contributor(root)
    items = {str(item["id"]): item for item in list_summaries(root)}
    if previous_id not in items or replacement_id not in items:
        raise ValueError("both previous and replacement summaries must exist")
    previous = items[previous_id]
    replacement = items[replacement_id]
    if previous["source_id"] != replacement["source_id"]:
        raise ValueError("summary supersession requires the same source")
    if not replacement["fresh"]:
        raise ValueError("replacement summary is stale")
    path = root / "summaries/supersessions" / f"{previous_id}.json"
    if path.exists():
        raise ValueError("summary is already superseded")
    payload = {
        "previous_summary_id": previous_id,
        "replacement_summary_id": replacement_id,
        "source_id": previous["source_id"],
        "superseded_by": contributor.id,
        "superseded_at": utc_now(),
    }
    write_json(path, payload)
    canonical = root / "summaries/canonical" / f"{previous['source_id']}.json"
    if canonical.exists() and json.loads(canonical.read_text()).get("summary_id") == previous_id:
        promote_summary(root, replacement_id)
    record_event(
        root,
        "summary.superseded",
        artifact_ids=[previous_id, replacement_id],
        supersedes=previous_id,
    )
    return path
