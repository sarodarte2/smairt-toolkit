"""Standard and Strict project safety policy operations."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from smairt.models import SmairtConfig, utc_now
from smairt.project import _git_files, is_prohibited
from smairt.provenance import record_event, require_contributor

SECRET_PATTERNS = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "aws-access-key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "github-token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    "assigned-secret": re.compile(
        r"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret)\s*[:=]\s*['\"]?[A-Za-z0-9_./+\-=]{16,}"
    ),
}


def observed_repository_visibility(root: Path) -> str:
    """Query GitHub visibility through its authenticated CLI when that is safely available."""
    remote = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    github_remote = remote.returncode == 0 and "github.com" in remote.stdout.lower()
    if not github_remote or not shutil.which("gh"):
        return "unknown"
    try:
        result = subprocess.run(
            ["gh", "repo", "view", "--json", "visibility", "--jq", ".visibility"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        return "unknown"
    visibility = result.stdout.strip().lower()
    if result.returncode == 0 and visibility in {"private", "public"}:
        return visibility
    return "unknown"


def attested_repository_visibility(root: Path) -> str:
    """Return the contributor-attested repository visibility."""
    config_path = root / "smairt.yaml"
    if config_path.exists():
        declared = SmairtConfig.load(config_path).repository_attestation.visibility
        if declared in {"private", "public"}:
            return declared
    return "unknown"


def repository_visibility(root: Path) -> str:
    """Return observed visibility when available, otherwise the contributor attestation."""
    observed = observed_repository_visibility(root)
    return observed if observed != "unknown" else attested_repository_visibility(root)


def attest_repository(root: Path, visibility: str) -> dict[str, object]:
    """Record a contributor-confirmed repository visibility and collaboration acknowledgment."""
    if visibility not in {"private", "public", "unknown"}:
        raise ValueError("visibility must be private, public, or unknown")
    contributor = require_contributor(root)
    config = SmairtConfig.load(root / "smairt.yaml")
    config.repository_attestation.acknowledged = visibility == "private"
    config.repository_attestation.contributor_id = contributor.id
    config.repository_attestation.acknowledged_at = utc_now()
    config.repository_attestation.visibility = visibility
    config.dump(root / "smairt.yaml")
    record_event(
        root,
        "safety.repository.attested",
        artifact_ids=["smairt.yaml"],
        details={"visibility": visibility},
    )
    return safety_status(root)


def protected_summary_findings(root: Path, *, staged: bool = False) -> list[dict[str, str]]:
    """Find tracked protected summaries that violate the selected safety mode."""
    config = SmairtConfig.load(root / "smairt.yaml")
    if config.data.classification.value not in {"private", "controlled"}:
        return []
    tracked = set(_git_files(root, staged))
    findings = []
    for path in (root / "summaries").glob("*/*.json"):
        relative = str(path.relative_to(root))
        if relative not in tracked or path.parent.name == "canonical":
            continue
        import json

        payload = json.loads(path.read_text())
        redacted = payload.get("shareable") and payload.get("redaction_confirmed")
        visibility = repository_visibility(root)
        if config.safety_mode == "strict" and (not redacted or visibility != "private"):
            findings.append(
                {"severity": "error", "code": "summary.protected", "artifact": relative}
            )
    return findings


def safety_policy_findings(root: Path, *, staged: bool = False) -> list[dict[str, str]]:
    """Evaluate acknowledgment, visibility, summary, and current-content policy."""
    config = SmairtConfig.load(root / "smairt.yaml")
    findings = protected_summary_findings(root, staged=staged)
    protected = config.data.classification.value in {"private", "controlled"}
    visibility = repository_visibility(root)
    observed = observed_repository_visibility(root)
    attested = attested_repository_visibility(root)
    if observed != "unknown" and attested != "unknown" and observed != attested:
        findings.append(
            {
                "severity": "error",
                "code": "repository.visibility-mismatch",
                "artifact": "smairt.yaml",
            }
        )
    if protected and not config.repository_attestation.acknowledged:
        findings.append(
            {"severity": "error", "code": "repository.attestation", "artifact": "smairt.yaml"}
        )
    if config.safety_mode == "strict" and visibility != "private":
        findings.append({"severity": "error", "code": "repository.visibility", "artifact": ".git"})
    findings.extend(_content_findings(root, staged=staged))
    return findings


def _content_findings(root: Path, *, staged: bool) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for relative in _git_files(root, staged):
        path = root / relative
        if not path.is_file() or path.stat().st_size > 1_000_000:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for code, pattern in SECRET_PATTERNS.items():
            if pattern.search(content):
                findings.append(
                    {"severity": "error", "code": f"secret.{code}", "artifact": relative}
                )
    return findings


def safety_status(root: Path) -> dict[str, object]:
    """Summarize the active mode, classification, contributor, and visibility."""
    config = SmairtConfig.load(root / "smairt.yaml")
    observed = observed_repository_visibility(root)
    attested = attested_repository_visibility(root)
    return {
        "mode": config.safety_mode,
        "classification": config.data.classification.value,
        "active_contributor": config.active_contributor,
        "repository_visibility": repository_visibility(root),
        "repository_visibility_observed": observed,
        "repository_visibility_attested": attested,
        "repository_visibility_mismatch": (
            observed != "unknown" and attested != "unknown" and observed != attested
        ),
        "repository_attestation": config.repository_attestation.model_dump(mode="json"),
    }


def set_safety_mode(root: Path, mode: str) -> dict[str, object]:
    """Change safety mode with active-contributor attribution and an event."""
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
    """Run current-file, history, visibility, and protected-summary release gates."""
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
    findings.extend(safety_policy_findings(root))
    if (root / ".git").exists():
        history = subprocess.run(
            [
                "git",
                "log",
                "--all",
                "--extended-regexp",
                "-G",
                "BEGIN .*PRIVATE KEY|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{30,}",
                "--pretty=format:%H",
                "--name-only",
            ],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if history.stdout.strip():
            findings.append({"severity": "error", "code": "secret.history", "artifact": ".git"})
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
