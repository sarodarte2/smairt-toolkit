"""Authoritative, conflict-aware coding-harness adapter management."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from pathlib import Path
from typing import Any, cast

import yaml

from smairt.harness_presentation import harness_info as presentation_info
from smairt.locking import mutating
from smairt.models import HarnessName, SmairtConfig, utc_now
from smairt.transactions import FileTransaction
from smairt.utils import ensure_within, sha256_text
from smairt.workflows import (
    WORKFLOW_SLUGS,
    claude_skill_files,
    cline_workflow_files,
    opencode_command_files,
)

ADAPTER_VERSION = 7
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
    merged_json: frozenset[str] = frozenset()
    json_ownership: dict[str, Any] = dataclass_field(default_factory=dict)


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
                    "name": "SMAIRT · Evidence Review",
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
if ! command -v smairt >/dev/null 2>&1; then
  printf '%s\n' '{"cancel":true,"contextModification":"","errorMessage":"SMAIRT CLI unavailable; protected operation denied."}'
  exit 0
fi
printf '%s' "$INPUT" | smairt harness hook --harness cline --event PreToolUse
"""
CLINE_CONTEXT_RESTORE = """#!/bin/sh
INPUT=$(cat)
EVENT=$(basename "$0")
if ! command -v smairt >/dev/null 2>&1; then
  printf '%s\n' '{"cancel":false,"contextModification":"SMAIRT CLI unavailable; do not mutate research state.","errorMessage":""}'
  exit 0
fi
printf '%s' "$INPUT" | smairt harness hook --harness cline --event "$EVENT"
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
    ".clinerules/hooks/PreCompact": CLINE_CONTEXT_RESTORE,
    ".clineignore": (".env*\nreferences/pdfs/**\ndata/raw/**\ndata/local/**\n.smairt/local/**\n"),
    **cline_workflow_files(),
}

CODEX_HOOK = """#!/bin/sh
INPUT=$(cat)
EVENT=${1:-PreToolUse}
if ! command -v smairt >/dev/null 2>&1; then
  printf '%s\n' '{"decision":"block","reason":"SMAIRT CLI unavailable; protected operation denied."}'
  exit 0
fi
printf '%s' "$INPUT" | smairt harness hook --harness codex --event "$EVENT"
"""

CURSOR_HOOK = """#!/bin/sh
INPUT=$(cat)
EVENT=${1:-preToolUse}
if ! command -v smairt >/dev/null 2>&1; then
  printf '%s\n' '{"decision":"block","reason":"SMAIRT CLI unavailable; protected operation denied."}'
  exit 0
fi
printf '%s' "$INPUT" | smairt harness hook --harness cursor --event "$EVENT"
"""

OPENCODE_FILES = {
    **opencode_command_files(),
    ".opencode/agents/smairt-reviewer.md": (
        "---\ndescription: Read-only adversarial review of bounded SMAIRT evidence\n"
        "mode: subagent\npermission:\n  edit: deny\n  bash: deny\n  external_directory: deny\n"
        "---\n\n# SMAIRT · Adversarial Reviewer\n\n"
        "Review only the packet supplied by the parent agent. Identify the strongest objection, "
        "unsupported assumptions, alternative explanations, missing controls, falsifiers, and "
        "provenance gaps. Return severity, confidence, and the smallest useful follow-up test. "
        "Never change files or approve scientific decisions.\n"
    ),
}

CURSOR_FILES = {
    ".cursor/rules/smairt.mdc": (
        "---\ndescription: SMAIRT scientific workflow and human-gate policy\nalwaysApply: true\n"
        "---\n\nUse AGENTS.md and `smairt next --prompt`. Never cross a human scientific gate.\n"
    ),
    ".cursorignore": ".env*\nreferences/pdfs/**\ndata/raw/**\ndata/local/**\n.smairt/local/**\n",
    ".cursor/hooks/smairt-hook": CURSOR_HOOK,
    ".cursor/agents/smairt-reviewer.md": (
        "---\nname: smairt-reviewer\n"
        "description: Challenge a bounded SMAIRT artifact without changing project state\n"
        "model: inherit\nreadonly: true\n---\n\n"
        "# SMAIRT · Adversarial Reviewer\n\n"
        "Review only the bounded packet supplied by the parent. Report the strongest objection, "
        "unsupported assumptions, alternatives, missing controls, falsifiers, provenance gaps, "
        "severity, confidence, and the smallest useful follow-up test. Do not edit files.\n"
    ),
    ".cursor/cli.json": (
        json.dumps(
            {
                "permissions": {
                    "allow": [
                        "Shell(smairt)",
                        "Read(**/*.md)",
                        "Read(**/*.yaml)",
                        "Read(**/*.json)",
                    ],
                    "deny": [
                        "Shell(rm)",
                        "Read(.env*)",
                        "Read(references/pdfs/**)",
                        "Read(data/raw/**)",
                        "Read(data/local/**)",
                        "Read(.smairt/local/**)",
                        "Write(.env*)",
                        "Write(references/pdfs/**)",
                        "Write(data/raw/**)",
                        "Write(data/local/**)",
                        "Write(.smairt/local/**)",
                    ],
                }
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ),
}

CLAUDE_HOOK = """#!/bin/sh
INPUT=$(cat)
EVENT=${1:-PreToolUse}
if ! command -v smairt >/dev/null 2>&1; then
  printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"SMAIRT CLI unavailable; protected operation denied."}}'
  exit 0
