"""Managed portable coding-harness adapters."""

from __future__ import annotations

import json
from pathlib import Path

from smairt.utils import sha256_text

COMMON = """# SMAIRT managed rules

- Treat `smairt.yaml` and portable records as authoritative scientific state.
- Run `smairt status --json`, `smairt next --json`, and task-scoped `smairt context` first.
- Never choose hypotheses, approve claims, or attribute contributors without the researcher.
- Never read or stage secrets, raw protected data, ignored PDFs, or protected local summaries.
- Use subagents only for independent read-only exploration and evidence gathering.
- Validate artifacts and run `smairt verify` before reporting completion.
"""

ZOO_FILES = {
    ".roo/rules/01-smairt.md": COMMON,
    ".roo/rules-architect/01-research-planning.md": (
        "# Research planning\nPresent scientific choices to the human.\n"
    ),
    ".roo/rules-code/01-research-code.md": (
        "# Research code\nUse SMAIRT iterations and immutable runs.\n"
    ),
    ".roo/rules-ask/01-research-review.md": (
        "# Research review\nRemain read-only; distinguish evidence and inference.\n"
    ),
    ".roo/rules-debug/01-run-integrity.md": (
        "# Debugging\nPreserve failures; use a new iteration when methods change.\n"
    ),
    ".roo/rules-orchestrator/01-delegation.md": (
        "# Orchestration\nDelegate only independent tasks. Require source paths, findings, "
        "uncertainty, and recommended files in every handoff.\n"
    ),
    ".rooignore": ".env*\nreferences/pdfs/**\ndata/raw/**\ndata/local/**\n.smairt/local/**\n",
}

CLINE_FILES = {
    ".clinerules/01-smairt.md": COMMON,
    ".clinerules/research-code.md": (
        '---\npaths:\n  - "experiments/**"\n  - "scripts/**"\n---\n'
        "# Research code\nUse a new iteration for meaningful method changes.\n"
    ),
    ".clinerules/paper.md": (
        '---\npaths:\n  - "paper/**"\n---\n# Paper workflow\n'
        "Draft only from approved claims, current evidence, and verified references.\n"
    ),
    ".clineignore": ".env*\nreferences/pdfs/**\ndata/raw/**\ndata/local/**\n.smairt/local/**\n",
    ".cline/workflows/smairt-next.md": (
        "# Continue SMAIRT research\n1. Run `smairt status --json`.\n"
        "2. Run `smairt next --json`.\n3. Load only task-scoped context.\n"
        "4. Stop at human scientific gates.\n"
    ),
}

ADAPTERS = {"codex": {}, "zoo": ZOO_FILES, "cline": CLINE_FILES}


def _manifest_path(root: Path, harness: str) -> Path:
    return root / ".smairt/harnesses" / f"{harness}.json"


def harness_status(root: Path, harness: str) -> dict[str, object]:
    if harness not in ADAPTERS:
        raise ValueError(f"unknown harness: {harness}")
    manifest_path = _manifest_path(root, harness)
    if harness == "codex":
        return {"harness": harness, "installed": (root / "AGENTS.md").exists(), "managed": False}
    if not manifest_path.exists():
        return {"harness": harness, "installed": False, "managed": True, "modified": []}
    manifest = json.loads(manifest_path.read_text())
    modified = []
    for relative, digest in manifest["files"].items():
        target = root / relative
        if not target.exists() or sha256_text(target.read_text()) != digest:
            modified.append(relative)
    return {
        "harness": harness,
        "installed": True,
        "managed": True,
        "version": manifest["version"],
        "modified": modified,
    }


def install_harness(root: Path, harness: str, *, upgrade: bool = False) -> dict[str, object]:
    if harness == "codex":
        return harness_status(root, harness)
    if harness not in ADAPTERS:
        raise ValueError(f"unknown harness: {harness}")
    current = harness_status(root, harness)
    if current["installed"] and not upgrade:
        raise ValueError(f"{harness} adapter is already installed")
    if current.get("modified"):
        raise ValueError("locally modified managed files: " + ", ".join(current["modified"]))
    hashes = {}
    for relative, content in ADAPTERS[harness].items():
        target = root / relative
        if not current["installed"] and target.exists():
            raise ValueError(f"refusing to overwrite existing file: {relative}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        hashes[relative] = sha256_text(content)
    manifest = {"harness": harness, "version": 1, "files": hashes}
    manifest_path = _manifest_path(root, harness)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return harness_status(root, harness)


def list_harnesses(root: Path) -> list[dict[str, object]]:
    return [harness_status(root, name) for name in ADAPTERS]
