"""Project discovery, status, context selection, and policy validation."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from smairt.code_quality import validate_code
from smairt.models import Decision, RunRecord, SmairtConfig

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
    """Walk upward from a path until the nearest smairt.yaml contract is found."""
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "smairt.yaml").exists():
            return candidate
    raise FileNotFoundError("No smairt.yaml found in this directory or its parents")


@dataclass
class ValidationReport:
    """Collect compatibility fields and structured findings from project checks."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checks: dict[str, bool] = field(default_factory=dict)
    findings: list[dict[str, str]] = field(default_factory=list)
    readiness: dict[str, bool] = field(default_factory=dict)

    def add(self, severity: str, code: str, artifact: str, message: str) -> None:
        """Add one finding and mirror it into legacy error or warning lists."""
        finding = {"severity": severity, "code": code, "artifact": artifact, "message": message}
        self.findings.append(finding)
        (self.errors if severity == "error" else self.warnings).append(message)

    @property
    def ok(self) -> bool:
        """Return true when no error-severity finding prevents safe progress."""
        return not self.errors

    def as_dict(self) -> dict[str, object]:
        """Convert the report into the stable JSON-facing validation contract."""
        return {
            "ok": self.ok,
            "checks": self.checks,
            "errors": self.errors,
            "warnings": self.warnings,
            "findings": self.findings,
            "readiness": self.readiness,
        }


def _git_files(root: Path, staged: bool) -> list[str]:
    """List either tracked or staged paths without mutating the repository."""
    command = ["git", "diff", "--cached", "--name-only"] if staged else ["git", "ls-files"]
    result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    return result.stdout.splitlines() if result.returncode == 0 else []


def is_prohibited(relative: str) -> bool:
    """Return whether a repository path violates generated data-safety policy."""
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
    """Validate project structure, safety, research links, code, and paper provenance."""
    report = ValidationReport()
    try:
        config = SmairtConfig.load(root / "smairt.yaml")
        report.checks["project_contract"] = True
    except Exception as exc:
        report.add("error", "project.contract", "smairt.yaml", f"Invalid project contract: {exc}")
        report.checks["project_contract"] = False
        return report

    required = ["AGENTS.md", "references/index.yaml", "prompts/CODE_CONVENTIONS.md"]
    missing = [item for item in required if not (root / item).exists()]
    report.checks["required_files"] = not missing
    if missing:
        report.add(
            "error", "project.required_files", ".", f"Missing required files: {', '.join(missing)}"
        )

    if config.git.enabled and (root / ".git").exists():
        prohibited = [item for item in _git_files(root, staged) if is_prohibited(item)]
        report.checks["git_safety"] = not prohibited
        if prohibited:
            report.add(
                "error",
                "git.protected",
                ".git",
                f"Protected files are tracked/staged: {', '.join(prohibited)}",
            )
    else:
        report.checks["git_safety"] = True

    try:
        references = json.loads("{}")
        references = yaml.safe_load((root / "references/index.yaml").read_text()) or {}
        report.checks["reference_index"] = isinstance(references.get("references"), list)
        if not report.checks["reference_index"]:
            report.add(
                "error",
                "references.schema",
                "references/index.yaml",
                "references/index.yaml must contain a references list",
            )
    except Exception as exc:
        report.checks["reference_index"] = False
        report.add(
            "error", "references.parse", "references/index.yaml", f"Invalid reference index: {exc}"
        )

    for finding in validate_code(root):
        report.add(finding["severity"], finding["code"], finding["artifact"], finding["message"])
    report.checks["code_readability"] = not any(
        item["severity"] == "error" and item["code"].startswith("code.") for item in report.findings
    )

    from smairt.research import (
        find_hypothesis,
        validate_background,
        validate_hypothesis,
        validate_proposal_set,
    )

    background_path = root / "background/initial_background.md"
    if (
        background_path.exists()
        and background_path.read_text().strip() != "# Initial Background\n\nStatus: DRAFT"
    ):
        for message in validate_background(root):
            report.add(
                "warning", "background.incomplete", str(background_path.relative_to(root)), message
            )
    proposals = sorted((root / "hypotheses/proposals").glob("PROPOSAL_SET_*.md"))
    if proposals:
        for message in validate_proposal_set(proposals[-1]):
            report.add(
                "warning", "proposal.incomplete", str(proposals[-1].relative_to(root)), message
            )
    if config.active.hypothesis:
        try:
            hypothesis_path = find_hypothesis(root, config.active.hypothesis)
        except FileNotFoundError:
            report.add(
                "error", "hypothesis.link", "smairt.yaml", "Active hypothesis file is missing"
            )
        else:
            for message in validate_hypothesis(hypothesis_path):
                report.add(
                    "warning",
                    "hypothesis.incomplete",
                    str(hypothesis_path.relative_to(root)),
                    message,
                )

    # Run records are the bridge between executed code and later scientific claims.
    # Validate them without executing or importing any researcher-authored code.
    for run_path in sorted((root / "results").glob("EXPERIMENT_*/ITERATION_*/RUN_*/run.json")):
        relative = str(run_path.relative_to(root))
        try:
            run_record = RunRecord.model_validate_json(run_path.read_text(encoding="utf-8"))
        except Exception as exc:
            report.add("error", "run.record", relative, f"Invalid run record: {exc}")
            continue
        for field_name, recorded_path in (
            ("log", run_record.log_path),
            ("results", run_record.results_directory),
        ):
            if not (root / recorded_path).exists():
                report.add(
                    "error",
                    f"run.{field_name}_missing",
                    relative,
                    f"Recorded {field_name} path does not exist: {recorded_path}",
                )
    # Decisions are human gates. A dangling decision would make the audit trail
    # appear stronger than the evidence, so broken links are hard errors.
    for decisions_path in sorted((root / "analysis").glob("EXPERIMENT_*/decisions.yaml")):
        payload = yaml.safe_load(decisions_path.read_text()) or {}
        for decision in payload.get("decisions", []):
            try:
                Decision(str(decision.get("decision")))
            except ValueError:
                report.add(
                    "error",
                    "decision.value",
                    str(decisions_path.relative_to(root)),
                    f"Invalid decision value: {decision.get('decision')}",
                )
            matches = list(
                (root / "results").glob(
                    f"EXPERIMENT_*/ITERATION_*/{decision.get('run_id')}/run.json"
                )
            )
            if len(matches) != 1:
                report.add(
                    "error",
                    "decision.run_link",
                    str(decisions_path.relative_to(root)),
                    f"Decision references missing or ambiguous run: {decision.get('run_id')}",
                )

    from smairt.paper import validate_paper

    for message in validate_paper(root):
        report.add("error", "paper.provenance", "paper/manifest.yaml", message)

    if not config.project.question:
        report.add(
            "warning",
            "project.question",
            "smairt.yaml",
            "Initial research question is not specified",
        )
    if config.data.classification.value == "controlled":
        report.add(
            "warning",
            "data.controlled",
            "smairt.yaml",
            "Controlled-data storage enforcement is not implemented in v1",
        )

    if tool_input and not sys.stdin.isatty():
        payload = sys.stdin.read()
        if any(token in payload.lower() for token in ("data/raw/", ".fast5", ".env", "api_key")):
            report.add(
                "error",
                "tool.protected_input",
                "stdin",
                "Codex tool input may access protected data or secrets",
            )
    report.readiness = _readiness(root, config)
    return report