fi
printf '%s' "$INPUT" | smairt harness hook --harness claude --event "$EVENT"
"""

CLAUDE_SETTINGS_PATH = ".claude/settings.json"
CLAUDE_MCP_PATH = ".mcp.json"
CLAUDE_DENY_RULES = (
    "Read(./.env*)",
    "Read(./references/pdfs/**)",
    "Read(./data/raw/**)",
    "Read(./data/local/**)",
    "Read(./.smairt/local/**)",
    "Write(./.env*)",
    "Write(./references/pdfs/**)",
    "Write(./data/raw/**)",
    "Write(./data/local/**)",
    "Write(./.smairt/local/**)",
)
CLAUDE_HOOK_COMMAND = "${CLAUDE_PROJECT_DIR}/.claude/hooks/smairt-hook"


def _claude_hook(event: str, matcher: str) -> dict[str, Any]:
    """Return one identifiable Claude hook entry owned by SMAIRT."""
    return {
        "matcher": matcher,
        "hooks": [
            {
                "type": "command",
                "command": f"{CLAUDE_HOOK_COMMAND} {event}",
                "timeout": 30,
            }
        ],
    }


CLAUDE_HOOKS = {
    "SessionStart": _claude_hook("SessionStart", "startup|resume|clear|compact"),
    "PreToolUse": _claude_hook("PreToolUse", "Bash|Edit|Write|NotebookEdit|mcp__.*"),
    "PreCompact": _claude_hook("PreCompact", "manual|auto"),
}

CLAUDE_FILES = {
    ".claude/CLAUDE.md": (
        "# SMAIRT project guidance\n\n@../AGENTS.md\n\n"
        "Begin with `smairt status --json` and `smairt next --json`. "
        "Use the project skills explicitly and stop at every researcher decision gate.\n"
    ),
    ".claude/agents/smairt-reviewer.md": (
        "---\nname: smairt-reviewer\n"
        "description: Challenge bounded SMAIRT evidence without changing project state\n"
        "tools: Read, Grep, Glob\npermissionMode: plan\n"
        "---\n\n# SMAIRT · Adversarial Reviewer\n\n"
        "Review only the packet supplied by the parent. Identify the strongest objection, "
        "unsupported assumptions, alternatives, missing controls, falsifiers, and provenance "
        "gaps. Return severity, confidence, and the smallest useful follow-up test. Never edit "
        "files or approve scientific decisions.\n"
    ),
    ".claude/hooks/smairt-hook": CLAUDE_HOOK,
    **claude_skill_files(),
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
                ".clinerules/hooks/PreCompact",
            }
        ),
    ),
    HarnessName.OPENCODE: Adapter(HarnessName.OPENCODE, OPENCODE_FILES),
    HarnessName.CURSOR: Adapter(
        HarnessName.CURSOR,
        CURSOR_FILES,
        frozenset({".cursor/hooks/smairt-hook"}),
    ),
    HarnessName.CLAUDE: Adapter(
        HarnessName.CLAUDE,
        CLAUDE_FILES,
        frozenset({".claude/hooks/smairt-hook"}),
        frozenset({CLAUDE_SETTINGS_PATH, CLAUDE_MCP_PATH}),
    ),
}


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    """Load an optional shared JSON object without accepting malformed user configuration."""
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} root must be an object")
    return payload


def _prior_claude_ownership(root: Path) -> dict[str, Any]:
    """Load previously recorded fragment ownership without trusting it as project input."""
    path = _managed_path(root, ".smairt/harnesses/claude.json")
    if not path.exists():
        return {}
    payload = _load_json_object(path, "Claude harness manifest")
    ownership = payload.get("json_ownership", {})
    return ownership if isinstance(ownership, dict) else {}


def _claude_settings(root: Path, prior: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Merge SMAIRT-owned permissions and hooks into researcher-owned Claude settings."""
    payload = _load_json_object(_managed_path(root, CLAUDE_SETTINGS_PATH), CLAUDE_SETTINGS_PATH)
    prior_settings = prior.get(CLAUDE_SETTINGS_PATH, {})
    prior_settings = prior_settings if isinstance(prior_settings, dict) else {}
    prior_deny = set(prior_settings.get("deny", []))
    prior_hooks = set(prior_settings.get("hooks", []))
    ownership: dict[str, Any] = {"deny": [], "hooks": []}
    permissions = payload.setdefault("permissions", {})
    if not isinstance(permissions, dict):
        raise ValueError(".claude/settings.json permissions must be an object")
    deny = permissions.setdefault("deny", [])
    if not isinstance(deny, list) or not all(isinstance(item, str) for item in deny):
        raise ValueError(".claude/settings.json permissions.deny must be a string list")
    for rule in CLAUDE_DENY_RULES:
        if rule not in deny:
            deny.append(rule)
            ownership["deny"].append(rule)
        elif rule in prior_deny:
            ownership["deny"].append(rule)
    permissions["deny"] = list(dict.fromkeys(deny))
    hooks = payload.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError(".claude/settings.json hooks must be an object")
    for event, owned in CLAUDE_HOOKS.items():
        entries = hooks.setdefault(event, [])
        if not isinstance(entries, list):
            raise ValueError(f".claude/settings.json hooks.{event} must be a list")
        matching = [entry for entry in entries if _is_claude_owned_hook(entry)]
        if event in prior_hooks:
            entries[:] = [entry for entry in entries if not _is_claude_owned_hook(entry)]
            entries.append(owned)
            ownership["hooks"].append(event)
        elif not matching:
            entries.append(owned)
            ownership["hooks"].append(event)
    return payload, ownership


