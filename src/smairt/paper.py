"""Paper-element provenance validation."""

from __future__ import annotations

from pathlib import Path

import yaml


def accepted_runs(root: Path) -> dict[str, dict[str, object]]:
    accepted: dict[str, dict[str, object]] = {}
    for selection in (root / "analysis").glob("*/selection.yaml"):
        payload = yaml.safe_load(selection.read_text()) or {}
        if payload.get("status") == "ACCEPTED" and payload.get("run_id"):
            accepted[str(payload["run_id"])] = payload
    return accepted


def validate_paper(root: Path) -> list[str]:
    manifest = root / "paper/manifest.yaml"
    payload = yaml.safe_load(manifest.read_text()) or {}
    elements = payload.get("elements", [])
    if not isinstance(elements, list):
        return ["paper manifest elements must be a list"]
    accepted = accepted_runs(root)
    errors: list[str] = []
    identifiers: set[str] = set()
    for index, element in enumerate(elements, start=1):
        if not isinstance(element, dict):
            errors.append(f"paper element {index} must be a mapping")
            continue
        identifier = str(element.get("id", ""))
        if not identifier:
            errors.append(f"paper element {index} is missing id")
        elif identifier in identifiers:
            errors.append(f"duplicate paper element id: {identifier}")
        identifiers.add(identifier)
        run_id = str(element.get("run_id", ""))
        if run_id not in accepted:
            display_run = run_id or "[missing]"
            errors.append(f"{identifier or index} references non-accepted run {display_run}")
    return errors
