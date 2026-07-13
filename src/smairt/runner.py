"""Recorded experiment execution with terminal-state provenance capture."""

from __future__ import annotations

import hashlib
import importlib.metadata
import os
import re
import shutil
import signal
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import FrameType
from typing import Any

import yaml

from smairt.integrity import build_manifest
from smairt.locking import ProjectMutationLock
from smairt.models import EnvironmentMode, RunRecord, RunStatus, SmairtConfig, utc_now
from smairt.research import find_hypothesis, validate_hypothesis
from smairt.utils import (
    atomic_write_bytes,
    ensure_no_symlink,
    sha256_file,
    validate_identifier,
    write_json,
)

_SECRET_NAME = re.compile(r"(?i)(?:api[_-]?key|access[_-]?token|token|secret|password|credential)")
_SECRET_ASSIGNMENT = re.compile(
    r"(?i)(api[_-]?key|access[_-]?token|token|secret|password|credential)(=|:)([^&\s]+)"
)
_URL_PASSWORD = re.compile(r"(https?://[^/:@\s]+:)([^@/\s]+)(@)", re.IGNORECASE)


def _git_capture(root: Path) -> dict[str, Any]:
    """Capture commit identity and all working-tree categories without mutation."""
    if not (root / ".git").exists():
        return {
            "status": "not_repository",
            "commit": None,
            "dirty": False,
            "staged": [],
            "unstaged": [],
            "untracked": [],
        }

    def run(*arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments], cwd=root, capture_output=True, text=True, check=False
        )

    try:
        commit = run("rev-parse", "HEAD")
        staged = run("diff", "--name-only", "--cached")
        unstaged = run("diff", "--name-only")
        untracked = run("ls-files", "--others", "--exclude-standard")
    except OSError:
        return {
            "status": "error",
            "commit": None,
            "dirty": True,
            "staged": [],
            "unstaged": [],
            "untracked": [],
        }
    categories = {
        "staged": [line for line in staged.stdout.splitlines() if line],
        "unstaged": [line for line in unstaged.stdout.splitlines() if line],
        "untracked": [line for line in untracked.stdout.splitlines() if line],
    }
    return {
        "status": (
            "ok"
            if all(result.returncode == 0 for result in (commit, staged, unstaged, untracked))
            else "error"
        ),
        "commit": commit.stdout.strip() if commit.returncode == 0 else None,
        "dirty": any(categories.values())
        or any(result.returncode != 0 for result in (commit, staged, unstaged, untracked)),
        **categories,
    }


def _experiment_path(root: Path, experiment_id: str) -> Path:
    """Resolve an experiment ID after excluding glob metacharacters and traversal."""
    validate_identifier(experiment_id, label="experiment ID")
    matches = list((root / "experiments").glob(f"{experiment_id}_*"))
    if len(matches) != 1:
        raise FileNotFoundError(f"Experiment {experiment_id} not found or ambiguous")
    return ensure_no_symlink(root, matches[0])


def _installed_packages() -> dict[str, str]:
    """Return package names and versions without paths, URLs, or environment values."""
    packages: dict[str, str] = {}
    for distribution in importlib.metadata.distributions():
        try:
            name = distribution.metadata["Name"]
        except KeyError:
            name = None
        if name:
            packages[str(name)] = distribution.version
    return dict(sorted(packages.items(), key=lambda item: item[0].lower()))


def _sanitized_command(command: list[str]) -> tuple[list[str], list[str]]:
    """Redact credential-shaped arguments while retaining executable provenance."""
    sanitized: list[str] = []
    secrets: list[str] = []
    redact_next = False
    for argument in command:
        if redact_next:
            secrets.append(argument)
            sanitized.append("[REDACTED]")
            redact_next = False
            continue
        if argument.startswith("-") and "=" not in argument and _SECRET_NAME.search(argument):
            sanitized.append(argument)
            redact_next = True
            continue

        def replace(match: re.Match[str]) -> str:
            secrets.append(match.group(3))
            return f"{match.group(1)}{match.group(2)}[REDACTED]"

        safe = _SECRET_ASSIGNMENT.sub(replace, argument)
        url_match = _URL_PASSWORD.search(safe)
        if url_match:
            secrets.append(url_match.group(2))
            safe = _URL_PASSWORD.sub(r"\1[REDACTED]\3", safe)
        sanitized.append(safe)
    return sanitized, [value for value in secrets if value]


