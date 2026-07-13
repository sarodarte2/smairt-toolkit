"""Conservative schema migration planning, application, and rollback."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import cast
from uuid import uuid4

import yaml

from smairt.errors import ExternalServiceError, IntegrityError
from smairt.locking import mutating
from smairt.models import MigrationEntry, SmairtConfig, utc_now
from smairt.provenance import git_state
from smairt.transactions import FileTransaction
from smairt.utils import ensure_no_symlink, sha256_file, sha256_text, validate_identifier


def detect_scaffold(root: Path) -> str:
    """Classify a project as original, v1, v2, mixed, or unknown."""
    config_path = root / "smairt.yaml"
    legacy = (root / "cookiecutter.json").exists() or (
        root / "prompts/00_priming_prompts.md"
    ).exists()
    if not config_path.exists():
        return "original" if legacy else "unknown"
    payload = yaml.safe_load(config_path.read_text()) or {}
    version = int(payload.get("schema_version", 1))
    if legacy and version >= 2:
        return "mixed"
    return "v2" if version >= 2 else "v1"


def migration_plan(root: Path) -> dict[str, object]:
    """Preview supported migration writes, backups, and blocking conflicts."""
    kind = detect_scaffold(root)
    conflicts = []
    if kind in {"unknown", "mixed", "original"}:
        conflicts.append(f"automatic migration is not safe for {kind} scaffold")
    writes = ["smairt.yaml", ".smairt/migrations/v1-to-v2-<id>.json"] if kind == "v1" else []
    return {
        "detected": kind,
        "from_version": 1 if kind == "v1" else 2,
        "to_version": 2,
        "writes": writes,
        "moves": [],
        "backups": ["smairt.yaml"] if writes else [],
        "conflicts": conflicts,
        "applicable": kind == "v1" and not conflicts,
    }


def _dirty(root: Path) -> bool:
    """Return Git dirtiness without treating an unhealthy repository as clean."""
    if not (root / ".git").exists():
        return False
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise ExternalServiceError("Git could not inspect the migration working tree") from exc
    if result.returncode != 0:
        raise ExternalServiceError("Git could not verify a clean migration working tree")
    return bool(result.stdout.strip())


@mutating("migration apply")
def apply_migration(
    root: Path, contributor_id: str | None = None, *, allow_dirty: bool = False
) -> dict[str, object]:
    """Apply the supported v1-to-v2 migration through a staged transaction."""
    plan = migration_plan(root)
    if not plan["applicable"]:
        conflicts = cast(list[str], plan["conflicts"])
        raise ValueError("migration cannot be applied: " + "; ".join(conflicts))
    if _dirty(root) and not allow_dirty:
        raise ValueError("migration requires a clean Git working tree")
    config_path = root / "smairt.yaml"
    before_hash = sha256_file(config_path)
    migration_id = f"v1-to-v2-{uuid4().hex}"
    backup = root / ".smairt/backups" / migration_id / "smairt.yaml"
    path = root / ".smairt/migrations" / f"{migration_id}.json"
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    payload["schema_version"] = 2
    config = SmairtConfig.model_validate(payload)
    applied_at = utc_now()
    config.migration_history.append(
        MigrationEntry(
            from_version=1,
            to_version=2,
            contributor_id=contributor_id,
            applied_at=applied_at,
        )
    )
    rendered = yaml.safe_dump(config.model_dump(mode="json", exclude_none=True), sort_keys=False)
    SmairtConfig.model_validate(yaml.safe_load(rendered))
    record = {
        "schema_version": 1,
        "id": migration_id,
        "status": "applied",
        "from_version": 1,
        "to_version": 2,
        "applied_at": applied_at,
        "before_sha256": before_hash,
        "after_sha256": sha256_text(rendered),
        "backup": str(backup.relative_to(root)),
        "git_before": git_state(root),
    }
    transaction = FileTransaction(root, "migration apply")
    transaction.stage_bytes(
        backup, config_path.read_bytes(), mode=config_path.stat().st_mode & 0o777
    )
    transaction.stage_text(config_path, rendered)
    transaction.stage_text(path, json.dumps(record, indent=2, sort_keys=True) + "\n")
    transaction.commit()
    return record


@mutating("migration rollback")
def rollback_migration(root: Path) -> dict[str, object]:
    """Restore the latest unchanged applied migration from its verified backup."""
    records: list[tuple[str, Path, dict[str, object]]] = []
    for candidate in (root / ".smairt/migrations").glob("v1-to-v2-*.json"):
        record = json.loads(candidate.read_text(encoding="utf-8"))
        identifier = str(record.get("id", ""))
        validate_identifier(identifier, label="migration ID")
        if candidate.stem != identifier:
            raise IntegrityError("migration record ID does not match its filename")
        records.append((str(record.get("applied_at", "")), candidate, record))
    if not records:
        raise ValueError("no applied v1-to-v2 migration found")
    _, path, record = max(records, key=lambda item: item[0])
    if record.get("status") != "applied":
        raise ValueError("latest migration is not in an applied state")
    config_path = root / "smairt.yaml"
    if sha256_file(config_path) != str(record.get("after_sha256", "")):
        raise ValueError("migrated files changed after migration; rollback refused")
    backup_value = record.get("backup")
    if not isinstance(backup_value, str):
        raise IntegrityError("migration backup path is missing")
    backup = ensure_no_symlink(root, root / backup_value)
    if not backup.is_file():
        raise IntegrityError("migration backup is missing or unsafe")
    before_hash = str(record.get("before_sha256", ""))
    if sha256_file(backup) != before_hash:
        raise IntegrityError("migration backup failed its integrity check")
    restored = backup.read_bytes()
    record.update(
        status="rolled_back",
        rolled_back_at=utc_now(),
        rolled_back_sha256=before_hash,
    )
    transaction = FileTransaction(root, "migration rollback")
    transaction.stage_bytes(config_path, restored, mode=backup.stat().st_mode & 0o777)
    transaction.stage_text(path, json.dumps(record, indent=2, sort_keys=True) + "\n")
    transaction.commit()
    return {"rolled_back": True, "restored_sha256": before_hash}
