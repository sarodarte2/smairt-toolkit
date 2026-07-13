"""Portable JSON Schema contract export and fixture validation."""

from __future__ import annotations

import json
from pathlib import Path

from smairt.models import (
    ClaimRecord,
    ContextCapsule,
    Contributor,
    CorrectionRecord,
    EvidenceCard,
    HumanGate,
    NextAction,
    PaperBuild,
    ProjectEvent,
    ReferenceRecord,
    RunRecord,
    SmairtConfig,
    SummaryRecord,
    ValidationFinding,
)
from smairt.utils import atomic_write

MODELS = {
    "project": SmairtConfig,
    "contributor": Contributor,
    "reference": ReferenceRecord,
    "run": RunRecord,
    "event": ProjectEvent,
    "correction": CorrectionRecord,
    "evidence-card": EvidenceCard,
    "claim": ClaimRecord,
    "summary": SummaryRecord,
    "context-capsule": ContextCapsule,
    "validation-finding": ValidationFinding,
    "next-action": NextAction,
    "human-gate": HumanGate,
    "paper-build": PaperBuild,
}


def export_contracts(destination: Path) -> list[str]:
    """Export versioned JSON Schemas and harness compatibility fixtures."""
    destination.mkdir(parents=True, exist_ok=True)
    written = []
    for name, model in MODELS.items():
        path = destination / f"{name}.schema.json"
        atomic_write(path, json.dumps(model.model_json_schema(), indent=2) + "\n")
        written.append(str(path))
    from smairt.harnesses import compatibility_payload

    for harness in ("codex", "zoo", "cline"):
        fixture = destination / "fixtures" / f"{harness}.json"
        fixture.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(fixture, json.dumps(compatibility_payload(harness), indent=2) + "\n")
        written.append(str(fixture))
    return written


def check_contracts(destination: Path) -> dict[str, object]:
    """Check that every required schema and adapter fixture is present and compatible."""
    findings = []
    for name in MODELS:
        path = destination / f"{name}.schema.json"
        if not path.exists():
            findings.append(f"missing {path.name}")
            continue
        try:
            payload = json.loads(path.read_text())
            if payload.get("type") != "object":
                findings.append(f"invalid root type in {path.name}")
        except json.JSONDecodeError as exc:
            findings.append(f"invalid JSON in {path.name}: {exc}")
    fixtures = destination / "fixtures"
    for harness in ("codex", "zoo", "cline"):
        path = fixtures / f"{harness}.json"
        if not path.exists():
            findings.append(f"missing fixture {path.name}")
            continue
        try:
            payload = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            findings.append(f"invalid fixture JSON in {path.name}: {exc}")
            continue
        if payload.get("contract_version") != 1 or payload.get("harness") != harness:
            findings.append(f"incompatible fixture {path.name}")
    return {"ok": not findings, "findings": findings}
