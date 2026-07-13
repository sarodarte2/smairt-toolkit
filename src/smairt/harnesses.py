"""Authoritative, conflict-aware coding-harness adapter management."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from smairt.locking import mutating
from smairt.models import HarnessName, SmairtConfig, utc_now
from smairt.transactions import FileTransaction
from smairt.utils import ensure_within, sha256_text

ADAPTER_VERSION = 4
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


CODEX_FILES: dict[str, str] = {}

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

MCP_TOOL_NAMES = [
    "reference_search",
    "reference_get",
    "zotero_search",
    "zotero_get_item",
    "zotero_list_collections",
]

CLINE_PRE_TOOL = """#!/bin/sh
INPUT=$(cat)
if printf '%s' "$INPUT" | smairt validate --tool-input >/dev/null 2>&1; then
  printf '%s\n' '{"cancel":false}'
else
  printf '%s\n' '{"cancel":true,"errorMessage":"SMAIRT safety validation failed"}'
fi
"""
CLINE_CONTEXT_RESTORE = """#!/bin/sh
cat >/dev/null
if ! command -v smairt >/dev/null 2>&1; then
  printf '%s\n' '{"cancel":false,"contextModification":"SMAIRT CLI unavailable; do not mutate research state until project context is restored."}'
  exit 0
fi
STATUS=$(smairt status --json 2>/dev/null || printf '%s' 'status unavailable')
NEXT=$(smairt next --json 2>/dev/null || printf '%s' 'next action unavailable')
export SMAIRT_HOOK_CONTEXT="SMAIRT project context:\n$STATUS\n\nRecommended next action:\n$NEXT\n\nLoad only task-scoped context and stop at human scientific gates."
PYTHON=$(command -v python3 || command -v python || true)
if [ -z "$PYTHON" ]; then
  printf '%s\n' '{"cancel":false,"contextModification":"Run smairt status --json and smairt next --json before continuing."}'
else
  "$PYTHON" -c 'import json, os; print(json.dumps({"cancel": False, "contextModification": os.environ["SMAIRT_HOOK_CONTEXT"]}))'