def _is_claude_owned_hook(entry: object) -> bool:
    """Identify only the hook entry whose command points at SMAIRT's project hook."""
    return CLAUDE_HOOK_COMMAND in json.dumps(entry, sort_keys=True)


def _strip_claude_owned(
    relative: str, payload: dict[str, Any], ownership: dict[str, Any]
) -> dict[str, Any]:
    """Remove only SMAIRT's recorded fragments from a shared Claude JSON file."""
    if relative == CLAUDE_MCP_PATH:
        servers = payload.get("mcpServers")
        if isinstance(servers, dict) and ownership.get("server") is True:
            servers.pop("smairt", None)
            if not servers:
                payload.pop("mcpServers", None)
        return payload
    permissions = payload.get("permissions")
    owned_deny = set(ownership.get("deny", []))
    if isinstance(permissions, dict) and isinstance(permissions.get("deny"), list):
        permissions["deny"] = [item for item in permissions["deny"] if item not in owned_deny]
        if not permissions["deny"]:
            permissions.pop("deny", None)
        if not permissions:
            payload.pop("permissions", None)
    hooks = payload.get("hooks")
    owned_hooks = set(ownership.get("hooks", []))
    if isinstance(hooks, dict):
        for event in tuple(hooks):
            entries = hooks[event]
            if isinstance(entries, list) and event in owned_hooks:
                hooks[event] = [entry for entry in entries if not _is_claude_owned_hook(entry)]
                if not hooks[event]:
                    hooks.pop(event, None)
        if not hooks:
            payload.pop("hooks", None)
    return payload


