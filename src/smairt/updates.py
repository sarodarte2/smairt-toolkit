"""Unified preview and application of safe project maintenance updates."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from smairt import __version__
from smairt.harnesses import ADAPTER_VERSION, install_harness, list_harnesses
from smairt.migrations import apply_migration, detect_scaffold, migration_plan
from smairt.models import SmairtConfig
from smairt.upgrade import upgrade_project

CURRENT_PROJECT_SCHEMA = 8


def project_update_plan(root: Path) -> dict[str, Any]:
    """Describe schema, guidance, and adapter work without changing the project."""
    root = root.resolve()
    config = SmairtConfig.load(root / "smairt.yaml")
    scaffold = detect_scaffold(root)
    schema_steps = (
        [
            {"from_version": version, "to_version": version + 1}
            for version in range(config.schema_version, CURRENT_PROJECT_SCHEMA)
        ]
        if config.schema_version < CURRENT_PROJECT_SCHEMA
        else []
    )
    guidance = upgrade_project(root, apply=False)
    harness = next(item for item in list_harnesses(root) if item["active"])
    manifest_version = harness.get("adapter_version")
    adapter_reasons: list[str] = []
    if config.harness.adapter_version != ADAPTER_VERSION:
        adapter_reasons.append(
            "project records adapter "
            f"{config.harness.adapter_version}; current is {ADAPTER_VERSION}"
        )
    if manifest_version != ADAPTER_VERSION:
        adapter_reasons.append(
            f"installed manifest is {manifest_version or 'missing'}; current is {ADAPTER_VERSION}"
        )
    for key in ("missing", "modified", "non_executable", "schema_errors"):
        if harness.get(key):
            count = len(cast(list[object], harness[key]))
            adapter_reasons.append(f"{key.replace('_', ' ')}: {count}")
    if harness.get("manifest_error"):
        adapter_reasons.append("adapter manifest is invalid")
    blockers = list(cast(list[str], migration_plan(root).get("conflicts", [])))
    effects = {
        3: "v3 adds project fields and explicit license settings",
        4: "v4 adds versioned reference and integration records",
        5: "v5 moves connection identity into user-local profiles",
        6: "v6 adds maintained harness and hook-policy contracts",
        7: "v7 enables Claude Code project state",
        8: "v8 adds scientific protocols and compute-job records",
    }
    return {
        "package_version": __version__,
        "project_schema": {
            "current": config.schema_version,
            "target": CURRENT_PROJECT_SCHEMA,
            "status": "current" if not schema_steps else "available",
            "steps": schema_steps,
            "effects": [effects[step["to_version"]] for step in schema_steps],
            "backups": ["smairt.yaml for every migration step"],
        },
        "managed_guidance": {
            "status": "available" if guidance["changes"] else "current",
            "changes": guidance["changes"],
            "preserved": guidance.get("legacy_preserved", []),
        },
        "harness_adapter": {
            "active": config.harness.active.value,
            "recorded": config.harness.adapter_version,
            "installed": manifest_version,
            "target": ADAPTER_VERSION,
            "status": "available" if adapter_reasons else "current",
            "reasons": adapter_reasons,
        },
        "detected": scaffold,
        "blockers": blockers,
        "updates_available": bool(schema_steps or guidance["changes"] or adapter_reasons),
        "network_accessed": False,
    }


def apply_project_updates(
    root: Path,
    *,
    contributor_id: str | None = None,
    allow_dirty: bool = False,
) -> dict[str, Any]:
    """Apply every conflict-free update in dependency order with durable receipts."""
    root = root.resolve()
    before = project_update_plan(root)
    if before["blockers"]:
        raise ValueError("project update is blocked: " + "; ".join(before["blockers"]))
    migrations: list[dict[str, object]] = []
    while SmairtConfig.load(root / "smairt.yaml").schema_version < CURRENT_PROJECT_SCHEMA:
        migrations.append(
            apply_migration(root, contributor_id=contributor_id, allow_dirty=allow_dirty)
        )
    guidance_preview = upgrade_project(root, apply=False)
    guidance = (
        upgrade_project(root, apply=True) if guidance_preview["changes"] else guidance_preview
    )
    current = project_update_plan(root)
    adapter: dict[str, object] | None = None
    if current["harness_adapter"]["status"] != "current":
        active = SmairtConfig.load(root / "smairt.yaml").harness.active.value
        adapter = install_harness(root, active, upgrade=True)
    return {
        "applied": True,
        "migrations": migrations,
        "managed_guidance": guidance,
        "harness_adapter": adapter,
        "final": project_update_plan(root),
        "network_accessed": False,
    }
