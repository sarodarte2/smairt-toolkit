"""Authoritative, conflict-aware coding-harness adapter management."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

import yaml

from smairt.models import HarnessName, SmairtConfig, utc_now
from smairt.utils import atomic_write, sha256_text

ADAPTER_VERSION = 2
BEGIN_MARKER = "<!-- SMAIRT:BEGIN MANAGED CORE -->"
END_MARKER = "<!-- SMAIRT:END MANAGED CORE -->"
CORE_RULES = """# SMAIRT managed core

- Treat `smairt.yaml` and portable records as authoritative scientific state.
- Run `smairt status --json`, `smairt next --json`, and task-scoped `smairt context` first.
- Never choose hypotheses, approve claims, or attribute contributors without the researcher.
- Never read or stage secrets, raw protected data, ignored PDFs, or protected local summaries.
- Use subagents only for independent read-only exploration and evidence gathering.
- Validate artifacts and run `smairt verify` before reporting completion.
"""


@dataclass(frozen=True)
class Adapter:
    """Describe one maintained harness adapter and its fully owned files."""

    name: HarnessName
    files: dict[str, str]
    executable: frozenset[str] = frozenset()


CODEX_FILES = {
    ".codex/config.toml": 'model_instructions_file = "../AGENTS.md"\n',
    ".codex/hooks.json": json.dumps(
        {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "^Bash$",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "smairt validate --tool-input",
                                "timeout": 30,
                                "statusMessage": "Checking SMAIRT safety policy",
                            }
                        ],
                    }
                ]
            }
        },
        indent=2,
    )
    + "\n",
}

ZOO_FILES = {
    ".roo/rules/01-smairt.md": (
        "# Zoo project behavior\n\nUse the shared AGENTS.md rules and the active SMAIRT action.\n"
    ),
    ".roo/rules-architect/01-research-planning.md": (
        "# Research planning\nPresent scientific choices to the human; do not mutate evidence.\n"
    ),
    ".roo/rules-code/01-research-code.md": (
        "# Research code\nUse SMAIRT iterations and immutable runs for every execution.\n"
    ),
    ".roo/rules-ask/01-research-review.md": (
        "# Research review\nRemain read-only and distinguish evidence from inference.\n"
    ),
    ".roo/rules-debug/01-run-integrity.md": (
        "# Debugging\nPreserve failures and create a new iteration when methods change.\n"
    ),
    ".roo/rules-orchestrator/01-delegation.md": (
        "# Orchestration\nDelegate only independent read-only exploration. Require source paths, "
        "findings, uncertainty, and recommended files in each handoff.\n"
    ),
    ".rooignore": (".env*\nreferences/pdfs/**\ndata/raw/**\ndata/local/**\n.smairt/local/**\n"),
    ".roomodes": yaml.safe_dump(
        {
            "customModes": [
                {
                    "slug": "smairt-review",
                    "name": "SMAIRT Evidence Review",
                    "roleDefinition": (
                        "Review SMAIRT evidence without editing files or crossing human gates."
                    ),
                    "groups": ["read"],
                    "customInstructions": (
                        "Run smairt status --json and smairt next --json; report uncertainty."
                    ),
                }
            ]
        },
        sort_keys=False,
    ),
}

CLINE_PRE_TOOL = """#!/bin/sh
INPUT=$(cat)
if printf '%s' "$INPUT" | smairt validate --tool-input >/dev/null 2>&1; then
  printf '%s\n' '{"cancel":false}'
else
  printf '%s\n' '{"cancel":true,"errorMessage":"SMAIRT safety validation failed"}'