fi
"""
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
    ".clinerules/hooks/TaskStart": CLINE_CONTEXT_RESTORE,
    ".clinerules/hooks/TaskResume": CLINE_CONTEXT_RESTORE,
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
        frozenset(
            {
                ".clinerules/hooks/PreToolUse",
                ".clinerules/hooks/TaskStart",
                ".clinerules/hooks/TaskResume",
            }
        ),
    ),
}


def _adapter(root: Path, name: HarnessName, *, enabled: bool | None = None) -> Adapter:
    """Render current project-scoped adapter files without embedding credentials."""
    base = ADAPTERS[name]
    files = dict(base.files)
    config = SmairtConfig.load(root / "smairt.yaml")
    is_enabled = name in config.integrations.mcp.enabled_harnesses if enabled is None else enabled
    if name is HarnessName.CODEX:
        content = (
            'model_instructions_file = "../AGENTS.md"\n\n'
            '[[hooks.PreToolUse]]\nmatcher = "^Bash$"\n\n'
            '[[hooks.PreToolUse.hooks]]\ntype = "command"\n'
            'command = "smairt validate --tool-input"\ntimeout = 30\n'
            'statusMessage = "Checking SMAIRT safety policy"\n'
        )
        if is_enabled:
            content += (
                '\n[mcp_servers.smairt]\ncommand = "smairt"\nargs = ["mcp", "serve"]\n'
                f"enabled_tools = {json.dumps(MCP_TOOL_NAMES)}\n"
            )
        files[".codex/config.toml"] = content
    elif name is HarnessName.ZOO:
        path = _managed_path(root, ".roo/mcp.json")
        payload: dict[str, Any] = {"mcpServers": {}}
        if path.exists():
            try:
                loaded = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ValueError(".roo/mcp.json must be valid JSON") from exc
            if not isinstance(loaded, dict) or not isinstance(loaded.get("mcpServers", {}), dict):
                raise ValueError(".roo/mcp.json must contain an mcpServers object")
            payload = loaded
            payload.setdefault("mcpServers", {})
        servers = payload["mcpServers"]
        servers.pop("smairt", None)
        if is_enabled:
            servers["smairt"] = {
                "command": "smairt",
                "args": ["mcp", "serve"],
                "alwaysAllow": MCP_TOOL_NAMES,
            }
        if servers:
            files[".roo/mcp.json"] = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    return Adapter(name, files, base.executable)


CAPABILITIES: dict[str, dict[str, object]] = {
    "codex": {
        "rules": "advisory",
        "protected_operation_hook": "advisory",
        "modes": "unsupported",
        "context_restore": "manual",
        "mcp": "read_only_opt_in",
        "configuration_notice": "project hooks and MCP require Codex project trust",
    },
    "zoo": {
        "rules": "advisory",
        "protected_operation_hook": "unsupported",
        "modes": "advisory",
        "context_restore": "manual",
        "mcp": "read_only_opt_in",
        "project_paths": ".roo, .roomodes, and .rooignore are intentionally Roo-compatible",
    },
    "cline": {
        "rules": "advisory",
        "protected_operation_hook": "blocking",
        "modes": "advisory",
        "context_restore": "advisory",
        "mcp": "deferred",
    },
}


def _manifest_path(root: Path, harness: HarnessName) -> Path:
    return _managed_path(root, f".smairt/harnesses/{harness.value}.json")


def _managed_path(root: Path, relative: str) -> Path:
    """Resolve one manifest or adapter path without following project symlinks."""
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe managed harness path: {relative}")
    current = root.resolve()
    for part in path.parts:
        current /= part
        if current.is_symlink():
            raise ValueError(f"managed harness path must not be a symlink: {relative}")
    return ensure_within(root, current)


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


def _load_manifest(root: Path, harness: HarnessName) -> dict[str, Any] | None:
    path = _manifest_path(root, harness)
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("harness manifest root must be an object")
    required = {"harness", "version", "activated_at", "files", "shared_agents_block_sha256"}
    if set(payload) != required or payload.get("harness") != harness.value:
        raise ValueError("harness manifest identity or fields are invalid")
    if not isinstance(payload.get("version"), int) or not isinstance(
        payload.get("activated_at"), str
    ):
        raise ValueError("harness manifest version or timestamp is invalid")
    files = payload.get("files")
    if not isinstance(files, dict) or not all(
        isinstance(relative, str)
        and isinstance(digest, str)
        and re.fullmatch(r"[a-f0-9]{64}", digest)
        for relative, digest in files.items()
    ):
        raise ValueError("harness manifest file digests are invalid")
    if not re.fullmatch(r"[a-f0-9]{64}", str(payload.get("shared_agents_block_sha256"))):
        raise ValueError("harness manifest AGENTS digest is invalid")
    return payload


def _validate_zoo_modes(content: str) -> list[str]:
    """Validate the portable subset of Zoo's Roo-compatible mode schema."""
    try:
        payload = yaml.safe_load(content)
    except yaml.YAMLError:
        return [".roomodes is not valid YAML"]
    modes = payload.get("customModes") if isinstance(payload, dict) else None
    if not isinstance(modes, list):
        return [".roomodes must contain a customModes list"]
    errors: list[str] = []
    required = {"slug", "name", "roleDefinition", "groups", "customInstructions"}
    slugs: set[str] = set()
    for index, mode in enumerate(modes):
        if not isinstance(mode, dict) or not required.issubset(mode):
            errors.append(f"custom mode {index} is missing required fields")
            continue
        slug = mode.get("slug")
        if not isinstance(slug, str) or not re.fullmatch(r"[a-z][a-z0-9-]{1,63}", slug):
            errors.append(f"custom mode {index} has an invalid slug")
        elif slug in slugs:
            errors.append(f"custom mode {index} duplicates slug {slug}")
        else:
            slugs.add(slug)
        for field in ("name", "roleDefinition", "customInstructions"):
            if not isinstance(mode.get(field), str) or not mode[field].strip():
                errors.append(f"custom mode {index} has invalid {field}")
        if not isinstance(mode["groups"], list) or not mode["groups"]:
            errors.append(f"custom mode {index} groups must be a list")
        elif not all(
            isinstance(group, str) and group in {"read", "edit", "browser", "command", "mcp"}
            for group in mode["groups"]
        ):
            errors.append(f"custom mode {index} contains unsupported groups")
    return errors