def _readiness(root: Path, config: SmairtConfig) -> dict[str, bool]:
    """Summarize whether each workflow stage is structurally ready to advance."""
    background = root / "background/initial_background.md"
    from smairt.research import validate_background

    background_ready = background.exists() and not validate_background(root)
    proposals = sorted((root / "hypotheses/proposals").glob("PROPOSAL_SET_*.md"))
    proposal_ready = False
    if proposals:
        from smairt.research import validate_proposal_set

        proposal_ready = not validate_proposal_set(proposals[-1])
    hypothesis_ready = False
    if config.active.hypothesis:
        from smairt.research import find_hypothesis, validate_hypothesis

        try:
            hypothesis_ready = not validate_hypothesis(
                find_hypothesis(root, config.active.hypothesis)
            )
        except FileNotFoundError:
            hypothesis_ready = False
    return {
        "background": background_ready,
        "proposal_set": proposal_ready,
        "hypothesis": hypothesis_ready,
        "experiment": bool(config.active.experiment),
        "accepted_evidence": bool(config.active.accepted_run),
    }


def status(root: Path) -> dict[str, object]:
    """Return compact project state, counts, validation, readiness, and guidance."""
    config = SmairtConfig.load(root / "smairt.yaml")
    report = validate_project(root)
    proposals = sorted((root / "hypotheses/proposals").glob("PROPOSAL_SET_*.md"))
    hypotheses = [
        path
        for path in sorted((root / "hypotheses").glob("HYPOTHESIS_*.md"))
        if path.name != "HYPOTHESIS_TEMPLATE.md"
    ]
    experiments = sorted((root / "experiments").glob("EXPERIMENT_*"))
    from smairt.guidance import next_guidance

    guidance = next_guidance(root)
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
        "stage": guidance["stage"],
        "readiness": report.readiness,
        "guidance": guidance,
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
    """Select the smallest initial file set needed for a particular research task."""
    if task not in CONTEXT_MAP:
        raise ValueError(f"Unknown task {task!r}; choose {', '.join(CONTEXT_MAP)}")
    current = status(root)
    return {
        "task": task,
        "status": current,
        "read": [path for path in CONTEXT_MAP[task] if (root / path).exists()],
        "rule": "Read only these files initially; load logs, PDFs, and older iterations on demand.",
    }
