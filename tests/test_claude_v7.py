"""Claude Code adapter, schema-v7 migration, and shared JSON ownership tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from smairt.harnesses import configure_mcp, select_harness
from smairt.migrations import apply_migration, migration_plan
from smairt.models import DataClassification, HarnessName, SmairtConfig
from smairt.scaffold import create_project
from smairt.workflows import WORKFLOW_SLUGS


def project(tmp_path: Path) -> Path:
    root = tmp_path / "claude-v7"
    create_project(
        root,
        name="Claude v7",
        author="Researcher",
        classification=DataClassification.UNPUBLISHED,
        initialize_git=False,
        confirm_contributor=True,
    )
    return root


def test_claude_adapter_generates_restricted_project_surfaces(tmp_path: Path) -> None:
    root = project(tmp_path)
    select_harness(root, "claude")
    assert "@../AGENTS.md" in (root / ".claude/CLAUDE.md").read_text()
    assert (root / ".claude/hooks/smairt-hook").stat().st_mode & 0o111
    reviewer = (root / ".claude/agents/smairt-reviewer.md").read_text()
    assert "tools: Read, Grep, Glob" in reviewer
    assert "permissionMode: plan" in reviewer
    for slug in WORKFLOW_SLUGS:
        skill = (root / f".claude/skills/{slug}/SKILL.md").read_text()
        assert "disable-model-invocation: true" in skill
    settings = json.loads((root / ".claude/settings.json").read_text())
    assert settings["permissions"]["deny"]
    assert set(settings["hooks"]) == {"SessionStart", "PreToolUse", "PreCompact"}


def test_claude_preserves_custom_settings_and_mcp_servers(tmp_path: Path) -> None:
    root = project(tmp_path)
    (root / ".claude").mkdir(exist_ok=True)
    (root / ".claude/settings.json").write_text(
        json.dumps({"model": "sonnet", "hooks": {"Stop": [{"hooks": []}]}})
    )
    (root / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"researcher": {"command": "custom"}}})
    )
    select_harness(root, "claude")
    configure_mcp(root, HarnessName.CLAUDE, True)
    assert json.loads((root / ".claude/settings.json").read_text())["model"] == "sonnet"
    servers = json.loads((root / ".mcp.json").read_text())["mcpServers"]
    assert set(servers) == {"researcher", "smairt"}

    configure_mcp(root, HarnessName.CLAUDE, False)
    assert json.loads((root / ".mcp.json").read_text())["mcpServers"] == {
        "researcher": {"command": "custom"}
    }
    manifest = json.loads((root / ".smairt/harnesses/claude.json").read_text())
    assert ".mcp.json" not in manifest["files"]
    configure_mcp(root, HarnessName.CLAUDE, True)

    select_harness(root, "codex")
    settings = json.loads((root / ".claude/settings.json").read_text())
    assert settings == {"model": "sonnet", "hooks": {"Stop": [{"hooks": []}]}}
    assert json.loads((root / ".mcp.json").read_text())["mcpServers"] == {
        "researcher": {"command": "custom"}
    }


def test_v6_migrates_to_v7_and_claude_requires_v7(tmp_path: Path) -> None:
    root = project(tmp_path)
    config = SmairtConfig.load(root / "smairt.yaml")
    config.schema_version = 6
    (root / "smairt.yaml").write_text(config.to_yaml())
    with pytest.raises(ValueError, match="schema v7"):
        select_harness(root, "claude")
    assert migration_plan(root)["to_version"] == 7
    applied = apply_migration(root)
    assert applied["to_version"] == 7
    assert SmairtConfig.load(root / "smairt.yaml").schema_version == 7


def test_claude_does_not_claim_preexisting_matching_fragments(tmp_path: Path) -> None:
    root = project(tmp_path)
    (root / ".claude").mkdir(exist_ok=True)
    preexisting_hook = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/smairt-hook PreToolUse",
            }
        ],
    }
    (root / ".claude/settings.json").write_text(
        json.dumps(
            {
                "permissions": {"deny": ["Read(./.env*)"]},
                "hooks": {"PreToolUse": [preexisting_hook]},
            }
        )
    )
    original_mcp = '{ "mcpServers": { "smairt": { "command": "researcher-command" } } }\n'
    (root / ".mcp.json").write_text(original_mcp)
    select_harness(root, "claude")
    select_harness(root, "codex")
    settings = json.loads((root / ".claude/settings.json").read_text())
    assert settings == {
        "permissions": {"deny": ["Read(./.env*)"]},
        "hooks": {"PreToolUse": [preexisting_hook]},
    }
    assert (root / ".mcp.json").read_text() == original_mcp