def harness_status(root: Path, harness: str | None = None) -> dict[str, Any]:
    """Report installation, activation, missing files, and local modifications."""
    config = SmairtConfig.load(root / "smairt.yaml")
    name = HarnessName(harness) if harness else config.harness.active
    manifest_error: str | None = None
    try:
        manifest = _load_manifest(root, name)
    except (OSError, ValueError, TypeError):
        manifest = None
        manifest_error = "manifest is malformed"
    modified: list[str] = []
    missing: list[str] = []
    executable_errors: list[str] = []
    schema_errors: list[str] = []
    try:
        if manifest:
            declared_files = dict(manifest.get("files", {}))
            for relative in _adapter(root, name).files:
                if relative not in declared_files:
                    missing.append(relative)
            for relative, digest in dict(manifest.get("files", {})).items():
                target = _managed_path(root, relative)
                if not target.exists():
                    missing.append(relative)
                elif sha256_text(target.read_text()) != digest:
                    modified.append(relative)
        executable_errors = [
            relative
            for relative in _adapter(root, name).executable
            if _managed_path(root, relative).exists()
            and not _managed_path(root, relative).stat().st_mode & 0o111
        ]
        schema_errors = (
            _validate_zoo_modes(_managed_path(root, ".roomodes").read_text())
            if name is HarnessName.ZOO and _managed_path(root, ".roomodes").exists()
            else []
        )
    except (OSError, TypeError, ValueError) as exc:
        manifest_error = f"unsafe or unreadable managed path: {exc}"
    version = manifest.get("version") if manifest else None
    return {
        "harness": name.value,
        "active": config.harness.active == name,
        "installed": manifest is not None,
        "adapter_version": version,
        "adapter_supported": version == ADAPTER_VERSION if manifest else False,
        "capabilities": CAPABILITIES[name.value],
        "modified": modified,
        "missing": missing,
        "non_executable": executable_errors,
        "schema_errors": schema_errors,
        "manifest_error": manifest_error,
        "configuration_notice": (
            "Cline hooks must be enabled in Cline settings"
            if name is HarnessName.CLINE
            else "Codex project hooks and MCP require project trust"
            if name is HarnessName.CODEX
            else None
        ),
    }


def switch_plan(root: Path, harness: str) -> dict[str, Any]:
    """Preview a harness switch without changing project state."""
    target_name = HarnessName(harness)
    config = SmairtConfig.load(root / "smairt.yaml")
    current_name = config.harness.active
    current_manifest = _load_manifest(root, current_name) or {"files": {}}
    target_manifest = _load_manifest(root, target_name) or {"files": {}}
    current_files = dict(current_manifest.get("files", {}))
    known_target = dict(target_manifest.get("files", {}))
    target_files = _adapter(root, target_name).files
    remove: list[str] = []
    modified: list[str] = []
    conflicts: list[str] = []
    preserve: list[str] = []
    for relative, digest in current_files.items():
        if relative in target_files:
            path = _managed_path(root, relative)
            if path.exists() and sha256_text(path.read_text()) != digest:
                modified.append(relative)
            continue
        path = _managed_path(root, relative)
        if not path.exists():
            continue
        if sha256_text(path.read_text()) == digest:
            remove.append(relative)
        else:
            modified.append(relative)
    for relative in target_files:
        path = _managed_path(root, relative)
        if path.exists() and relative not in current_files:
            prior_digest = known_target.get(relative)
            if prior_digest is None or sha256_text(path.read_text()) != prior_digest:
                conflicts.append(relative)
    for directory in (".codex", ".roo", ".cline", ".clinerules"):
        base = _managed_path(root, directory)
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


