"""Preview and apply safe updates to framework-managed project guidance."""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from smairt import __version__
from smairt.harnesses import select_harness, switch_plan
from smairt.models import SmairtConfig
from smairt.scaffold import CODE_CONVENTIONS, SKILL, SKILL_REFERENCE
from smairt.utils import atomic_write, sha256_text


def managed_files() -> dict[str, str]:
    """Return the authoritative framework-owned files for generated projects."""
    return {
        ".agents/skills/smairt-research/SKILL.md": SKILL,
        ".agents/skills/smairt-research/references/workflow.md": SKILL_REFERENCE,
        "prompts/CODE_CONVENTIONS.md": CODE_CONVENTIONS,
    }


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
    result: dict[str, Any] = {"version": __version__, "applied": apply, "changes": changes}
    config = SmairtConfig.load(root / "smairt.yaml")
    harness_plan = switch_plan(root, config.harness.active.value)
    result["harness"] = harness_plan
    if not apply:
        return result
    if harness_plan["modified_managed"] or harness_plan["conflicts"]:
        raise ValueError("harness-managed files must be reconciled before upgrade")

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    backup_root = root / ".smairt/backups" / timestamp
    for change in changes:
        relative = str(change["path"])
        target = root / relative
        if target.exists():
            backup = backup_root / relative
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backup)
        atomic_write(target, managed_files()[relative].rstrip() + "\n")
    hashes = {
        relative: sha256_text(content.rstrip() + "\n")
        for relative, content in managed_files().items()
    }
    manifest = {"framework_version": __version__, "managed_files": hashes}
    atomic_write(root / ".smairt/framework.yaml", yaml.safe_dump(manifest, sort_keys=False))
    select_harness(root, config.harness.active.value)
    result["backup"] = (
        str(backup_root.relative_to(root))
        if any(item["status"] == "update" for item in changes)
        else None
    )
    return result
