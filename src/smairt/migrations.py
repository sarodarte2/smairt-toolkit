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
from smairt.references import load_index, render_index
from smairt.transactions import FileTransaction
from smairt.utils import ensure_no_symlink, sha256_file, sha256_text, validate_identifier


def detect_scaffold(root: Path) -> str:
    """Classify a project as original, versioned, mixed, or unknown."""
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
    if version in {3, 4, 5, 6, 7, 8}:
        return f"v{version}"
    return "v2" if version == 2 else "v1"


def migration_plan(root: Path) -> dict[str, object]:
    """Preview supported migration writes, backups, and blocking conflicts."""
    kind = detect_scaffold(root)
    conflicts = []
    if kind in {"unknown", "mixed", "original"}:
        conflicts.append(f"automatic migration is not safe for {kind} scaffold")
    applicable = kind in {"v1", "v2", "v3", "v4", "v5", "v6", "v7"} and not conflicts
    from_version = (
        1
        if kind == "v1"
        else 2
        if kind == "v2"
        else 3
        if kind == "v3"
        else 4
        if kind == "v4"
        else 5
        if kind == "v5"
        else 6
        if kind == "v6"
        else 7
    )
    to_version = min(from_version + 1, 8)
    migration_name = f"v{from_version}-to-v{to_version}-<id>.json"
    writes = ["smairt.yaml", f".smairt/migrations/{migration_name}"] if applicable else []
    if applicable and to_version == 4:
        writes.insert(1, "references/index.yaml")
    if applicable and to_version == 5:
        writes.append(".smairt/local/integrations.yaml")
    return {
        "detected": kind,
        "from_version": from_version,
        "to_version": to_version,
        "writes": writes,
        "moves": (
            [
                "Zotero library/account settings -> user-local profile",
                "provider profile bindings -> .smairt/local/integrations.yaml",
            ]
            if applicable and to_version == 5
            else []
        ),
        "backups": (
            ["smairt.yaml", "references/index.yaml"] if to_version == 4 else ["smairt.yaml"]
        )
        if writes
        else [],
        "conflicts": conflicts,
        "applicable": applicable,
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
    """Apply the next supported schema migration through a staged transaction."""
    plan = migration_plan(root)
    if not plan["applicable"]:
        conflicts = cast(list[str], plan["conflicts"])
        raise ValueError("migration cannot be applied: " + "; ".join(conflicts))
    if _dirty(root) and not allow_dirty:
        raise ValueError("migration requires a clean Git working tree")
    config_path = root / "smairt.yaml"
    before_hash = sha256_file(config_path)
    from_version = cast(int, plan["from_version"])
    to_version = cast(int, plan["to_version"])
    migration_id = f"v{from_version}-to-v{to_version}-{uuid4().hex}"
    backup_root = root / ".smairt/backups" / migration_id
    backup = backup_root / "smairt.yaml"
    path = root / ".smairt/migrations" / f"{migration_id}.json"
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    payload["schema_version"] = to_version
    if to_version == 3:
        project = payload.setdefault("project", {})
        project.setdefault("fields_of_study", [])
        project.setdefault("license", "unspecified")
    if to_version == 4:
        payload.setdefault("integrations", {})
    if to_version == 5:
        from smairt.local_setup import ConnectionProfile, bind_profile, configure_profile
        from smairt.models import ZoteroLibraryType, ZoteroMode

        integrations = payload.setdefault("integrations", {})
        openalex = integrations.setdefault("openalex", {})
        openalex_credential = openalex.pop("credential", {}) or {}
        openalex_profile = str(openalex_credential.get("profile") or "default")
        configure_profile(
            openalex_profile,
            ConnectionProfile(
                provider="openalex",
                credential_profile=openalex_profile,
                environment_variable=str(
                    openalex_credential.get("environment_variable") or "OPENALEX_API_KEY"
                ),
            ),
        )
        if bool(openalex.get("enabled")):
            bind_profile(root, "openalex", openalex_profile)
        zotero = integrations.setdefault("zotero", {})
        zotero_mode = ZoteroMode(str(zotero.pop("mode", "disabled")))
        zotero_credential = zotero.pop("credential", {}) or {}
        zotero_profile = str(zotero_credential.get("profile") or "default")
        library_id = zotero.pop("library_id", None)
        library_type = ZoteroLibraryType(str(zotero.pop("library_type", "user")))
        zotero["enabled"] = zotero_mode is not ZoteroMode.DISABLED
        if zotero_mode is not ZoteroMode.DISABLED:
            configure_profile(
                zotero_profile,
                ConnectionProfile(
                    provider="zotero",
                    credential_profile=zotero_profile,
                    environment_variable=str(
                        zotero_credential.get("environment_variable") or "ZOTERO_API_KEY"
                    ),
                    mode=zotero_mode,
                    library_id=str(library_id) if library_id else None,
                    library_type=library_type if zotero_mode is ZoteroMode.WEB else None,
                ),
            )
            bind_profile(root, "zotero", zotero_profile)
    config = SmairtConfig.model_validate(payload)
    applied_at = utc_now()
    config.migration_history.append(
        MigrationEntry(
            from_version=from_version,
            to_version=to_version,
            contributor_id=contributor_id,
            applied_at=applied_at,
        )
    )
    rendered = config.to_yaml()
    SmairtConfig.model_validate(yaml.safe_load(rendered))
    changes: dict[str, tuple[Path, bytes, str]] = {
        "smairt.yaml": (config_path, config_path.read_bytes(), rendered)
    }
    reference_path = root / "references/index.yaml"
    if to_version == 4:
        if not reference_path.is_file():
            raise ValueError("v3 to v4 migration requires references/index.yaml")
        records = load_index(root)
        changes["references/index.yaml"] = (
            reference_path,
            reference_path.read_bytes(),
            render_index(records),
        )
    file_records: dict[str, dict[str, object]] = {}
    for relative, (target, before, after) in changes.items():
        file_records[relative] = {
            "before_sha256": sha256_text(before.decode("utf-8")),
            "after_sha256": sha256_text(after),
            "before_mode": target.stat().st_mode & 0o777,
            "backup": str((backup_root / relative).relative_to(root)),
        }
    record = {
        "schema_version": 1,
        "id": migration_id,
        "status": "applied",
        "from_version": from_version,
        "to_version": to_version,
        "applied_at": applied_at,
        "before_sha256": before_hash,
        "after_sha256": sha256_text(rendered),
        "backup": str(backup.relative_to(root)),
        "backups": {
            relative: str((backup_root / relative).relative_to(root)) for relative in changes
        },
        "files": file_records,
        "git_before": git_state(root),
    }
    transaction = FileTransaction(root, "migration apply")
    for relative, (target, before, after) in changes.items():
        file_record = file_records[relative]
        backup_path = backup_root / relative
        transaction.stage_bytes(
            backup_path,
            before,
            mode=cast(int, file_record["before_mode"]),
        )
        transaction.stage_text(target, after, mode=cast(int, file_record["before_mode"]))
    transaction.stage_text(path, json.dumps(record, indent=2, sort_keys=True) + "\n")
    transaction.commit()
    return record


@mutating("migration rollback")
def rollback_migration(root: Path) -> dict[str, object]:
    """Restore the latest unchanged applied migration from its verified backup."""
    records: list[tuple[str, Path, dict[str, object]]] = []
    for candidate in (root / ".smairt/migrations").glob("v*-to-v*-*.json"):
        record = json.loads(candidate.read_text(encoding="utf-8"))
        identifier = str(record.get("id", ""))
        validate_identifier(identifier, label="migration ID")
        if candidate.stem != identifier:
            raise IntegrityError("migration record ID does not match its filename")
        records.append((str(record.get("applied_at", "")), candidate, record))
    if not records:
        raise ValueError("no applied migration found")
    _, path, record = max(records, key=lambda item: item[0])
    if record.get("status") != "applied":
        raise ValueError("latest migration is not in an applied state")
    files = record.get("files")
    if isinstance(files, dict):
        restores: list[tuple[Path, Path, int]] = []
        for relative, metadata in files.items():
            if not isinstance(relative, str) or not isinstance(metadata, dict):
                raise IntegrityError("migration file record is malformed")
            target = ensure_no_symlink(root, root / relative)
            backup_value = metadata.get("backup")
            before_hash = metadata.get("before_sha256")
            after_hash = metadata.get("after_sha256")
            before_mode = metadata.get("before_mode")
            if not all(
                isinstance(value, str) for value in (backup_value, before_hash, after_hash)
            ) or not isinstance(before_mode, int):
                raise IntegrityError("migration file hashes or mode are malformed")
            if not target.is_file() or sha256_file(target) != after_hash:
                raise ValueError(
                    f"migrated file changed after migration; rollback refused: {relative}"
                )
            backup_path = ensure_no_symlink(root, root / str(backup_value))
            if not backup_path.is_file() or sha256_file(backup_path) != before_hash:
                raise IntegrityError(f"migration backup failed integrity check: {relative}")
            restores.append((target, backup_path, before_mode))
        record.update(status="rolled_back", rolled_back_at=utc_now())
        transaction = FileTransaction(root, "migration rollback")
        for target, backup_path, before_mode in restores:
            transaction.stage_bytes(target, backup_path.read_bytes(), mode=before_mode)
        transaction.stage_text(path, json.dumps(record, indent=2, sort_keys=True) + "\n")
        transaction.commit()
        return {
            "rolled_back": True,
            "restored": [str(target.relative_to(root)) for target, _, _ in restores],
        }
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
    backups = record.get("backups")
    if isinstance(backups, dict):
        for relative, backup_value in backups.items():
            if (
                relative == "smairt.yaml"
                or not isinstance(relative, str)
                or not isinstance(backup_value, str)
            ):
                continue
            destination = ensure_no_symlink(root, root / relative)
            additional_backup = ensure_no_symlink(root, root / backup_value)
            if not additional_backup.is_file():
                raise IntegrityError("migration backup is missing or unsafe")
            transaction.stage_bytes(
                destination,
                additional_backup.read_bytes(),
                mode=additional_backup.stat().st_mode & 0o777,
            )
    transaction.stage_text(path, json.dumps(record, indent=2, sort_keys=True) + "\n")
    transaction.commit()
    return {"rolled_back": True, "restored_sha256": before_hash}
