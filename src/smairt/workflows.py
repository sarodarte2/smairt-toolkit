"""Define the portable SMAIRT workflows rendered into coding-harness adapters."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkflowDefinition:
    """Describe one researcher-facing workflow without binding it to a harness."""

    slug: str
    title: str
    description: str
    context_task: str
    actions: tuple[str, ...]
    human_gate: str
    result: str
    manual_only: bool = False


WORKFLOWS = (
    WorkflowDefinition(
        "smairt-next",
        "Next Research Step",
        "Orient to the current SMAIRT stage and recommend a bounded next action.",
        "planning",
        (
            "Run `smairt status --json` and `smairt next --json`.",
            "Load only the context named by the recommended action.",
            "Explain the recommendation, why it is timely, and up to three safe alternatives.",
        ),
        "Do not cross a scientific decision gate merely because it is recommended.",
        "Finish with what is ready now, the recommended action, and relevant alternatives.",
    ),
    WorkflowDefinition(
        "smairt-literature",
        "Literature and References",
        "Search, import, inspect, or synthesize references with visible provenance.",
        "planning",
        (
            "Inspect the reference index and current background before searching broadly.",
            "Use DOI-first metadata and read-only integrations; distinguish Crossref, OpenAlex, "
            "Zotero, and local PDF effects.",
            "Report every created or updated reference artifact and any unresolved metadata gap.",
        ),
        "Never copy a local PDF, contact a remote service, or accept a synthesis without the "
        "required confirmation.",
        "Finish with imported sources, visible project changes, limitations, and the next "
        "synthesis step.",
    ),
    WorkflowDefinition(
        "smairt-design",
        "Hypotheses and Experiment Design",
        "Develop competing hypotheses and experiment options without selecting for the researcher.",
        "planning",
        (
            "Ground options in the indexed background and current evidence gaps.",
            "Present scientifically distinct options with predictions, controls, falsifiers, and "
            "feasibility tradeoffs.",
            "Offer to open the relevant proposal or experiment artifact before a decision.",
        ),
        "The researcher selects hypotheses, experimental routes, controls, and consequential "
        "method changes.",
        "Finish with the options, their tradeoffs, and the exact human choice required.",
    ),
    WorkflowDefinition(
        "smairt-challenge",
        "Adversarial Review",
        "Challenge a bounded research artifact in an isolated read-only review context.",
        "review",
        (
            "Build a bounded packet with `smairt context --task review --json` and an optional "
            "`--target`.",
            "Use the harness's read-only reviewer or review mode; do not edit project files.",
            "Identify the strongest objection, unsupported assumptions, alternatives, missing "
            "controls, falsifiers, and provenance gaps.",
        ),
        "The reviewer advises only; the researcher decides whether any finding changes the "
        "project.",
        "Return severity, confidence, evidence gaps, and the smallest useful follow-up test.",
        manual_only=True,
    ),
    WorkflowDefinition(
        "smairt-interpret",
        "Interpret Results",
        "Separate observations from inference and propose evidence without silently accepting it.",
        "interpretation",
        (
            "Load the active iteration, immutable run record, and relevant accepted context.",
            "Separate observed results, inference, alternative explanations, limitations, and "
            "evidence gaps.",
            "Propose the appropriate evidence decision and explain what would falsify the "
            "interpretation.",
        ),
        "Only the researcher accepts a run as evidence or records a scientific decision.",
        "Finish with observations, interpretation, uncertainty, and the pending decision.",
    ),
    WorkflowDefinition(
        "smairt-paper",
        "Paper and Claims",
        "Draft professional manuscript text from approved claims and current evidence.",
        "paper",
        (
            "Load only current accepted evidence, approved claims, verified references, and the "
            "requested manuscript section.",
            "Keep source-backed claims, inference, limitations, and evidence gaps visibly "
            "distinct.",
            "Treat Markdown as canonical and DOCX as a reviewed export artifact.",
        ),
        "The researcher approves claims, manuscript sections, contribution statements, and "
        "publication actions.",
        "Finish with drafted text, supporting claim IDs, unresolved gaps, and the next review "
        "gate.",
    ),
)


def _skill_markdown(workflow: WorkflowDefinition) -> str:
    """Render one portable Agent Skill with a consistent, compact information hierarchy."""
    manual = "disable-model-invocation: true\n" if workflow.manual_only else ""
    actions = "\n".join(f"{index}. {action}" for index, action in enumerate(workflow.actions, 1))
    return (
        "---\n"
        f"name: {workflow.slug}\n"
        f'description: "{workflow.description}"\n'
        f"{manual}"
        "---\n\n"
        f"# SMAIRT · {workflow.title}\n\n"
        f"## Purpose\n\n{workflow.description}\n\n"
        "## Start here\n\n"
        "Run `smairt status --json` and `smairt next --json`, then load only the bounded context "
        f"returned by `smairt context --task {workflow.context_task}`.\n\n"
        f"## Actions\n\n{actions}\n\n"
        f"## Human decision boundary\n\n{workflow.human_gate}\n\n"
        f"## Finish with\n\n{workflow.result}\n"
    )


def shared_skill_files() -> dict[str, str]:
    """Return the six canonical project skills shared by compatible harnesses."""
    rendered: dict[str, str] = {}
    for workflow in WORKFLOWS:
        base = f".agents/skills/{workflow.slug}"
        rendered[f"{base}/SKILL.md"] = _skill_markdown(workflow)
        policy = "\npolicy:\n  allow_implicit_invocation: false" if workflow.manual_only else ""
        rendered[f"{base}/agents/openai.yaml"] = (
            "interface:\n"
            f'  display_name: "SMAIRT · {workflow.title}"\n'
            f'  short_description: "{workflow.description}"\n'
            f'  default_prompt: "Use ${workflow.slug} for this SMAIRT project."'
            f"{policy}\n"
        )
    return rendered


def cline_workflow_files() -> dict[str, str]:
    """Render stable Cline slash workflows with Plan/Act-aware handoffs."""
    files: dict[str, str] = {}
    for workflow in WORKFLOWS:
        actions = "\n".join(
            f"{index}. {action}" for index, action in enumerate(workflow.actions, 1)
        )
        files[f".cline/workflows/{workflow.slug}.md"] = (
            f"# SMAIRT · {workflow.title}\n\n"
            f"**Purpose:** {workflow.description}\n\n"
            "## Plan\n\n"
            f"{actions}\n\n"
            "## Act boundary\n\n"
            f"{workflow.human_gate}\n\n"
            f"**Return:** {workflow.result}\n"
        )
    return files


def opencode_command_files() -> dict[str, str]:
    """Render OpenCode commands that delegate to the canonical skill contract."""
    return {
        f".opencode/commands/{workflow.slug}.md": (
            "---\n"
            f"description: {workflow.description}\n"
            "---\n\n"
            f"# SMAIRT · {workflow.title}\n\n"
            f"Load `.agents/skills/{workflow.slug}/SKILL.md` and follow it exactly. "
            "Keep project mutations behind SMAIRT commands and human gates.\n"
        )
        for workflow in WORKFLOWS
    }


def claude_skill_files() -> dict[str, str]:
    """Render Claude Code project skills with explicit researcher invocation."""
    files: dict[str, str] = {}
    for workflow in WORKFLOWS:
        content = _skill_markdown(workflow)
        if "disable-model-invocation:" not in content:
            content = content.replace("---\n\n", "disable-model-invocation: true\n---\n\n", 1)
        files[f".claude/skills/{workflow.slug}/SKILL.md"] = content
    return files


WORKFLOW_SLUGS = tuple(workflow.slug for workflow in WORKFLOWS)
