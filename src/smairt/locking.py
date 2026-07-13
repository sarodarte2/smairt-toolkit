"""Cross-process project mutation locking without third-party dependencies."""

from __future__ import annotations

import json
import os
import shutil
import socket
from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import RLock
from typing import Any, ParamSpec, TypeVar
from uuid import uuid4

import yaml

from smairt.errors import MutationConflictError, RecoveryRequiredError
from smairt.models import utc_now
from smairt.utils import atomic_write, ensure_no_symlink

_PROCESS_GUARD = RLock()
_PROJECT_GUARDS: dict[Path, RLock] = {}
_HELD: dict[Path, int] = {}
P = ParamSpec("P")
R = TypeVar("R")


@dataclass(frozen=True)
class LockOwner:
    """Describe the process and researcher currently mutating a project."""

    host: str
    pid: int
    command: str
    contributor: str | None
    acquired_at: str
    token: str


def _lock_path(root: Path) -> Path:
    root = root.resolve()
    return ensure_no_symlink(root, root / ".smairt/locks/mutation.lock")


def _owner_path(root: Path) -> Path:
    return _lock_path(root) / "owner.json"


def _process_alive(pid: int) -> bool:
    """Return whether a local PID exists without sending it a signal."""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _incomplete_transactions(root: Path) -> list[str]:
    """Find journals that must be resolved before an unrelated mutation."""
    incomplete: list[str] = []
    for path in (root / ".smairt/transactions").glob("*"):
        if not path.is_dir():
            continue
        metadata = path / "transaction.json"
        if not metadata.exists():
            incomplete.append(path.name)
            continue
        try:
            status = json.loads(metadata.read_text(encoding="utf-8")).get("status")
        except (OSError, ValueError):
            status = "corrupt"
        if status not in {"committed", "rolled_back"}:
            incomplete.append(path.name)
    return incomplete


def read_lock(root: Path) -> dict[str, Any]:
    """Return lock ownership plus whether local liveness can be established."""
    lock = _lock_path(root)
    if not lock.exists():
        return {"locked": False, "owner": None, "recoverable": False}
    try:
        owner = json.loads(_owner_path(root).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"locked": True, "owner": None, "recoverable": False, "corrupt": True}
    required = {"host", "pid", "command", "contributor", "acquired_at", "token"}
    if set(owner) != required or not isinstance(owner.get("pid"), int):
        return {"locked": True, "owner": None, "recoverable": False, "corrupt": True}
    if not all(
        isinstance(owner.get(key), str) for key in ("host", "command", "acquired_at", "token")
    ):
        return {"locked": True, "owner": None, "recoverable": False, "corrupt": True}
    if owner.get("contributor") is not None and not isinstance(owner.get("contributor"), str):
        return {"locked": True, "owner": None, "recoverable": False, "corrupt": True}
    same_host = owner["host"] == socket.gethostname()
    alive = _process_alive(owner["pid"]) if same_host else None
    return {
        "locked": True,
        "owner": owner,
        "same_host": same_host,
        "process_alive": alive,
        "recoverable": bool(same_host and alive is False),
    }


def break_lock(root: Path, *, force: bool = False) -> dict[str, Any]:
    """Remove a stale lock, requiring force for live, corrupt, or remote owners."""
    status = read_lock(root)
    if not status["locked"]:
        return status
    if not status.get("recoverable") and not force:
        raise MutationConflictError(
            "lock ownership cannot be proven stale; rerun with explicit confirmation"
        )
    shutil.rmtree(_lock_path(root))
    return {"locked": False, "broken": True, "previous_owner": status.get("owner")}


class ProjectMutationLock(AbstractContextManager["ProjectMutationLock"]):
    """Serialize consequential changes within one checkout.

    Same-process nesting is supported because high-level workflows call smaller
    mutating domain functions. A same-host lock is recovered automatically only
    when its PID is conclusively dead.
    """

    def __init__(self, root: Path, command: str, contributor: str | None = None) -> None:
        self.root = root.resolve()
        self.path = _lock_path(self.root)
        self.command = command
        self.contributor = contributor
        self.acquired = False
        self.token = uuid4().hex
        self._thread_guard: RLock | None = None

    def __enter__(self) -> ProjectMutationLock:
        with _PROCESS_GUARD:
            guard = _PROJECT_GUARDS.setdefault(self.path, RLock())
        guard.acquire()
        self._thread_guard = guard
        try:
            return self._enter_owned_thread()
        except BaseException:
            self._thread_guard = None
            guard.release()
            raise

    def _enter_owned_thread(self) -> ProjectMutationLock:
        """Acquire process and filesystem ownership while holding the thread guard."""
        with _PROCESS_GUARD:
            if _HELD.get(self.path, 0):
                _HELD[self.path] += 1
                self.acquired = True
                return self
            incomplete = _incomplete_transactions(self.root)
            if incomplete and not self.command.startswith("recovery "):
                raise RecoveryRequiredError(
                    "incomplete transaction requires recovery: " + ", ".join(incomplete)
                )
            self.path.parent.mkdir(parents=True, exist_ok=True)
            try:
                self.path.mkdir()
            except FileExistsError:
                status = read_lock(self.root)
                if status.get("recoverable"):
                    stale = self.path.with_name(f".stale-{uuid4().hex}")
                    try:
                        self.path.replace(stale)
                    except FileNotFoundError:
                        pass
                    else:
                        shutil.rmtree(stale, ignore_errors=True)
                    try:
                        self.path.mkdir()
                    except FileExistsError as exc:
                        raise MutationConflictError(
                            "another process acquired the recovered project lock"
                        ) from exc
                else:
                    owner = status.get("owner") or {}
                    detail = f"{owner.get('host', 'unknown')} pid {owner.get('pid', 'unknown')}"
                    raise MutationConflictError(f"project is locked by {detail}") from None
            owner = LockOwner(
                host=socket.gethostname(),
                pid=os.getpid(),
                command=self.command,
                contributor=self.contributor,
                acquired_at=utc_now(),
                token=self.token,
            )
            atomic_write(self.path / "owner.json", json.dumps(asdict(owner), indent=2) + "\n")
            _HELD[self.path] = 1
            self.acquired = True
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if not self.acquired:
            return
        with _PROCESS_GUARD:
            count = _HELD.get(self.path, 0) - 1
            if count > 0:
                _HELD[self.path] = count
            else:
                _HELD.pop(self.path, None)
                status = read_lock(self.root)
                if (status.get("owner") or {}).get("token") == self.token:
                    shutil.rmtree(self.path, ignore_errors=True)
            self.acquired = False
        if self._thread_guard is not None:
            guard = self._thread_guard
            self._thread_guard = None
            guard.release()


def mutating(command: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Wrap a domain function whose first argument is the project root."""

    def decorate(function: Callable[P, R]) -> Callable[P, R]:
        from functools import wraps

        @wraps(function)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            if not args or not isinstance(args[0], Path):
                raise TypeError("mutating functions must receive project root first")
            contributor: str | None = None
            config_path = args[0] / "smairt.yaml"
            if config_path.exists():
                try:
                    payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
                    candidate = payload.get("active_contributor")
                    contributor = candidate if isinstance(candidate, str) else None
                except (OSError, ValueError):
                    pass
            with ProjectMutationLock(args[0], command, contributor=contributor):
                return function(*args, **kwargs)

        return wrapped

    return decorate