@mutating("harness select")
def select_harness(
    root: Path,
    harness: str,
    *,
    dry_run: bool = False,
    backup_and_switch: bool = False,
) -> dict[str, Any]:
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
    if target_name is HarnessName.ZOO:
        errors = _validate_zoo_modes(ZOO_FILES[".roomodes"])
        if errors:
            raise ValueError("invalid generated Zoo modes: " + "; ".join(errors))
    transaction = FileTransaction(root, "harness select")
    backup_root = _stage_harness_selection(root, target_name, plan, transaction)
    transaction.commit()
    return {
        **harness_status(root),
        "backup": str(backup_root.relative_to(root)) if plan["modified_managed"] else None,
    }


def _stage_harness_selection(
    root: Path,
    target_name: HarnessName,
    plan: dict[str, Any],
    transaction: FileTransaction,
) -> Path:
    """Stage a prevalidated harness switch into a caller-owned transaction."""
    stamp = utc_now().replace(":", "").replace("+", "_")
    backup_root = _managed_path(root, f".smairt/backups/harness-switch/{stamp}")
    for relative in plan["modified_managed"]:
        source = _managed_path(root, relative)
        destination = backup_root / relative
        transaction.stage_bytes(
            destination, source.read_bytes(), mode=source.stat().st_mode & 0o777
        )
        if relative not in _adapter(root, target_name).files:
            transaction.stage_delete(source)
    for relative in plan["remove"]:
        transaction.stage_delete(_managed_path(root, relative))
    agents = _managed_path(root, "AGENTS.md")
    transaction.stage_text(agents, _merge_agents(agents.read_text() if agents.exists() else ""))
    hashes: dict[str, str] = {}
    adapter = _adapter(root, target_name)
    for relative, content in adapter.files.items():
        path = _managed_path(root, relative)
        transaction.stage_text(
            path, content, mode=0o755 if relative in adapter.executable else None
        )
        hashes[relative] = sha256_text(content)
    manifest = {
        "harness": target_name.value,
        "version": ADAPTER_VERSION,
        "activated_at": utc_now(),
        "files": hashes,
        "shared_agents_block_sha256": sha256_text(_managed_block()),
    }
    transaction.stage_text(
        _manifest_path(root, target_name), json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    config = SmairtConfig.load(root / "smairt.yaml")
    config.harness.active = target_name
    config.harness.adapter_version = ADAPTER_VERSION
    config.harness.activated_at = utc_now()
    transaction.stage_text(
        root / "smairt.yaml",
        config.to_yaml(),
    )
    fixture = root / ".smairt/contracts/v1/fixtures" / f"{target_name.value}.json"
    transaction.stage_text(
        fixture,
        json.dumps(compatibility_payload(target_name.value), indent=2, sort_keys=True) + "\n",
    )
    return backup_root


def install_harness(root: Path, harness: str, *, upgrade: bool = False) -> dict[str, object]:
    """Compatibility alias for authoritative selection."""
    return select_harness(root, harness, backup_and_switch=upgrade)


def list_harnesses(root: Path) -> list[dict[str, object]]:
    """Return status for every maintained harness adapter."""
    return [harness_status(root, name.value) for name in HarnessName]


def mcp_status(root: Path) -> dict[str, object]:
    """Report project-scoped MCP state without starting a provider connection."""
    config = SmairtConfig.load(root / "smairt.yaml")
    return {
        "active_harness": config.harness.active.value,
        "enabled_harnesses": [item.value for item in config.integrations.mcp.enabled_harnesses],
        "zotero_access": config.integrations.zotero.mcp_access_enabled,
        "tools": MCP_TOOL_NAMES,
        "network_accessed": False,
    }


@mutating("MCP harness configuration")
def configure_mcp(
    root: Path,
    harness: HarnessName,
    enabled: bool,
    *,
    dry_run: bool = False,
) -> dict[str, object]:
    """Transactionally toggle MCP for the active Codex or Zoo adapter."""
    config = SmairtConfig.load(root / "smairt.yaml")
    if config.schema_version < 4:
        raise ValueError("MCP settings require schema v4; run 'smairt migrate apply'")
    if harness is HarnessName.CLINE:
        raise ValueError("Cline MCP configuration is deferred")
    if config.harness.active is not harness:
        raise ValueError("MCP can be changed only for the active harness")
    currently_enabled = harness in config.integrations.mcp.enabled_harnesses
    if currently_enabled is enabled:
        return {
            "harness": harness.value,
            "enabled": enabled,
            "changed": False,
            "files": [],
            **mcp_status(root),
        }
    manifest = _load_manifest(root, harness)
    if manifest is None:
        raise ValueError("active harness is not installed")
    modified = []
    for relative, digest in dict(manifest["files"]).items():
        path = _managed_path(root, relative)
        if path.exists() and sha256_text(path.read_text()) != digest:
            if harness is HarnessName.ZOO and relative == ".roo/mcp.json":
                # This shared Zoo file may contain researcher-owned server entries.
                _adapter(root, harness, enabled=enabled)
                continue
            modified.append(relative)
    if modified:
        raise ValueError(
            "locally modified managed files prevent MCP changes: " + ", ".join(modified)
        )
    plan: dict[str, Any] = {
        "harness": harness.value,
        "enabled": enabled,
        "changed": True,
        "files": [],
    }
    next_adapter = _adapter(root, harness, enabled=enabled)
    current_files = dict(manifest["files"])
    plan["files"] = sorted(
        relative
        for relative in set(current_files) | set(next_adapter.files)
        if relative not in next_adapter.files
        or not _managed_path(root, relative).exists()
        or _managed_path(root, relative).read_text() != next_adapter.files[relative]
    )
    if dry_run:
        return plan
    enabled_harnesses = config.integrations.mcp.enabled_harnesses
    if enabled and harness not in enabled_harnesses:
        enabled_harnesses.append(harness)
    if not enabled:
        config.integrations.mcp.enabled_harnesses = [
            item for item in enabled_harnesses if item is not harness
        ]
    transaction = FileTransaction(root, "MCP harness configuration")
    hashes: dict[str, str] = {}
    for relative in set(current_files) - set(next_adapter.files):
        path = _managed_path(root, relative)
        if path.exists():
            transaction.stage_delete(path)
    for relative, content in next_adapter.files.items():
        path = _managed_path(root, relative)
        if not path.exists() or path.read_text() != content:
            transaction.stage_text(path, content)
        hashes[relative] = sha256_text(content)
    next_manifest = {
        "harness": harness.value,
        "version": ADAPTER_VERSION,
        "activated_at": manifest["activated_at"],
        "files": hashes,
        "shared_agents_block_sha256": sha256_text(_managed_block()),
    }
    transaction.stage_text(
        _manifest_path(root, harness), json.dumps(next_manifest, indent=2, sort_keys=True) + "\n"
    )
    transaction.stage_text(
        root / "smairt.yaml",
        config.to_yaml(),
    )
    transaction.commit()
    return {**plan, **mcp_status(root)}


@mutating("harness fixture write")
def write_compatibility_fixture(root: Path, harness: str) -> Path:
    """Write a portable adapter fixture without duplicating scientific state."""
    name = HarnessName(harness)
    payload = compatibility_payload(name.value)
    path = root / ".smairt/contracts/v1/fixtures" / f"{name.value}.json"
    transaction = FileTransaction(root, "harness fixture write")
    transaction.stage_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    transaction.commit()
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
        "exit_codes": {
            "success": 0,
            "validation_failure": 1,
            "usage_or_project_error": 2,
            "lock_or_recovery_required": 3,
        },
        "human_gates": [
            "hypothesis_selection",
            "scientific_decision",
            "claim_approval",
            "contributor_confirmation",
            "evidence_correction",
        ],
    }
