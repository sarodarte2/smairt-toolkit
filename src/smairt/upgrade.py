"""Preview and apply safe updates to framework-managed project guidance."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from smairt import __version__
from smairt.harnesses import _stage_harness_selection, switch_plan
from smairt.locking import mutating
from smairt.models import SmairtConfig
from smairt.scaffold import CODE_CONVENTIONS, SKILL_FILES
from smairt.transactions import FileTransaction
from smairt.utils import sha256_text

LEGACY_SKILL_FILES = (
    ".agents/skills/smairt-research/SKILL.md",
    ".agents/skills/smairt-research/agents/openai.yaml",
    ".agents/skills/smairt-research/references/workflow.md",
)


def managed_files() -> dict[str, str]:
    """Return the authoritative framework-owned files for generated projects."""
    return {
        **SKILL_FILES,
        "prompts/CODE_CONVENTIONS.md": CODE_CONVENTIONS,
    }


def _legacy_skill_changes(root: Path) -> tuple[list[dict[str, str]], list[str]]:
    """Identify unchanged legacy skill files that can be removed without losing edits."""
    manifest_path = root / ".smairt/framework.yaml"
    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        manifest = {}
    prior = manifest.get("managed_files", {}) if isinstance(manifest, dict) else {}
    changes: list[dict[str, str]] = []
    preserved: list[str] = []
    for relative in LEGACY_SKILL_FILES:
        path = root / relative
        if not path.exists():
            continue
        expected = prior.get(relative) if isinstance(prior, dict) else None
        if isinstance(expected, str) and sha256_text(path.read_text(encoding="utf-8")) == expected:
            changes.append({"path": relative, "status": "remove"})
        else:
            preserved.append(relative)
    return changes, preserved


@mutating("project upgrade")
def upgrade_project(root: Path, *, apply: bool = False) -> dict[str, Any]:
    """Preview or apply managed-file changes while backing up every replacement."""
    changes = []
    for relative, desired in managed_files().items():
        normalized = desired.rstrip() + "\n"
        path = root / relative
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != normalized:
            changes.append(
                {"path": relative, "status": "update" if current is not None else "create"}
            )
    legacy_changes, legacy_preserved = _legacy_skill_changes(root)
    changes.extend(legacy_changes)
    result: dict[str, Any] = {
        "version": __version__,
        "applied": apply,
        "changes": changes,
        "legacy_preserved": legacy_preserved,
    }
    config = SmairtConfig.load(root / "smairt.yaml")
    harness_plan = switch_plan(root, config.harness.active.value)
    result["harness"] = harness_plan
    if not apply:
        return result
    if harness_plan["modified_managed"] or harness_plan["conflicts"]:
        raise ValueError("harness-managed files must be reconciled before upgrade")

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    backup_root = root / ".smairt/backups" / timestamp
    transaction = FileTransaction(root, "project upgrade")
    for change in changes:
        relative = str(change["path"])
        target = root / relative
        if target.exists():
            backup = backup_root / relative
            transaction.stage_bytes(backup, target.read_bytes(), mode=target.stat().st_mode & 0o777)
        if change["status"] == "remove":
            transaction.stage_delete(target)
        else:
            transaction.stage_text(target, managed_files()[relative].rstrip() + "\n")
    hashes = {
        relative: sha256_text(content.rstrip() + "\n")
        for relative, content in managed_files().items()
    }
    manifest = {"framework_version": __version__, "managed_files": hashes}
    transaction.stage_text(
        root / ".smairt/framework.yaml", yaml.safe_dump(manifest, sort_keys=False)
    )
    _stage_harness_selection(root, config.harness.active, harness_plan, transaction)
    transaction.commit()
    result["backup"] = (
        str(backup_root.relative_to(root))
        if any(item["status"] in {"update", "remove"} for item in changes)
        else None
    )
    return result
