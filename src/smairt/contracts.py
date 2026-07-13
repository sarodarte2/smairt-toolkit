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
    destination.mkdir(parents=True, exist_ok=True)
    written = []
    for name, model in MODELS.items():
        path = destination / f"{name}.schema.json"
        path.write_text(json.dumps(model.model_json_schema(), indent=2) + "\n")
        written.append(str(path))
    return written


def check_contracts(destination: Path) -> dict[str, object]:
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
    return {"ok": not findings, "findings": findings}
