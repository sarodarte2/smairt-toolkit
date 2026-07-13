"""Offline project, dependency, and release-readiness diagnostics."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
from pathlib import Path

from smairt import __version__
from smairt.harnesses import list_harnesses
from smairt.locking import read_lock
from smairt.migrations import detect_scaffold, migration_plan
from smairt.models import EnvironmentMode, SmairtConfig
from smairt.project import validate_project
from smairt.safety import release_check
from smairt.transactions import transaction_status

RUNTIME_IMPORTS = {
    "pydantic": "pydantic",
    "pyyaml": "yaml",
    "rich": "rich",
    "textual": "textual",
    "typer": "typer",
    "pypdf": "pypdf",
    "python-docx": "docx",
}


def doctor(root: Path) -> dict[str, object]:
    """Return a comprehensive local health report without contacting remotes."""
    validation = validate_project(root).as_dict()
    config = SmairtConfig.load(root / "smairt.yaml")
    missing_dependencies = [
        name for name, module in RUNTIME_IMPORTS.items() if importlib.util.find_spec(module) is None
    ]
    git_available = shutil.which("git") is not None
    git_repository = (root / ".git").exists()
    git_required = config.git.enabled
    git_ok = not git_required
    if git_repository and git_available:
        git_ok = (
            subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=root,
                capture_output=True,
                check=False,
            ).returncode
            == 0
        )
    environment_ok = not (
        config.environment.mode is not EnvironmentMode.NONE and shutil.which("conda") is None
    )
    transactions = transaction_status(root)
    harnesses = list_harnesses(root)
    active_harness = next(item for item in harnesses if item["active"])
    harness_ok = not any(
        active_harness.get(key)
        for key in ("missing", "modified", "non_executable", "schema_errors", "manifest_error")
    ) and bool(active_harness.get("adapter_supported"))
    schema = detect_scaffold(root)
    release = release_check(root)
    ok = bool(
        validation["ok"]
        and schema == "v2"
        and not missing_dependencies
        and (not git_required or git_ok)
        and environment_ok
        and transactions["ok"]
        and harness_ok
    )
    return {
        "ok": ok,
        "package": {"version": __version__, "missing_dependencies": missing_dependencies},
        "scaffold": schema,
        "schema_compatible": schema == "v2",
        "git": {
            "available": git_available,
            "repository": git_repository,
            "healthy": git_ok,
        },
        "lock": read_lock(root),
        "transactions": transactions,
        "validation": validation,
        "harnesses": harnesses,
        "environment": {
            "configured": config.environment.model_dump(mode="json", exclude_none=True),
            "healthy": environment_ok,
        },
        "migration": migration_plan(root),
        "release": release,
        "release_ready": bool(ok and release["ok"]),
        "network_accessed": False,
    }
