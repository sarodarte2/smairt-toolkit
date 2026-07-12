"""Project discovery, status, context selection, and policy validation."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from smairt.models import SmairtConfig

PROHIBITED_SUFFIXES = {
    ".fast5",
    ".pod5",
    ".fastq",
    ".fq",
    ".bam",
    ".cram",
    ".pem",
    ".key",
    ".p12",
}
PROHIBITED_NAMES = {".env", "credentials.json", "secrets.json", "secrets.yaml"}


def find_project(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "smairt.yaml").exists():
            return candidate
    raise FileNotFoundError("No smairt.yaml found in this directory or its parents")


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checks: dict[str, bool] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "checks": self.checks,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def _git_files(root: Path, staged: bool) -> list[str]:
    command = ["git", "diff", "--cached", "--name-only"] if staged else ["git", "ls-files"]
    result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    return result.stdout.splitlines() if result.returncode == 0 else []


def is_prohibited(relative: str) -> bool:
    path = Path(relative)
    lower = relative.lower()
    return (
        path.name.lower() in PROHIBITED_NAMES
        or path.suffix.lower() in PROHIBITED_SUFFIXES
        or lower.startswith("references/pdfs/")
        or lower.startswith("data/raw/")
        or lower.startswith("data/local/")
        or path.name.lower().startswith("credentials")
        or path.name.lower().startswith("secrets")
    )


def validate_project(
    root: Path, *, staged: bool = False, tool_input: bool = False
) -> ValidationReport:
    report = ValidationReport()
    try:
        config = SmairtConfig.load(root / "smairt.yaml")
        report.checks["project_contract"] = True
    except Exception as exc:
        report.errors.append(f"Invalid project contract: {exc}")
        report.checks["project_contract"] = False
        return report

    required = ["AGENTS.md", "references/index.yaml", "prompts/CODE_CONVENTIONS.md"]
    missing = [item for item in required if not (root / item).exists()]
    report.checks["required_files"] = not missing
    if missing:
        report.errors.append(f"Missing required files: {', '.join(missing)}")

    if config.git.enabled and (root / ".git").exists():
        prohibited = [item for item in _git_files(root, staged) if is_prohibited(item)]
        report.checks["git_safety"] = not prohibited
        if prohibited:
            report.errors.append(f"Protected files are tracked/staged: {', '.join(prohibited)}")
    else:
        report.checks["git_safety"] = True

    try:
        references = json.loads("{}")
        import yaml

        references = yaml.safe_load((root / "references/index.yaml").read_text()) or {}
        report.checks["reference_index"] = isinstance(references.get("references"), list)
        if not report.checks["reference_index"]:
            report.errors.append("references/index.yaml must contain a references list")
    except Exception as exc:
        report.checks["reference_index"] = False
        report.errors.append(f"Invalid reference index: {exc}")

    if not config.project.question:
        report.warnings.append("Initial research question is not specified")
    if config.data.classification.value == "controlled":
        report.warnings.append("Controlled-data storage enforcement is not implemented in v1")

    if tool_input and not sys.stdin.isatty():
        payload = sys.stdin.read()
        if any(token in payload.lower() for token in ("data/raw/", ".fast5", ".env", "api_key")):
            report.errors.append("Codex tool input may access protected data or secrets")
    return report


def status(root: Path) -> dict[str, object]:
    config = SmairtConfig.load(root / "smairt.yaml")
    report = validate_project(root)
    proposals = sorted((root / "hypotheses/proposals").glob("PROPOSAL_SET_*.md"))
    hypotheses = [
        path
        for path in sorted((root / "hypotheses").glob("HYPOTHESIS_*.md"))
        if path.name != "HYPOTHESIS_TEMPLATE.md"
    ]
    experiments = sorted((root / "experiments").glob("EXPERIMENT_*"))
    return {
        "project": config.project.model_dump(mode="json"),
        "data_classification": config.data.classification.value,
        "environment": config.environment.model_dump(mode="json", exclude_none=True),
        "active": config.active.model_dump(mode="json", exclude_none=True),
        "counts": {
            "proposal_sets": len(proposals),
            "hypotheses": len(hypotheses),
            "experiments": len(experiments),
        },
        "validation": report.as_dict(),
    }


CONTEXT_MAP = {
    "planning": [
        "prompts/RESEARCH_CONVENTIONS.md",
        "plans/README.md",
        "background/initial_background.md",
    ],
    "code": [
        "prompts/CODE_CONVENTIONS.md",
        "prompts/KNOWN_PATTERNS.md",
    ],
    "run": [
        "prompts/CODE_CONVENTIONS.md",
        "prompts/RESEARCH_CONVENTIONS.md",
    ],
    "interpretation": [
        "prompts/INTERPRETATION_CONVENTIONS.md",
        "prompts/intellectual_contribution.md",
    ],
    "paper": [
        "paper/README.md",
        "paper/manifest.yaml",
        "prompts/INTERPRETATION_CONVENTIONS.md",
    ],
}


def context(root: Path, task: str) -> dict[str, object]:
    if task not in CONTEXT_MAP:
        raise ValueError(f"Unknown task {task!r}; choose {', '.join(CONTEXT_MAP)}")
    current = status(root)
    return {
        "task": task,
        "status": current,
        "read": [path for path in CONTEXT_MAP[task] if (root / path).exists()],
        "rule": "Read only these files initially; load logs, PDFs, and older iterations on demand.",
    }
