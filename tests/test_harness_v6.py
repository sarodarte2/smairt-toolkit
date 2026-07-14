"""Responsive terminal and five-harness adapter contracts."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import Mock

from rich.console import Console

from smairt.harnesses import configure_mcp, harness_status, select_harness
from smairt.hook_policy import hook_response, parse_hook_payload, policy_denial
from smairt.models import DataClassification, HarnessName
from smairt.scaffold import create_project


def project(tmp_path: Path) -> Path:
    root = tmp_path / "five-harnesses"
    create_project(
        root,
        name="Five Harnesses",
        author="Researcher",
        classification=DataClassification.UNPUBLISHED,
        initialize_git=False,
        confirm_contributor=True,
    )
    return root


def test_opencode_and_cursor_adapters_are_hardened_and_mcp_capable(tmp_path: Path) -> None:
    root = project(tmp_path)
    select_harness(root, "opencode")
    opencode = json.loads((root / "opencode.json").read_text())
    assert opencode["permission"]["external_directory"] == "deny"
    assert opencode["permission"]["bash"]["git push --force*"] == "deny"
    assert not (root / ".opencode/plugins").exists()
    configure_mcp(root, HarnessName.OPENCODE, True)
    assert json.loads((root / "opencode.json").read_text())["mcp"]["smairt"]["enabled"]

    select_harness(root, "cursor")
    hooks = json.loads((root / ".cursor/hooks.json").read_text())
    assert hooks["hooks"]["preToolUse"][0]["failClosed"] is True
    assert (root / ".cursor/hooks/smairt-hook").stat().st_mode & 0o111
    configure_mcp(root, HarnessName.CURSOR, True)
    assert "smairt" in json.loads((root / ".cursor/mcp.json").read_text())["mcpServers"]
    assert harness_status(root)["capabilities"]["protected_operation_hook"] == "blocking"


def test_all_harnesses_have_truthful_capability_records(tmp_path: Path) -> None:
    root = project(tmp_path)
    for harness in HarnessName:
        result = select_harness(root, harness.value)
        assert result["harness"] == harness.value
        assert "protected_operation_hook" in result["capabilities"]
        assert configure_mcp(root, harness, True)["enabled"] is True
    assert harness_status(root, "zoo")["capabilities"]["protected_operation_hook"] == "unsupported"


def test_hook_policy_bounds_and_denies_protected_or_human_gate_operations(tmp_path: Path) -> None:
    root = project(tmp_path)
    payload = parse_hook_payload(b'{"tool_name":"Bash","tool_input":{"command":"git status"}}')
    assert policy_denial(payload) is None
    protected = {"tool_name": "apply_patch", "tool_input": {"command": "data/raw/x.fast5"}}
    assert "Protected" in str(policy_denial(protected))
    human = {
        "tool_name": "Bash",
        "tool_input": {"command": "smairt decision record --decision ACCEPT"},
    }
    codex = hook_response(root, "codex", "PreToolUse", human)
    assert codex["hookSpecificOutput"]["permissionDecision"] == "deny"
    cline = hook_response(root, "cline", "PreToolUse", human)
    assert cline["cancel"] is True


def test_responsive_header_uses_compact_and_wide_branding(monkeypatch) -> None:
    from smairt import tui

    monkeypatch.setenv("SMAIRT_REDUCED_MOTION", "1")
    narrow_buffer = io.StringIO()
    narrow = Console(file=narrow_buffer, width=50, height=14, force_terminal=False)
    monkeypatch.setattr(tui, "console", narrow)
    tui._header("Project", "Health and next step")
    assert "◆ SMAIRT · Project" in narrow_buffer.getvalue()

    wide_buffer = io.StringIO()
    wide = Console(file=wide_buffer, width=130, height=40, force_terminal=True)
    wide.clear = Mock()  # type: ignore[method-assign]
    monkeypatch.setattr(tui, "console", wide)
    tui._header("Project", "Health and next step")
    tui._header("References", "Metadata and PDFs")
    assert wide.clear.call_count == 2
    assert "Scientific Method" in wide_buffer.getvalue()