def _redact_text(value: str, secrets: list[str]) -> str:
    """Remove command-derived secret values from child output and failures."""
    redacted = value
    for secret in sorted(set(secrets), key=len, reverse=True):
        redacted = redacted.replace(secret, "[REDACTED]")
    return _SECRET_ASSIGNMENT.sub(r"\1\2[REDACTED]", redacted)


def _resolved_entrypoint(
    iteration: Path, command: list[str], metadata: dict[str, Any]
) -> Path | None:
    """Resolve the executed source file rather than assuming the final argument."""
    candidates: list[str] = []
    configured = metadata.get("entrypoint")
    if isinstance(configured, str):
        candidates.append(configured)
    candidates.extend(argument for argument in command if not argument.startswith("-"))
    for candidate in candidates:
        path = Path(candidate)
        path = path if path.is_absolute() else iteration / path
        try:
            resolved = path.resolve()
            resolved.relative_to(iteration.resolve())
        except (OSError, ValueError):
            continue
        if resolved.is_file():
            return resolved
    return None


def _effective_command(
    config: SmairtConfig, command: list[str]
) -> tuple[list[str], dict[str, Any]]:
    """Resolve the configured execution environment or fail with a stable cause."""
    effective = list(command)
    environment: dict[str, Any] = {
        "mode": config.environment.mode.value,
        "python": sys.version,
        "packages": _installed_packages(),
    }
    if config.environment.mode is EnvironmentMode.NEW_CONDA and config.environment.name:
        if not shutil.which("conda"):
            raise RuntimeError("Conda environment configured but conda is not available")
        effective = ["conda", "run", "-n", config.environment.name, *command]
        environment["conda_name"] = config.environment.name
    elif config.environment.mode is EnvironmentMode.EXISTING_CONDA:
        if not shutil.which("conda"):
            raise RuntimeError("Existing Conda environment configured but conda is unavailable")
        if config.environment.prefix:
            effective = ["conda", "run", "-p", config.environment.prefix, *command]
            environment["conda_prefix"] = config.environment.prefix
        elif config.environment.name:
            effective = ["conda", "run", "-n", config.environment.name, *command]
            environment["conda_name"] = config.environment.name
    return effective, environment


def _safe_snapshot(content: bytes, artifact: str) -> tuple[bytes | None, dict[str, str] | None]:
    """Reject secret-bearing or non-text snapshots while retaining a safe digest receipt."""
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return None, {
            "artifact": artifact,
            "reason": "non-text snapshot omitted",
            "sha256": hashlib.sha256(content).hexdigest(),
        }
    from smairt.safety import SECRET_PATTERNS

    if any(pattern.search(text) for pattern in SECRET_PATTERNS.values()):
        return None, {
            "artifact": artifact,
            "reason": "secret-like content omitted",
            "sha256": hashlib.sha256(content).hexdigest(),
        }
    return content, None


def _write_git_artifacts(root: Path, run_dir: Path, state: dict[str, Any]) -> list[dict[str, str]]:
    """Persist safe Git patches and return receipts for intentionally omitted snapshots."""
    redactions: list[dict[str, str]] = []
    write_json(run_dir / "git-state.json", state)
    if not (root / ".git").exists():
        return redactions
    for filename, arguments in (
        ("unstaged.patch", ["git", "diff", "--binary"]),
        ("staged.patch", ["git", "diff", "--binary", "--cached"]),
    ):
        result = subprocess.run(arguments, cwd=root, capture_output=True, check=False)
        if result.stdout:
            safe, receipt = _safe_snapshot(result.stdout, filename)
            if receipt:
                redactions.append(receipt)
            elif safe is not None:
                atomic_write_bytes(run_dir / filename, safe)
    return redactions


