"""Machine-checkable scientific protocol and result-summary contracts."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from smairt.models import ScientificProtocol, ScientificResultSummary
from smairt.utils import sha256_file

PLACEHOLDER = "[complete before running]"


def protocol_template(question_or_purpose: str, seed: int = 1024) -> str:
    """Render a readable draft that names every required scientific decision."""
    payload = {
        "schema_version": 1,
        "status": "draft",
        "question_or_purpose": question_or_purpose,
        "design": PLACEHOLDER,
        "unit_of_analysis": PLACEHOLDER,
        "inputs": [{"name": "declared input", "unit": PLACEHOLDER}],
        "primary_outcome": {"name": PLACEHOLDER, "unit": PLACEHOLDER},
        "secondary_outcomes": [],
        "controls": [PLACEHOLDER],
        "replication_rationale": PLACEHOLDER,
        "randomization_and_blinding": PLACEHOLDER,
        "exclusions_and_missing_data": PLACEHOLDER,
        "analysis_method": PLACEHOLDER,
        "assumptions": [PLACEHOLDER],
        "uncertainty_measure": PLACEHOLDER,
        "multiple_comparisons": PLACEHOLDER,
        "seed": seed,
        "success_criteria": PLACEHOLDER,
        "failure_criteria": PLACEHOLDER,
        "falsifier": PLACEHOLDER,
        "stopping_rule": PLACEHOLDER,
        "declared_outputs": ["artifacts/results.json"],
    }
    return yaml.safe_dump(payload, sort_keys=False)


def load_protocol(path: Path) -> ScientificProtocol:
    """Load one protocol through the stable typed contract."""
    return ScientificProtocol.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def validate_protocol(path: Path) -> list[str]:
    """Report structural, readiness, and placeholder failures without mutation."""
    if not path.exists():
        return ["missing protocol.yaml"]
    try:
        protocol = load_protocol(path)
    except (OSError, ValueError, ValidationError) as exc:
        return [f"invalid protocol.yaml: {exc}"]
    errors = []
    if protocol.status != "ready":
        errors.append("protocol status must be ready")
    content = path.read_text(encoding="utf-8").casefold()
    if PLACEHOLDER.casefold() in content:
        errors.append("protocol still contains required placeholders")
    return errors


def validate_result_summary(path: Path) -> list[str]:
    """Require a typed, placeholder-free scientific result interpretation."""
    if not path.exists():
        return ["missing result-summary.yaml"]
    try:
        summary = ScientificResultSummary.model_validate(
            yaml.safe_load(path.read_text(encoding="utf-8"))
        )
    except (OSError, ValueError, ValidationError) as exc:
        return [f"invalid result-summary.yaml: {exc}"]
    if not summary.artifact_checksums:
        return ["result summary must record at least one artifact checksum"]
    for relative, expected in summary.artifact_checksums.items():
        candidate = Path(relative)
        if candidate.is_absolute() or ".." in candidate.parts:
            return [f"result summary contains unsafe artifact path: {relative}"]
        artifact = path.parent / candidate
        if not artifact.is_file():
            return [f"result summary artifact is missing: {relative}"]
        if sha256_file(artifact) != expected:
            return [f"result summary checksum does not match: {relative}"]
    if PLACEHOLDER.casefold() in path.read_text(encoding="utf-8").casefold():
        return ["result summary still contains required placeholders"]
    return []


def validate_interpretation(path: Path) -> list[str]:
    """Require observations, inference, and limitations before acceptance."""
    if not path.exists():
        return ["missing iteration analysis"]
    content = path.read_text(encoding="utf-8")
    errors = []
    for heading in ("Observed Results", "Interpretation", "Limitations and Confounders"):
        marker = f"## {heading}"
        if marker not in content:
            errors.append(f"missing analysis section: {heading}")
            continue
        body = content.split(marker, 1)[1].split("\n## ", 1)[0].strip()
        if not body:
            errors.append(f"empty analysis section: {heading}")
    if PLACEHOLDER.casefold() in content.casefold():
        errors.append("analysis still contains required placeholders")
    return errors