fi
"""
CLINE_PRE_COMPACT = (
    "#!/bin/sh\ncat >/dev/null\n"
    'printf \'%s\\n\' \'{"cancel":false,"contextModification":'
    '"Run smairt next --json and reload SMAIRT context after compaction."}\'\n'
)
CLINE_FILES = {
    ".clinerules/01-smairt.md": (
        "# Cline project behavior\n\nUse the shared AGENTS.md rules and stop at human gates.\n"
    ),
    ".clinerules/research-code.md": (
        '---\npaths:\n  - "experiments/**"\n  - "scripts/**"\n---\n'
        "# Research code\nUse a new iteration for meaningful method changes.\n"
    ),
    ".clinerules/paper.md": (
        '---\npaths:\n  - "paper/**"\n---\n# Paper workflow\n'
        "Draft only from approved claims, current evidence, and verified references.\n"
    ),
    ".clinerules/hooks/PreToolUse": CLINE_PRE_TOOL,
    ".clinerules/hooks/PreCompact": CLINE_PRE_COMPACT,
    ".clineignore": (".env*\nreferences/pdfs/**\ndata/raw/**\ndata/local/**\n.smairt/local/**\n"),
    ".cline/workflows/smairt-next.md": (
        "# Continue SMAIRT research\n1. Run `smairt status --json`.\n"
        "2. Run `smairt next --json`.\n3. Load only task-scoped context.\n"
        "4. Use `/newtask` when the current context becomes broad.\n"
        "5. Stop at human scientific gates.\n"
    ),
}

ADAPTERS = {
    HarnessName.CODEX: Adapter(HarnessName.CODEX, CODEX_FILES),
    HarnessName.ZOO: Adapter(HarnessName.ZOO, ZOO_FILES),
    HarnessName.CLINE: Adapter(
        HarnessName.CLINE,
        CLINE_FILES,
        frozenset({".clinerules/hooks/PreToolUse", ".clinerules/hooks/PreCompact"}),
    ),
}

CAPABILITIES = {
    "codex": {"rules": True, "modes": False, "read_only_subagents": True},
    "zoo": {"rules": True, "modes": True, "read_only_subagents": False},
    "cline": {"rules": True, "modes": True, "read_only_subagents": True},
}


def _manifest_path(root: Path, harness: HarnessName) -> Path:
    return root / ".smairt/harnesses" / f"{harness.value}.json"


def _managed_block() -> str:
    return f"{BEGIN_MARKER}\n{CORE_RULES.rstrip()}\n{END_MARKER}\n"


def _merge_agents(existing: str) -> str:
    block = _managed_block()
    if BEGIN_MARKER not in existing or END_MARKER not in existing:
        prefix = existing.rstrip()
        return f"{prefix}\n\n{block}" if prefix else block
    before, remainder = existing.split(BEGIN_MARKER, 1)
    _, after = remainder.split(END_MARKER, 1)
    return (
        f"{before.rstrip()}\n\n{block}{after.lstrip()}"
        if before.strip()
        else block + after.lstrip()
    )


def _load_manifest(root: Path, harness: HarnessName) -> dict[str, object] | None:
    path = _manifest_path(root, harness)
    return json.loads(path.read_text()) if path.exists() else None


def harness_status(root: Path, harness: str | None = None) -> dict[str, object]:
    """Report installation, activation, missing files, and local modifications."""
    config = SmairtConfig.load(root / "smairt.yaml")
    name = HarnessName(harness) if harness else config.harness.active
    manifest = _load_manifest(root, name)
    modified: list[str] = []
    missing: list[str] = []
    if manifest:
        for relative, digest in dict(manifest.get("files", {})).items():
            target = root / relative
            if not target.exists():
                missing.append(relative)
            elif sha256_text(target.read_text()) != digest:
                modified.append(relative)
    return {
        "harness": name.value,
        "active": config.harness.active == name,
        "installed": manifest is not None,
        "adapter_version": manifest.get("version") if manifest else None,
        "modified": modified,
        "missing": missing,
    }


def switch_plan(root: Path, harness: str) -> dict[str, object]:
    """Preview a harness switch without changing project state."""
    target_name = HarnessName(harness)
    config = SmairtConfig.load(root / "smairt.yaml")
    current_name = config.harness.active
    current_manifest = _load_manifest(root, current_name) or {"files": {}}
    target_manifest = _load_manifest(root, target_name) or {"files": {}}
    current_files = dict(current_manifest.get("files", {}))
    known_target = dict(target_manifest.get("files", {}))
    target_files = ADAPTERS[target_name].files
    remove: list[str] = []
    modified: list[str] = []
    conflicts: list[str] = []
    preserve: list[str] = []
    for relative, digest in current_files.items():
        if relative in target_files:
            path = root / relative
            if path.exists() and sha256_text(path.read_text()) != digest:
                modified.append(relative)
            continue
        path = root / relative
        if not path.exists():
            continue
        if sha256_text(path.read_text()) == digest:
            remove.append(relative)
        else:
            modified.append(relative)
    for relative in target_files:
        path = root / relative
        if path.exists() and relative not in current_files:
            prior_digest = known_target.get(relative)
            if prior_digest is None or sha256_text(path.read_text()) != prior_digest:
                conflicts.append(relative)
    for directory in (".codex", ".roo", ".cline", ".clinerules"):
        base = root / directory
        if base.exists():
            owned = set(current_files) | set(target_files)
            preserve.extend(
                str(path.relative_to(root))
                for path in base.rglob("*")
                if path.is_file() and str(path.relative_to(root)) not in owned
            )
    return {
        "from": current_name.value,
        "to": target_name.value,
        "create_or_update": sorted(target_files),
        "remove": sorted(remove),
        "modified_managed": sorted(modified),
        "conflicts": sorted(conflicts),
        "preserved_custom": sorted(set(preserve)),
        "can_apply": not conflicts and not modified,
    }


def select_harness(
    root: Path,
    harness: str,
    *,
    dry_run: bool = False,
    backup_and_switch: bool = False,
) -> dict[str, object]:
    """Select exactly one harness while preserving custom and modified files."""
    plan = switch_plan(root, harness)
    if dry_run:
        return plan
    if plan["conflicts"]:
        raise ValueError(
            "target files already exist and are unmanaged: " + ", ".join(plan["conflicts"])
        )
    if plan["modified_managed"] and not backup_and_switch:
        raise ValueError(
            "locally modified managed files require --backup-and-switch: "
            + ", ".join(plan["modified_managed"])
        )
    target_name = HarnessName(harness)
    stamp = utc_now().replace(":", "").replace("+", "_")
    backup_root = root / ".smairt/backups/harness-switch" / stamp
    for relative in plan["modified_managed"]:
        source = root / relative
        destination = backup_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        source.unlink()
    for relative in plan["remove"]:
        (root / relative).unlink(missing_ok=True)
    agents = root / "AGENTS.md"
    atomic_write(agents, _merge_agents(agents.read_text() if agents.exists() else ""))
    hashes: dict[str, str] = {}
    adapter = ADAPTERS[target_name]
    for relative, content in adapter.files.items():
        path = root / relative
        atomic_write(path, content)
        if relative in adapter.executable:
            path.chmod(0o755)
        hashes[relative] = sha256_text(content)
    manifest = {
        "harness": target_name.value,
        "version": ADAPTER_VERSION,
        "activated_at": utc_now(),
        "files": hashes,
        "shared_agents_block_sha256": sha256_text(_managed_block()),
    }
    atomic_write(_manifest_path(root, target_name), json.dumps(manifest, indent=2) + "\n")
    config = SmairtConfig.load(root / "smairt.yaml")
    config.harness.active = target_name
    config.harness.adapter_version = ADAPTER_VERSION
    config.harness.activated_at = utc_now()
    config.dump(root / "smairt.yaml")
    write_compatibility_fixture(root, target_name.value)
    return {
        **harness_status(root),
        "backup": str(backup_root.relative_to(root)) if plan["modified_managed"] else None,
    }


def install_harness(root: Path, harness: str, *, upgrade: bool = False) -> dict[str, object]:
    """Compatibility alias for authoritative selection."""
    return select_harness(root, harness, backup_and_switch=upgrade)


def list_harnesses(root: Path) -> list[dict[str, object]]:
    """Return status for every maintained harness adapter."""
    return [harness_status(root, name.value) for name in HarnessName]


def write_compatibility_fixture(root: Path, harness: str) -> Path:
    """Write a portable adapter fixture without duplicating scientific state."""
    name = HarnessName(harness)
    payload = compatibility_payload(name.value)
    path = root / ".smairt/contracts/v1/fixtures" / f"{name.value}.json"
    atomic_write(path, json.dumps(payload, indent=2) + "\n")
    return path


def compatibility_payload(harness: str) -> dict[str, object]:
    """Return one stable adapter fixture payload for any export destination."""
    name = HarnessName(harness)
    return {
        "contract_version": 1,
        "harness": name.value,
        "capabilities": CAPABILITIES[name.value],
        "commands": {
            "status": "smairt status --json",
            "next": "smairt next --json",
            "validate": "smairt validate --json",
        },
        "exit_codes": {"success": 0, "validation_failure": 1, "usage_or_project_error": 2},
        "human_gates": [
            "hypothesis_selection",
            "scientific_decision",
            "claim_approval",
            "contributor_confirmation",
            "evidence_correction",
        ],
    }
