"""Human-facing descriptions for choosing and understanding coding harnesses."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from smairt.models import HarnessName


@dataclass(frozen=True)
class HarnessPresentation:
    """Describe one maintained adapter without overstating its runtime guarantees."""

    display_name: str
    tagline: str
    best_for: str
    orientation: str
    invocation: str
    safety: str
    reviewer: str
    setup: str
    limitation: str
    guide: str

    def as_dict(self) -> dict[str, str]:
        """Return a stable JSON-friendly representation."""
        return asdict(self)


HARNESS_PRESENTATIONS: dict[HarnessName, HarnessPresentation] = {
    HarnessName.CODEX: HarnessPresentation(
        display_name="Codex",
        tagline="Terminal-first OpenAI agents with project skills and custom reviewers",
        best_for="Researchers who want a strong terminal workflow and native Codex delegation",
        orientation="Terminal and Codex app",
        invocation="$smairt-next and other $smairt-* skills",
        safety="Project hooks plus authoritative SMAIRT CLI and integrity gates",
        reviewer="Native read-only project subagent; model override is optional",
        setup="Trust the project and review project hooks before enabling them",
        limitation="Hook coverage depends on project trust and does not replace CLI gates",
        guide="docs/harnesses/codex.md",
    ),
    HarnessName.ZOO: HarnessPresentation(
        display_name="Zoo Code",
        tagline="Mode-centric planning and orchestration with a dedicated review mode",
        best_for="Researchers who prefer visible roles, modes, and delegated task orchestration",
        orientation="Editor extension with native modes",
        invocation="/smairt-next and other /smairt-* skills",
        safety="Rules, read-only mode boundaries, and authoritative SMAIRT CLI gates",
        reviewer="SMAIRT Evidence Review mode with an optional sticky reviewer model",
        setup="Review the generated .roo rules, mode, ignore, and MCP configuration",
        limitation="No documented blocking protected-operation hook",
        guide="docs/harnesses/zoo-code.md",
    ),
    HarnessName.CLINE: HarnessPresentation(
        display_name="Cline",
        tagline="Plan/Act research workflows with lifecycle hooks and read-only subagents",
        best_for="Researchers who want explicit planning, approval, and execution transitions",
        orientation="VS Code-compatible editor extension",
        invocation="/smairt-next and other .cline workflow commands",
        safety="Blocking PreToolUse hook when Cline hooks are enabled",
        reviewer=(
            "Standard isolated read-only subagent; Agent Squad is optional for cross-model review"
        ),
        setup="Enable Cline hooks and review the generated workflow and ignore files",
        limitation="A distinct reviewer model requires the advanced Agent Squad path",
        guide="docs/harnesses/cline.md",
    ),
    HarnessName.OPENCODE: HarnessPresentation(
        display_name="OpenCode",
        tagline="Provider-flexible terminal agents with explicit permissions and commands",
        best_for="Researchers who prefer an open terminal workflow and provider flexibility",
        orientation="Terminal-first",
        invocation="/smairt-next and other .opencode commands",
        safety="Project permissions plus authoritative SMAIRT CLI and integrity gates",
        reviewer="Native read-only subagent; model override is optional",
        setup="Review opencode.json permissions and opt in to the read-only MCP if needed",
        limitation="SMAIRT intentionally does not install executable project plugins",
        guide="docs/harnesses/opencode.md",
    ),
    HarnessName.CURSOR: HarnessPresentation(
        display_name="Cursor",
        tagline="IDE-native skills, rules, hooks, and read-only project subagents",
        best_for="Researchers who want SMAIRT guidance embedded in an editor-first workflow",
        orientation="Cursor IDE and Cursor CLI",
        invocation="/smairt-next and other /smairt-* project skills",
        safety="Project hooks, CLI permissions, and authoritative SMAIRT gates",
        reviewer="Native read-only project subagent; model override is optional",
        setup="Trust the project, enable hooks, and review Cursor CLI permissions",
        limitation="Hook enforcement remains controlled by Cursor trust and settings",
        guide="docs/harnesses/cursor.md",
    ),
    HarnessName.CLAUDE: HarnessPresentation(
        display_name="Claude Code",
        tagline="Terminal-native Claude workflows with project skills, hooks, and subagents",
        best_for="Researchers who use Claude Code and want SMAIRT-aware project automation",
        orientation="Terminal-first",
        invocation="/smairt-next and other project skills",
        safety="Project hooks plus authoritative SMAIRT CLI and integrity gates",
        reviewer="Read-only plan-mode project subagent",
        setup="Trust the project and review Claude hooks and MCP configuration",
        limitation="Hooks and MCP remain subject to Claude Code project trust",
        guide="docs/harnesses/claude-code.md",
    ),
}


def harness_info(name: HarnessName | str) -> dict[str, str]:
    """Return the maintained chooser metadata for one harness."""
    harness = name if isinstance(name, HarnessName) else HarnessName(name)
    return {"harness": harness.value, **HARNESS_PRESENTATIONS[harness].as_dict()}
