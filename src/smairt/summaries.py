"""Immutable contributor-scoped source summaries with promotion and invalidation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from smairt.locking import mutating
from smairt.models import SmairtConfig, SummaryRecord, utc_now
from smairt.provenance import require_contributor, stage_event
from smairt.transactions import FileTransaction
from smairt.utils import ensure_no_symlink, sha256_file, slugify


def _source_path(root: Path, source: Path) -> tuple[Path, str]:
    """Resolve a regular source without following a project-local symlink."""
    root = root.resolve()
    requested = source if source.is_absolute() else root / source
    resolved = ensure_no_symlink(root, requested)
    if not resolved.is_file():
        raise ValueError("summary source must be a regular file")
    return resolved, str(resolved.relative_to(root))


@mutating("summary create")
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
    source, source_relative = _source_path(root, source)
    protected = config.data.classification.value in {"private", "controlled"}
    strict_protected = config.safety_mode == "strict" and protected
    if strict_protected and shareable != redaction_confirmed:
        raise ValueError("Strict mode tracking requires shareable and confirmed redaction")
    tracked = not strict_protected or (shareable and redaction_confirmed)
    digest = sha256_file(source)
    source_id = slugify(source_relative)
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
        "source_path": source_relative,
        "source_sha256": digest,
        "content": content,
        "shareable": shareable,
        "redaction_confirmed": redaction_confirmed,
        "tracked": tracked,
        "status": "current",
        "created_at": utc_now(),
    }
    record = SummaryRecord.model_validate(payload)
    transaction = FileTransaction(root, "summary create")
    transaction.stage_text(
        path, json.dumps(record.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    )
    stage_event(root, transaction, "summary.created", artifact_ids=[record.id])
    transaction.commit()
    return path


def list_summaries(root: Path) -> list[dict[str, Any]]:
    """List tracked and local summaries with current source freshness."""
    paths = [
        path
        for path in (root / "summaries").glob("*/*.json")
        if path.parent.name not in {"canonical", "supersessions"}
    ]
    paths += list((root / ".smairt/local/summaries").glob("*/*.json"))
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in sorted(paths):
        record = SummaryRecord.model_validate_json(path.read_text(encoding="utf-8"))
        if record.id in seen:
            raise ValueError(f"duplicate summary ID: {record.id}")
        seen.add(record.id)
        item = record.model_dump(mode="json")
        item["artifact_path"] = str(path.relative_to(root))
        try:
            source, _ = _source_path(root, Path(str(item["source_path"])))
        except ValueError:
            item["fresh"] = False
        else:
            item["fresh"] = sha256_file(source) == item["source_sha256"]
        items.append(item)
    return items


@mutating("summary promote")
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
    payload = {
        "summary_id": identifier,
        "source_id": summary["source_id"],
        "source_sha256": summary["source_sha256"],
        "promoted_by": contributor.id,
        "promoted_at": utc_now(),
    }
    transaction = FileTransaction(root, "summary promote")
    transaction.stage_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    stage_event(root, transaction, "summary.promoted", artifact_ids=[identifier])
    transaction.commit()
    return path


@mutating("summary supersede")
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
    if not replacement["tracked"]:
        raise ValueError("local protected summaries cannot become canonical replacements")
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
    transaction = FileTransaction(root, "summary supersede")
    transaction.stage_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    canonical = root / "summaries/canonical" / f"{previous['source_id']}.json"
    if canonical.exists() and json.loads(canonical.read_text()).get("summary_id") == previous_id:
        transaction.stage_text(
            canonical,
            json.dumps(
                {
                    "summary_id": replacement_id,
                    "source_id": replacement["source_id"],
                    "source_sha256": replacement["source_sha256"],
                    "promoted_by": contributor.id,
                    "promoted_at": utc_now(),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
        )
    stage_event(
        root,
        transaction,
        "summary.superseded",
        artifact_ids=[previous_id, replacement_id],
        supersedes=previous_id,
    )
    transaction.commit()
    return path
