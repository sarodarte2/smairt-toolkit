"""Standard and Strict project safety policy operations."""

from __future__ import annotations

import subprocess
from pathlib import Path

from smairt.models import SmairtConfig
from smairt.project import _git_files, is_prohibited
from smairt.provenance import record_event, require_contributor


def repository_visibility(root: Path) -> str:
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return "unknown"
    # A remote URL alone cannot prove server-side visibility.
    return "unknown"


def safety_status(root: Path) -> dict[str, object]:
    config = SmairtConfig.load(root / "smairt.yaml")
    return {
        "mode": config.safety_mode,
        "classification": config.data.classification.value,
        "active_contributor": config.active_contributor,
        "repository_visibility": repository_visibility(root),
        "repository_attestation": config.repository_attestation.model_dump(mode="json"),
    }


def set_safety_mode(root: Path, mode: str) -> dict[str, object]:
    actor = require_contributor(root)
    if mode not in {"standard", "strict"}:
        raise ValueError("mode must be standard or strict")
    config = SmairtConfig.load(root / "smairt.yaml")
    previous = config.safety_mode
    config.safety_mode = mode
    config.dump(root / "smairt.yaml")
    record_event(
        root,
        "safety.mode.changed",
        artifact_ids=["smairt.yaml"],
        details={"previous": previous, "current": mode, "confirmed_by": actor.id},
    )
    return safety_status(root)


def release_check(root: Path) -> dict[str, object]:
    config = SmairtConfig.load(root / "smairt.yaml")
    findings: list[dict[str, str]] = []
    protected = [path for path in _git_files(root, False) if is_prohibited(path)]
    for path in protected:
        findings.append({"severity": "error", "code": "protected.current", "artifact": path})
    history = subprocess.run(
        ["git", "log", "--all", "--name-only", "--pretty=format:"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    for path in sorted({p for p in history.stdout.splitlines() if p and is_prohibited(p)}):
        findings.append({"severity": "error", "code": "protected.history", "artifact": path})
    if config.safety_mode == "strict" and repository_visibility(root) == "unknown":
        findings.append({"severity": "error", "code": "visibility.unknown", "artifact": ".git"})
    elif repository_visibility(root) == "unknown":
        findings.append({"severity": "warning", "code": "visibility.unknown", "artifact": ".git"})
    return {
        "ok": not any(f["severity"] == "error" for f in findings),
        "findings": findings,
        "disclaimer": (
            "A private Git repository is collaboration infrastructure, "
            "not institutional compliance certification."
        ),
    }
