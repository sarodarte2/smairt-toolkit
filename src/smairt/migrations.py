"""Conservative schema migration planning, application, and rollback."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import yaml

from smairt.models import MigrationEntry, SmairtConfig
from smairt.utils import sha256_file


def detect_scaffold(root: Path) -> str:
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
    kind = detect_scaffold(root)
    conflicts = []
    if kind in {"unknown", "mixed", "original"}:
        conflicts.append(f"automatic migration is not safe for {kind} scaffold")
    writes = ["smairt.yaml", ".smairt/migrations/v1-to-v2.json"] if kind == "v1" else []
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
    result = subprocess.run(
        ["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, check=False
    )
    return result.returncode == 0 and bool(result.stdout.strip())


def apply_migration(
    root: Path, contributor_id: str | None = None, *, allow_dirty: bool = False
) -> dict[str, object]:
    plan = migration_plan(root)
    if not plan["applicable"]:
        raise ValueError("migration cannot be applied: " + "; ".join(plan["conflicts"]))
    if _dirty(root) and not allow_dirty:
        raise ValueError("migration requires a clean Git working tree")
    config_path = root / "smairt.yaml"
    before_hash = sha256_file(config_path)
    backup = root / ".smairt/backups/migration-v1/smairt.yaml"
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(config_path, backup)
    config = SmairtConfig.load(config_path)
    config.schema_version = 2
    config.migration_history.append(
        MigrationEntry(from_version=1, to_version=2, contributor_id=contributor_id)
    )
    config.dump(config_path)
    record = {
        "from_version": 1,
        "to_version": 2,
        "before_sha256": before_hash,
        "after_sha256": sha256_file(config_path),
        "backup": str(backup.relative_to(root)),
    }
    path = root / ".smairt/migrations/v1-to-v2.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2) + "\n")
    return record


def rollback_migration(root: Path) -> dict[str, object]:
    path = root / ".smairt/migrations/v1-to-v2.json"
    if not path.exists():
        raise ValueError("no applied v1-to-v2 migration found")
    record = json.loads(path.read_text())
    config_path = root / "smairt.yaml"
    if sha256_file(config_path) != record["after_sha256"]:
        raise ValueError("migrated files changed after migration; rollback refused")
    shutil.copy2(root / record["backup"], config_path)
    return {"rolled_back": True, "restored_sha256": sha256_file(config_path)}
