"""Standard and Strict project safety policy operations."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

from smairt.locking import mutating
from smairt.models import RepositoryVisibility, SafetyMode, SmairtConfig, utc_now
from smairt.project import _git_files, is_prohibited
from smairt.provenance import require_contributor, stage_event
from smairt.transactions import FileTransaction
from smairt.utils import write_json

VISIBILITY_MAX_AGE = timedelta(hours=24)

SECRET_PATTERNS = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "aws-access-key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "github-token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    "assigned-secret": re.compile(
        r"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret)\s*[:=]\s*['\"]?[A-Za-z0-9_./+\-=]{16,}"
    ),
}


def _visibility_cache_path(root: Path) -> Path:
    return root / ".smairt/cache/repository-visibility.json"


def cached_repository_observation(root: Path) -> dict[str, object]:
    """Read the last explicit visibility observation without performing network access."""
    path = _visibility_cache_path(root)
    if not path.exists():
        return {
            "visibility": "unknown",
            "observed_at": None,
            "source": None,
            "status": "not_refreshed",
            "stale": True,
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        observed_at = datetime.fromisoformat(str(payload["observed_at"]).replace("Z", "+00:00"))
        payload["stale"] = datetime.now(UTC) - observed_at > VISIBILITY_MAX_AGE
        return cast(dict[str, object], payload)
    except (OSError, ValueError, KeyError, TypeError):
        return {
            "visibility": "unknown",
            "observed_at": None,
            "source": "cache",
            "status": "corrupt_cache",
            "stale": True,
        }


@mutating("safety visibility refresh")
def refresh_repository_visibility(root: Path) -> dict[str, object]:
    """Explicitly query GitHub once and cache a non-sensitive observation."""
    remote = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    github_remote = remote.returncode == 0 and "github.com" in remote.stdout.lower()
    status = "ok"
    visibility = "unknown"
    if not github_remote:
        status = "unsupported_host"
    elif not shutil.which("gh"):
        status = "missing_cli"
    else:
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
            status = "timeout"
        else:
            candidate = result.stdout.strip().lower()
            if result.returncode == 0 and candidate in {"private", "public"}:
                visibility = candidate
            elif any(token in result.stderr.lower() for token in ("auth", "login", "token")):
                status = "unauthenticated"
            else:
                status = "api_failure"
    payload: dict[str, object] = {
        "visibility": visibility,
        "observed_at": utc_now(),
        "source": "github_cli",
        "status": status,
        "stale": False,
    }
    write_json(_visibility_cache_path(root), payload)
    return payload


def observed_repository_visibility(root: Path) -> str:
    """Return the cached observation; this compatibility helper is offline."""
    return str(cached_repository_observation(root)["visibility"])


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


@mutating("safety repository attest")
def attest_repository(root: Path, visibility: str) -> dict[str, object]:
    """Record a contributor-confirmed repository visibility and collaboration acknowledgment."""
    if visibility not in {"private", "public", "unknown"}:
        raise ValueError("visibility must be private, public, or unknown")
    contributor = require_contributor(root)
    config = SmairtConfig.load(root / "smairt.yaml")
    config.repository_attestation.acknowledged = visibility == "private"
    config.repository_attestation.contributor_id = contributor.id
    config.repository_attestation.acknowledged_at = utc_now()
    config.repository_attestation.visibility = RepositoryVisibility(visibility)
    transaction = FileTransaction(root, "safety repository attest")
    transaction.stage_text(
        root / "smairt.yaml",
        config.to_yaml(),
    )
    stage_event(
        root,
        transaction,
        "safety.repository.attested",
        artifact_ids=["smairt.yaml"],
        details={"visibility": visibility},
    )
    transaction.commit()
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
    if not (root / ".git").exists():
        return findings
    try:
        git_files = _git_files(root, staged)
    except RuntimeError:
        return [{"severity": "error", "code": "git.scan_failed", "artifact": ".git"}]
    for relative in git_files:
        path = root / relative
        if not path.is_file():
            continue
        try:
            matches: set[str] = set()
            carry = ""
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    content = carry + chunk.decode("latin-1")
                    matches.update(
                        code for code, pattern in SECRET_PATTERNS.items() if pattern.search(content)
                    )
                    carry = content[-4096:]
        except OSError:
            findings.append(
                {"severity": "error", "code": "secret.scan_failed", "artifact": relative}
            )
            continue
        findings.extend(
            {"severity": "error", "code": f"secret.{code}", "artifact": relative}
            for code in sorted(matches)
        )
    return findings


def safety_status(root: Path) -> dict[str, object]:
    """Summarize safety state entirely from local records and cached observations."""
    config = SmairtConfig.load(root / "smairt.yaml")
    observation = cached_repository_observation(root)
    observed = str(observation["visibility"])
    attested = attested_repository_visibility(root)
    findings = safety_policy_findings(root)
    return {
        "mode": config.safety_mode.value,
        "classification": config.data.classification.value,
        "active_contributor": config.active_contributor,
        "repository_visibility": repository_visibility(root),
        "repository_visibility_observed": observed,
        "repository_visibility_attested": attested,
        "repository_visibility_observation": observation,
        "repository_visibility_mismatch": (
            observed != "unknown" and attested != "unknown" and observed != attested
        ),
        "repository_attestation": config.repository_attestation.model_dump(mode="json"),
        "enforcement_maturity": "experimental",
        "compliance_certified": False,
        "warnings": [item for item in findings if item["severity"] == "warning"],
        "blockers": [item for item in findings if item["severity"] == "error"],
        "remediation": (
            "Use `smairt safety status --refresh-visibility` before strict release checks."
        ),
        "notice": "SMAIRT safety checks are experimental and do not certify compliance.",
    }


@mutating("safety mode set")
def set_safety_mode(root: Path, mode: str) -> dict[str, object]:
    """Change safety mode with active-contributor attribution and an event."""
    actor = require_contributor(root)
    if mode not in {"standard", "strict"}:
        raise ValueError("mode must be standard or strict")
    config = SmairtConfig.load(root / "smairt.yaml")
    previous = config.safety_mode
    config.safety_mode = SafetyMode(mode)
    transaction = FileTransaction(root, "safety mode set")
    transaction.stage_text(
        root / "smairt.yaml",
        config.to_yaml(),
    )
    stage_event(
        root,
        transaction,
        "safety.mode.changed",
        artifact_ids=["smairt.yaml"],
        details={"previous": previous, "current": mode, "confirmed_by": actor.id},
    )
    transaction.commit()
    return safety_status(root)


def release_check(root: Path) -> dict[str, object]:
    """Run current-file, history, visibility, and protected-summary release gates."""
    config = SmairtConfig.load(root / "smairt.yaml")
    findings: list[dict[str, str]] = []
    git_available = shutil.which("git") is not None
    git_repository = (root / ".git").exists()
    if not git_available:
        findings.append({"severity": "error", "code": "git.missing", "artifact": ".git"})
    if not git_repository:
        findings.append({"severity": "error", "code": "git.repository", "artifact": ".git"})
    if git_available and git_repository:
        try:
            tracked = _git_files(root, False)
        except RuntimeError:
            tracked = []
            findings.append({"severity": "error", "code": "git.scan_failed", "artifact": ".git"})
        protected = [path for path in tracked if is_prohibited(path)]
        for path in protected:
            findings.append({"severity": "error", "code": "protected.current", "artifact": path})
        history = subprocess.run(
            ["git", "log", "--all", "--name-only", "--pretty=format:"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if history.returncode != 0:
            findings.append({"severity": "error", "code": "git.scan_failed", "artifact": ".git"})
        else:
            for path in sorted({p for p in history.stdout.splitlines() if p and is_prohibited(p)}):
                findings.append(
                    {"severity": "error", "code": "protected.history", "artifact": path}
                )
    findings.extend(safety_policy_findings(root))
    if git_available and git_repository:
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
        if history.returncode != 0:
            findings.append({"severity": "error", "code": "git.scan_failed", "artifact": ".git"})
        elif history.stdout.strip():
            findings.append({"severity": "error", "code": "secret.history", "artifact": ".git"})
    observation = cached_repository_observation(root)
    if config.data.classification.value == "controlled":
        findings.append(
            {"severity": "error", "code": "controlled.unsupported", "artifact": "smairt.yaml"}
        )
    if config.safety_mode == "strict" and (
        observation["visibility"] != "private" or observation["stale"]
    ):
        findings.append({"severity": "error", "code": "visibility.unverified", "artifact": ".git"})
    elif repository_visibility(root) == "unknown":
        findings.append({"severity": "warning", "code": "visibility.unknown", "artifact": ".git"})
    return {
        "ok": not any(f["severity"] == "error" for f in findings),
        "findings": findings,
        "disclaimer": (
            "Experimental policy only. A private Git repository is collaboration "
            "infrastructure, not regulatory or institutional compliance certification."
        ),
    }
