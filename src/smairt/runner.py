"""Recorded experiment execution with automatic environment and provenance capture."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from smairt.models import EnvironmentMode, RunRecord, SmairtConfig, utc_now
from smairt.utils import sha256_file, write_json


def _git_state(root: Path) -> tuple[str | None, bool]:
    if not (root / ".git").exists():
        return None, False
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=False
    )
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, check=False
    )
    return (commit.stdout.strip() if commit.returncode == 0 else None, bool(status.stdout.strip()))


def _experiment_path(root: Path, experiment_id: str) -> Path:
    path = next((root / "experiments").glob(f"{experiment_id}_*"), None)
    if path is None:
        raise FileNotFoundError(f"Experiment {experiment_id} not found")
    return path


def run_experiment(
    root: Path,
    *,
    experiment_id: str,
    iteration_id: str,
    command: list[str],
) -> RunRecord:
    if not command:
        raise ValueError("command is required after --")
    config = SmairtConfig.load(root / "smairt.yaml")
    experiment = _experiment_path(root, experiment_id)
    iteration = experiment / "iterations" / iteration_id
    if not iteration.exists():
        raise FileNotFoundError(iteration)
    iteration_config = iteration / "config.yaml"
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    run_id = f"RUN_{timestamp}"
    run_dir = root / "results" / experiment_id / iteration_id / run_id
    figures_dir = run_dir / "figures"
    artifacts_dir = run_dir / "artifacts"
    figures_dir.mkdir(parents=True)
    artifacts_dir.mkdir()
    log_path = run_dir / "run.log"

    effective_command = list(command)
    environment_info: dict[str, object] = {
        "mode": config.environment.mode.value,
        "python": sys.version,
    }
    if config.environment.mode is EnvironmentMode.NEW_CONDA and config.environment.name:
        if not shutil.which("conda"):
            raise RuntimeError("Conda environment configured but conda is not available")
        effective_command = ["conda", "run", "-n", config.environment.name, *command]
        environment_info["conda_name"] = config.environment.name
    elif config.environment.mode is EnvironmentMode.EXISTING_CONDA:
        if not shutil.which("conda"):
            raise RuntimeError("Existing Conda environment configured but conda is unavailable")
        if config.environment.prefix:
            effective_command = ["conda", "run", "-p", config.environment.prefix, *command]
            environment_info["conda_prefix"] = config.environment.prefix
        elif config.environment.name:
            effective_command = ["conda", "run", "-n", config.environment.name, *command]
            environment_info["conda_name"] = config.environment.name

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
    started_at = utc_now()
    with log_path.open("w", encoding="utf-8") as log:
        log.write(f"SMAIRT run {run_id}\nCommand: {' '.join(effective_command)}\n\n")
        process = subprocess.Popen(
            effective_command,
            cwd=iteration,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            print(line, end="")
            log.write(line)
        exit_code = process.wait()
    completed_at = utc_now()
    commit, dirty = _git_state(root)
    record = RunRecord(
        run_id=run_id,
        experiment_id=experiment_id,
        iteration_id=iteration_id,
        command=command,
        started_at=started_at,
        completed_at=completed_at,
        exit_code=exit_code,
        working_directory=str(iteration.relative_to(root)),
        log_path=str(log_path.relative_to(root)),
        results_directory=str(run_dir.relative_to(root)),
        config_sha256=sha256_file(iteration_config) if iteration_config.exists() else None,
        git_commit=commit,
        git_dirty=dirty,
        environment=environment_info,
    )
    write_json(run_dir / "run.json", record.model_dump(mode="json", exclude_none=True))
    if dirty and (root / ".git").exists():
        diff = subprocess.run(
            ["git", "diff", "--binary"], cwd=root, capture_output=True, check=False
        )
        (run_dir / "working_tree.patch").write_bytes(diff.stdout)
    if iteration_config.exists():
        shutil.copy2(iteration_config, run_dir / "config.snapshot.yaml")
    entrypoint = iteration / command[-1] if len(command) >= 2 else None
    if entrypoint and entrypoint.exists() and entrypoint.is_file():
        shutil.copy2(entrypoint, run_dir / f"entrypoint.snapshot{entrypoint.suffix}")
    return record