def _claude_owned_present(
    relative: str, payload: dict[str, Any], ownership: dict[str, Any]
) -> bool:
    """Check recorded fragments without treating unrelated JSON edits as modifications."""
    if relative == CLAUDE_MCP_PATH:
        if ownership.get("server") is not True:
            return True
        servers = payload.get("mcpServers")
        return isinstance(servers, dict) and servers.get("smairt") == {
            "command": "smairt",
            "args": ["mcp", "serve"],
        }
    permissions = payload.get("permissions")
    deny = permissions.get("deny", []) if isinstance(permissions, dict) else []
    if not set(ownership.get("deny", [])).issubset(set(deny)):
        return False
    hooks = payload.get("hooks")
    if not isinstance(hooks, dict):
        return not ownership.get("hooks")
    return all(
        any(_is_claude_owned_hook(entry) for entry in hooks.get(event, []))
        for event in ownership.get("hooks", [])
    )


def _adapter(root: Path, name: HarnessName, *, enabled: bool | None = None) -> Adapter:
    """Render current project-scoped adapter files without embedding credentials."""
    base = ADAPTERS[name]
    files = dict(base.files)
    config = SmairtConfig.load(root / "smairt.yaml")
    is_enabled = name in config.integrations.mcp.enabled_harnesses if enabled is None else enabled
    if name is HarnessName.CODEX:
        content = 'model_instructions_file = "../AGENTS.md"\n'
        if is_enabled:
            content += (
                '\n[mcp_servers.smairt]\ncommand = "smairt"\nargs = ["mcp", "serve"]\n'
                f"enabled_tools = {json.dumps(MCP_TOOL_NAMES)}\n"
            )
        files[".codex/config.toml"] = content
        files[".codex/agents/smairt-reviewer.toml"] = (
            'name = "smairt-reviewer"\n'
            'description = "Challenge a bounded SMAIRT artifact without changing project state"\n'
            'sandbox_mode = "read-only"\n'
            'developer_instructions = """Review only the bounded packet supplied by the parent. '
            "Identify the strongest objection, unsupported assumptions, alternative explanations, "
            "missing controls, falsifiers, and provenance gaps. Return severity, confidence, and "
            'the smallest useful follow-up test. Never change files or approve decisions."""\n'
        )
        files[".codex/hooks/smairt-hook"] = CODEX_HOOK
        hook_command = '"$(git rev-parse --show-toplevel)/.codex/hooks/smairt-hook"'
        files[".codex/hooks.json"] = (
            json.dumps(
                {
                    "hooks": {
                        "SessionStart": [
                            {
                                "matcher": "startup|resume|compact",
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": f"{hook_command} SessionStart",
                                        "timeout": 30,
                                        "statusMessage": "SMAIRT · Loading research context",
                                    }
                                ],
                            }
                        ],
                        "PreToolUse": [
                            {
                                "matcher": "Bash|apply_patch|Edit|Write|mcp__.*",
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": f"{hook_command} PreToolUse",
                                        "timeout": 30,
                                        "statusMessage": "SMAIRT · Checking research boundary",
                                    }
                                ],
                            }
                        ],
                        "PreCompact": [
                            {
                                "matcher": "manual|auto",
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": f"{hook_command} PreCompact",
                                        "timeout": 30,
                                    }
                                ],
                            }
                        ],
                    }
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        return Adapter(name, files, frozenset({".codex/hooks/smairt-hook"}))
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
    elif name is HarnessName.CLINE and is_enabled:
        files[".cline/mcp.json"] = (
            json.dumps(
                {"mcpServers": {"smairt": {"command": "smairt", "args": ["mcp", "serve"]}}},
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
    elif name is HarnessName.OPENCODE:
        opencode_payload: dict[str, Any] = {
            "$schema": "https://opencode.ai/config.json",
            "instructions": ["AGENTS.md"],
            "permission": {
                "external_directory": "deny",
                "bash": {
                    "*": "ask",
                    "git status*": "allow",
                    "git diff*": "allow",
                    "smairt status*": "allow",
                    "smairt next*": "allow",
                    "smairt context*": "allow",
                    "smairt validate*": "allow",
                    "git reset --hard*": "deny",
                    "git clean -fd*": "deny",
                    "git push --force*": "deny",
                },
            },
        }
        if is_enabled:
            opencode_payload["mcp"] = {
                "smairt": {
                    "type": "local",
                    "command": ["smairt", "mcp", "serve"],
                    "enabled": True,
                }
            }
        files["opencode.json"] = json.dumps(opencode_payload, indent=2, sort_keys=False) + "\n"
    elif name is HarnessName.CURSOR:
        command = '"$(git rev-parse --show-toplevel)/.cursor/hooks/smairt-hook"'
        files[".cursor/hooks.json"] = (
            json.dumps(
                {
                    "version": 1,
                    "hooks": {
                        "sessionStart": [{"command": f"{command} sessionStart", "timeout": 30}],
                        "preToolUse": [
                            {
                                "command": f"{command} preToolUse",
                                "matcher": "Shell|Write|Edit|MCP",
                                "timeout": 30,
                                "failClosed": True,
                            }
                        ],
                        "preCompact": [{"command": f"{command} preCompact", "timeout": 30}],
                    },
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        if is_enabled:
            files[".cursor/mcp.json"] = (
                json.dumps(
                    {"mcpServers": {"smairt": {"command": "smairt", "args": ["mcp", "serve"]}}},
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )
    elif name is HarnessName.CLAUDE:
        prior_ownership = _prior_claude_ownership(root)
        settings, settings_ownership = _claude_settings(root, prior_ownership)
        json_ownership: dict[str, Any] = {CLAUDE_SETTINGS_PATH: settings_ownership}
        files[CLAUDE_SETTINGS_PATH] = json.dumps(settings, indent=2, sort_keys=True) + "\n"
        mcp_path = _managed_path(root, CLAUDE_MCP_PATH)
        prior_mcp = prior_ownership.get(CLAUDE_MCP_PATH, {})
        prior_mcp = prior_mcp if isinstance(prior_mcp, dict) else {}
        if is_enabled or prior_mcp.get("server") is True:
            mcp = _load_json_object(mcp_path, CLAUDE_MCP_PATH)
            servers = mcp.setdefault("mcpServers", {})
            if not isinstance(servers, dict):
                raise ValueError(".mcp.json mcpServers must be an object")
            owned_server = prior_mcp.get("server") is True
            desired_server = {"command": "smairt", "args": ["mcp", "serve"]}
            if is_enabled:
                existing_server = servers.get("smairt")
                if existing_server is None:
                    servers["smairt"] = desired_server
                    owned_server = True
                elif owned_server:
                    servers["smairt"] = desired_server
                else:
                    raise ValueError(".mcp.json already contains a researcher-owned smairt server")
            elif owned_server:
                servers.pop("smairt", None)
                owned_server = False
            if not servers:
                mcp.pop("mcpServers", None)
            files[CLAUDE_MCP_PATH] = json.dumps(mcp, indent=2, sort_keys=True) + "\n"
            json_ownership[CLAUDE_MCP_PATH] = {"server": owned_server}
        return Adapter(name, files, base.executable, base.merged_json, json_ownership)
    return Adapter(name, files, base.executable, base.merged_json)


CAPABILITIES: dict[str, dict[str, object]] = {
    "codex": {
        "rules": "advisory",
        "protected_operation_hook": "blocking_incomplete",
        "modes": "native",
        "context_restore": "session_and_compact_hooks",
        "skills": "native_project_skills",
        "commands": "$smairt-*",
        "reviewer": "native_read_only_subagent",
        "cross_model_review": "optional_native_override",
        "mcp": "read_only_opt_in",
        "configuration_notice": "project hooks and MCP require Codex project trust",
    },
    "zoo": {
        "rules": "advisory",
        "protected_operation_hook": "unsupported",
        "modes": "native_plus_smairt_review",
        "context_restore": "manual",
        "skills": "native_project_skills",
        "commands": "/smairt-*",
        "reviewer": "read_only_review_mode",
        "cross_model_review": "optional_sticky_mode_model",
        "mcp": "read_only_opt_in",
        "project_paths": ".roo, .roomodes, and .rooignore are intentionally Roo-compatible",
    },
    "cline": {
        "rules": "advisory",
        "protected_operation_hook": "blocking",
        "modes": "native_plan_act",
        "context_restore": "task_and_compact_hooks",
        "skills": "stable_workflows",
        "commands": "/smairt-*",
        "reviewer": "standard_read_only_subagent",
        "cross_model_review": "optional_agent_squad",
        "mcp": "read_only_opt_in",
    },
    "opencode": {
        "rules": "advisory",
        "protected_operation_hook": "permissions",
        "modes": "native_build_plan",
        "context_restore": "command",
        "skills": "canonical_skills_plus_commands",
        "commands": "/smairt-*",
        "reviewer": "native_read_only_subagent",
        "cross_model_review": "optional_native_override",
        "mcp": "read_only_opt_in",
        "configuration_notice": "executable OpenCode plugins are intentionally not installed",
    },
    "cursor": {
        "rules": "advisory",
        "protected_operation_hook": "blocking",
        "modes": "native_agent_ask",
        "context_restore": "session_and_compact_hooks",
        "skills": "native_project_skills",
        "commands": "/smairt-*",
        "reviewer": "native_read_only_subagent",
        "cross_model_review": "optional_native_override",
        "mcp": "read_only_opt_in",
        "configuration_notice": "project hooks must be enabled and trusted by Cursor",
    },
    "claude": {
        "rules": "advisory",
        "protected_operation_hook": "blocking",
        "modes": "native_plan",
        "context_restore": "session_and_compact_hooks",
        "skills": "native_project_skills",
        "commands": "/smairt-*",
        "reviewer": "native_read_only_plan_subagent",
        "cross_model_review": "optional_native_override",
        "mcp": "read_only_opt_in",
        "configuration_notice": "project hooks and MCP require Claude Code project trust",
    },
}

for _capabilities in CAPABILITIES.values():
    _capabilities["workflows"] = list(WORKFLOW_SLUGS)

HARNESS_BINARIES = {
    HarnessName.CODEX: ("codex",),
    HarnessName.ZOO: ("zoo",),
    HarnessName.CLINE: ("cline",),
    HarnessName.OPENCODE: ("opencode",),
    HarnessName.CURSOR: ("agent", "cursor-agent"),
    HarnessName.CLAUDE: ("claude",),
}


def _binary_status(name: HarnessName) -> dict[str, object]:
    """Inspect a local harness executable without contacting its provider."""
    candidates = HARNESS_BINARIES[name]
    executable = next((item for item in candidates if shutil.which(item)), candidates[0])
    path = shutil.which(executable)
    version = None
    if path:
        try:
            result = subprocess.run(
                [path, "--version"], capture_output=True, text=True, timeout=3, check=False
            )
            output = (result.stdout or result.stderr).strip()
            version = output.splitlines()[0] if output else None
        except (OSError, subprocess.TimeoutExpired):
            version = None
    return {"command": executable, "available": bool(path), "version": version}


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
    optional = {"merged_json", "json_ownership"}
    if not required.issubset(payload) or set(payload) - (required | optional):
        raise ValueError("harness manifest identity or fields are invalid")
    if payload.get("harness") != harness.value:
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
    merged = payload.get("merged_json", [])
    if not isinstance(merged, list) or not all(isinstance(item, str) for item in merged):
        raise ValueError("harness manifest merged JSON paths are invalid")
    ownership = payload.get("json_ownership", {})
    if not isinstance(ownership, dict):
        raise ValueError("harness manifest JSON ownership is invalid")
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
            merged_files = set(cast(list[str], manifest.get("merged_json", [])))
            json_ownership = cast(dict[str, Any], manifest.get("json_ownership", {}))
            for relative in _adapter(root, name).files:
                if relative not in declared_files:
                    missing.append(relative)
            for relative, digest in dict(manifest.get("files", {})).items():
                target = _managed_path(root, relative)
                if not target.exists():
                    missing.append(relative)
                elif relative in merged_files:
                    desired = _adapter(root, name).files.get(relative)
                    if desired is None:
                        missing.append(relative)
                    elif name is HarnessName.CLAUDE:
                        current = _load_json_object(target, relative)
                        owned = json_ownership.get(relative, {})
                        if not _claude_owned_present(
                            relative, current, owned if isinstance(owned, dict) else {}
                        ):
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
        "presentation": presentation_info(name),
        "active": config.harness.active == name,
        "installed": manifest is not None,
        "adapter_version": version,
        "adapter_supported": version == ADAPTER_VERSION if manifest else False,
        "capabilities": CAPABILITIES[name.value],
        "binary": _binary_status(name),
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
            else "Cursor project hooks require project trust"
            if name is HarnessName.CURSOR
            else "OpenCode uses permissions; executable plugins are not installed"
            if name is HarnessName.OPENCODE
            else "Zoo has no documented blocking protected-operation hook"
            if name is HarnessName.ZOO
            else "Claude Code project hooks and MCP require project trust"
            if name is HarnessName.CLAUDE
            else None
        ),
    }


def switch_plan(root: Path, harness: str) -> dict[str, Any]:
    """Preview a harness switch without changing project state."""
    target_name = HarnessName(harness)
    config = SmairtConfig.load(root / "smairt.yaml")
    current_name = config.harness.active
    current_manifest = _load_manifest(root, current_name) or {
        "files": {},
        "merged_json": [],
        "json_ownership": {},
    }
    target_manifest = _load_manifest(root, target_name) or {
        "files": {},
        "merged_json": [],
        "json_ownership": {},
    }
    current_files = dict(current_manifest.get("files", {}))
    known_target = dict(target_manifest.get("files", {}))
    target_files = _adapter(root, target_name).files
    current_merged = set(cast(list[str], current_manifest.get("merged_json", [])))
    target_merged = set(_adapter(root, target_name).merged_json)
    remove: list[str] = []
    remove_owned: list[str] = []
    modified: list[str] = []
    conflicts: list[str] = []
    preserve: list[str] = []
    for relative, digest in current_files.items():
        if relative in current_merged:
            if relative not in target_merged:
                remove_owned.append(relative)
            continue
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
        if relative in target_merged:
            continue
        if path.exists() and relative not in current_files:
            prior_digest = known_target.get(relative)
            if prior_digest is None or sha256_text(path.read_text()) != prior_digest:
                conflicts.append(relative)
    for directory in (
        ".codex",
        ".roo",
        ".cline",
        ".clinerules",
        ".opencode",
        ".cursor",
        ".claude",
    ):
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
        "remove_owned": sorted(remove_owned),
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
    config = SmairtConfig.load(root / "smairt.yaml")
    if target_name is HarnessName.CLAUDE and config.schema_version < 7:
        raise ValueError("Claude Code requires schema v7; run 'smairt migrate apply'")
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
    for relative in plan.get("remove_owned", []):
        path = _managed_path(root, relative)
        if not path.exists():
            continue
        payload = _load_json_object(path, relative)
        source_manifest = _load_manifest(root, HarnessName(str(plan["from"]))) or {}
        ownership_map = source_manifest.get("json_ownership", {})
        ownership_map = ownership_map if isinstance(ownership_map, dict) else {}
        ownership = ownership_map.get(relative, {})
        preserved = _strip_claude_owned(
            relative, payload, ownership if isinstance(ownership, dict) else {}
        )
        if preserved:
            transaction.stage_text(path, json.dumps(preserved, indent=2, sort_keys=True) + "\n")
        else:
            transaction.stage_delete(path)
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
        "merged_json": sorted(adapter.merged_json & set(adapter.files)),
        "json_ownership": adapter.json_ownership,
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


def list_harnesses(root: Path | None = None) -> list[dict[str, object]]:
    """Return chooser metadata everywhere and project status when a project is available."""
    if root is None:
        return [
            {
                **presentation_info(name),
                "active": None,
                "installed": None,
                "binary": _binary_status(name),
                "capabilities": CAPABILITIES[name.value],
            }
            for name in HarnessName
        ]
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
    """Transactionally toggle read-only MCP for the active maintained adapter."""
    config = SmairtConfig.load(root / "smairt.yaml")
    if config.schema_version < 4:
        raise ValueError("MCP settings require schema v4; run 'smairt migrate apply'")
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
    merged_files = set(cast(list[str], manifest.get("merged_json", [])))
    for relative, digest in dict(manifest["files"]).items():
        path = _managed_path(root, relative)
        if path.exists() and sha256_text(path.read_text()) != digest:
            if relative in merged_files:
                continue
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
        unowned_claude_mcp = (
            harness is HarnessName.CLAUDE
            and not enabled
            and relative == CLAUDE_MCP_PATH
            and next_adapter.json_ownership.get(CLAUDE_MCP_PATH, {}).get("server") is not True
        )
        if unowned_claude_mcp:
            continue
        hashes[relative] = sha256_text(content)
    tracked_files = set(hashes)
    next_manifest = {
        "harness": harness.value,
        "version": ADAPTER_VERSION,
        "activated_at": manifest["activated_at"],
        "files": hashes,
        "merged_json": sorted(next_adapter.merged_json & tracked_files),
        "json_ownership": {
            relative: ownership
            for relative, ownership in next_adapter.json_ownership.items()
            if relative in tracked_files
        },
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