def run_experiment(
    root: Path,
    *,
    experiment_id: str,
    iteration_id: str,
    command: list[str] | None = None,
) -> RunRecord:
    """Execute an iteration and finalize every reserved attempt.

    Reservation and finalization hold the project mutation lock; the child runs
    without it so independent experiments can execute concurrently. Launch,
    environment, nonzero-exit, and interruption failures still produce a
    terminal run record and integrity manifest.
    """
    validate_identifier(iteration_id, label="iteration ID")
    config = SmairtConfig.load(root / "smairt.yaml")
    experiment = _experiment_path(root, experiment_id)
    metadata = yaml.safe_load((experiment / "experiment.yaml").read_text()) or {}
    original_command = list(command or [])
    if not original_command:
        original_command = [sys.executable, str(metadata.get("entrypoint", "run.py"))]
    recorded_command, command_secrets = _sanitized_command(original_command)
    hypothesis_id = metadata.get("hypothesis")
    if hypothesis_id:
        hypothesis_errors = validate_hypothesis(find_hypothesis(root, str(hypothesis_id)))
        if hypothesis_errors:
            raise ValueError("Linked hypothesis is incomplete: " + "; ".join(hypothesis_errors))
    iteration = ensure_no_symlink(root, experiment / "iterations" / iteration_id)
    if not iteration.is_dir():
        raise FileNotFoundError(iteration)
    iteration_config = iteration / "config.yaml"
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    run_id = f"RUN_{timestamp}"
    run_dir = root / "results" / experiment_id / iteration_id / run_id
    figures_dir = run_dir / "figures"
    artifacts_dir = run_dir / "artifacts"
    log_path = run_dir / "run.log"
    incomplete_log = run_dir / ".run.log.incomplete"
    started_at = utc_now()
    initial = RunRecord(
        run_id=run_id,
        experiment_id=experiment_id,
        iteration_id=iteration_id,
        status=RunStatus.STARTED,
        command=recorded_command,
        started_at=started_at,
        working_directory=str(iteration.relative_to(root)),
        log_path=str(log_path.relative_to(root)),
        results_directory=str(run_dir.relative_to(root)),
        environment={"mode": config.environment.mode.value},
        manifest_path=str((run_dir / "manifest.json").relative_to(root)),
    )
    with ProjectMutationLock(root, f"run reserve {experiment_id}/{iteration_id}"):
        figures_dir.mkdir(parents=True)
        artifacts_dir.mkdir()
        write_json(run_dir / "run.json", initial.model_dump(mode="json", exclude_none=True))

    status = RunStatus.FAILED
    exit_code = 127
    environment_info: dict[str, Any] = {"mode": config.environment.mode.value}
    process: subprocess.Popen[str] | None = None
    interrupted = False
    unexpected: Exception | None = None
    handlers: dict[int, Any] = {}
    try:
        effective_command, environment_info = _effective_command(config, original_command)
        recorded_effective, effective_secrets = _sanitized_command(effective_command)
        command_secrets.extend(effective_secrets)
        env = os.environ.copy()
        env.update(
            {
                "SMAIRT_PROJECT_ROOT": str(root),
                "SMAIRT_EXPERIMENT_ID": experiment_id,
                "SMAIRT_ITERATION_ID": iteration_id,
                "SMAIRT_RUN_ID": run_id,
                "SMAIRT_CONFIG_PATH": str(iteration_config),
                "SMAIRT_RESULTS_DIR": str(artifacts_dir),
                "SMAIRT_FIGURES_DIR": str(figures_dir),
            }
        )
        with incomplete_log.open("w", encoding="utf-8") as log:
            log.write(f"SMAIRT run {run_id}\nCommand: {' '.join(recorded_effective)}\n\n")
            log.flush()
            process = subprocess.Popen(
                effective_command,
                cwd=iteration,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            def forward(signum: int, frame: FrameType | None) -> None:
                del frame
                nonlocal interrupted
                interrupted = True
                if process and process.poll() is None:
                    process.send_signal(signum)

            for signum in (signal.SIGINT, signal.SIGTERM):
                try:
                    handlers[signum] = signal.getsignal(signum)
                    signal.signal(signum, forward)
                except ValueError:
                    pass
            if process.stdout is None:  # pragma: no cover - guaranteed by stdout=PIPE
                raise RuntimeError("runner child process did not expose stdout")
            for line in process.stdout:
                redacted_line = _redact_text(line, command_secrets)
                print(redacted_line, end="")
                log.write(redacted_line)
            exit_code = process.wait()
        status = (
            RunStatus.INTERRUPTED
            if interrupted or exit_code in {-signal.SIGINT, -signal.SIGTERM, 130, 143}
            else RunStatus.COMPLETED
            if exit_code == 0
            else RunStatus.FAILED
        )
    except KeyboardInterrupt:
        interrupted = True
        if process and process.poll() is None:
            process.send_signal(signal.SIGINT)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
        exit_code = 130
        status = RunStatus.INTERRUPTED
    except (FileNotFoundError, PermissionError, RuntimeError) as exc:
        exit_code = 126 if isinstance(exc, PermissionError) else 127
        status = RunStatus.FAILED
        with incomplete_log.open("a", encoding="utf-8") as log:
            log.write(f"SMAIRT launch failure: {_redact_text(str(exc), command_secrets)}\n")
    except OSError as exc:
        exit_code = 1
        status = RunStatus.FAILED
        with incomplete_log.open("a", encoding="utf-8") as log:
            log.write(f"SMAIRT execution failure: {_redact_text(str(exc), command_secrets)}\n")
    except Exception as exc:
        unexpected = exc
        exit_code = 1
        status = RunStatus.FAILED
        with incomplete_log.open("a", encoding="utf-8") as log:
            log.write("SMAIRT execution failed unexpectedly; rerun with --verbose for details.\n")
    finally:
        for restore_signum, handler in handlers.items():
            signal.signal(restore_signum, handler)

    completed_at = utc_now()
    git = _git_capture(root)
    record = RunRecord(
        run_id=run_id,
        experiment_id=experiment_id,
        iteration_id=iteration_id,
        status=status,
        command=recorded_command,
        started_at=started_at,
        completed_at=completed_at,
        exit_code=exit_code,
        working_directory=str(iteration.relative_to(root)),
        log_path=str(log_path.relative_to(root)),
        results_directory=str(run_dir.relative_to(root)),
        config_sha256=sha256_file(iteration_config) if iteration_config.exists() else None,
        git_commit=git["commit"],
        git_dirty=bool(git["dirty"]),
        environment=environment_info,
        manifest_path=str((run_dir / "manifest.json").relative_to(root)),
    )
    with ProjectMutationLock(root, f"run finalize {run_id}"):
        if incomplete_log.exists():
            incomplete_log.replace(log_path)
        else:
            atomic_write_bytes(log_path, b"")
        redactions = _write_git_artifacts(root, run_dir, git)
        if iteration_config.exists():
            safe, receipt = _safe_snapshot(iteration_config.read_bytes(), "config.snapshot.yaml")
            if receipt:
                redactions.append(receipt)
            elif safe is not None:
                atomic_write_bytes(run_dir / "config.snapshot.yaml", safe)
        entrypoint = _resolved_entrypoint(iteration, original_command, metadata)
        if entrypoint:
            name = f"entrypoint.snapshot{entrypoint.suffix}"
            safe, receipt = _safe_snapshot(entrypoint.read_bytes(), name)
            if receipt:
                redactions.append(receipt)
            elif safe is not None:
                atomic_write_bytes(run_dir / name, safe)
        environment = dict(record.environment)
        environment["git_capture_status"] = git["status"]
        if redactions:
            environment["omitted_provenance"] = redactions
            write_json(run_dir / "provenance-omissions.json", {"omissions": redactions})
        record = record.model_copy(update={"environment": environment})
        write_json(run_dir / "run.json", record.model_dump(mode="json", exclude_none=True))
        build_manifest(root, run_dir)
    if unexpected is not None:
        raise unexpected
    return record
