"""Recoverable multi-file transactions for durable SMAIRT state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from smairt.errors import IntegrityError, RecoveryRequiredError
from smairt.locking import ProjectMutationLock
from smairt.models import utc_now
from smairt.utils import (
    atomic_write,
    atomic_write_bytes,
    ensure_no_symlink,
    sha256_file,
    validate_identifier,
)


def _journal_root(root: Path) -> Path:
    return root / ".smairt/transactions"


def _metadata(path: Path) -> dict[str, object]:
    payload = json.loads((path / "transaction.json").read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("transaction journal root must be an object")
    return cast(dict[str, object], payload)


def _contained(base: Path, relative: object, *, label: str) -> Path:
    """Resolve a journal-controlled relative path inside its required boundary."""
    if not isinstance(relative, str) or not relative:
        raise IntegrityError(f"{label} is missing")
    candidate = Path(str(relative))
    if candidate.is_absolute() or ".." in candidate.parts:
        raise IntegrityError(f"{label} is not a safe relative path")
    try:
        resolved = ensure_no_symlink(base, base / candidate)
    except ValueError as exc:
        raise IntegrityError(f"{label} escapes its recovery boundary") from exc
    return resolved


def _operations(record: dict[str, object]) -> list[dict[str, Any]]:
    """Validate the transaction operation collection before recovery uses it."""
    raw = record.get("operations")
    if not isinstance(raw, list) or not all(isinstance(item, dict) for item in raw):
        raise IntegrityError("transaction operations are malformed")
    return cast(list[dict[str, Any]], raw)


def transaction_status(root: Path) -> dict[str, object]:
    """List incomplete and historical transaction journals."""
    journals: list[dict[str, object]] = []
    for path in sorted(_journal_root(root).glob("*")):
        if not path.is_dir():
            continue
        if not (path / "transaction.json").exists():
            journals.append({"id": path.name, "status": "corrupt"})
            continue
        try:
            record = _metadata(path)
        except (OSError, ValueError):
            record = {"id": path.name, "status": "corrupt"}
        journals.append(record)
    incomplete = [
        item for item in journals if item.get("status") not in {"committed", "rolled_back"}
    ]
    return {"ok": not incomplete, "incomplete": incomplete, "transactions": journals}


class FileTransaction:
    """Stage validated bytes and atomically replace all declared targets."""

    def __init__(self, root: Path, command: str) -> None:
        self.root = root.resolve()
        self.id = f"txn-{uuid4().hex}"
        self.path = _journal_root(self.root) / self.id
        self.command = command
        self.created_at = utc_now()
        self.operations: list[dict[str, object]] = []

    def _persist(self, status: str) -> dict[str, object]:
        """Persist the current staged-operation set as recoverable journal state."""
        record: dict[str, object] = {
            "schema_version": 1,
            "id": self.id,
            "command": self.command,
            "created_at": self.created_at,
            "status": status,
            "operations": self.operations,
        }
        atomic_write(self.path / "transaction.json", json.dumps(record, indent=2) + "\n")
        return record

    def stage_text(self, target: Path, content: str, *, mode: int | None = None) -> None:
        """Stage UTF-8 text and record its pre/post integrity hashes."""
        self.stage_bytes(target, content.encode("utf-8"), mode=mode)

    def stage_bytes(self, target: Path, content: bytes, *, mode: int | None = None) -> None:
        """Stage bytes for a root-contained target without exposing partial state."""
        requested = target if target.is_absolute() else self.root / target
        try:
            target = ensure_no_symlink(self.root, requested)
            relative = target.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("transaction target is unsafe or escapes the project root") from exc
        # Publish the journal before staging bytes so an interruption never
        # leaves an opaque directory that recovery cannot interpret.
        self._persist("staging")
        index = len(self.operations)
        staged = self.path / "staged" / str(index)
        backup = self.path / "backups" / str(index)
        atomic_write_bytes(staged, content)
        existed = target.exists()
        if existed:
            atomic_write_bytes(backup, target.read_bytes(), mode=target.stat().st_mode & 0o777)
        self.operations.append(
            {
                "target": str(relative),
                "staged": str(staged.relative_to(self.path)),
                "backup": str(backup.relative_to(self.path)) if existed else None,
                "pre_sha256": sha256_file(target) if existed else None,
                "pre_mode": target.stat().st_mode & 0o777 if existed else None,
                "post_sha256": sha256_file(staged),
                "mode": mode,
                "delete": False,
            }
        )
        self._persist("staging")

    def stage_delete(self, target: Path) -> None:
        """Stage deletion of one root-contained file with a verified rollback copy."""
        requested = target if target.is_absolute() else self.root / target
        try:
            target = ensure_no_symlink(self.root, requested)
            relative = target.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("transaction target is unsafe or escapes the project root") from exc
        if target.exists() and not target.is_file():
            raise ValueError("transaction deletion target must be a file")
        self._persist("staging")
        index = len(self.operations)
        backup = self.path / "backups" / str(index)
        existed = target.exists()
        if existed:
            atomic_write_bytes(backup, target.read_bytes(), mode=target.stat().st_mode & 0o777)
        self.operations.append(
            {
                "target": str(relative),
                "staged": None,
                "backup": str(backup.relative_to(self.path)) if existed else None,
                "pre_sha256": sha256_file(target) if existed else None,
                "pre_mode": target.stat().st_mode & 0o777 if existed else None,
                "post_sha256": None,
                "mode": None,
                "delete": True,
            }
        )
        self._persist("staging")

    def commit(self) -> dict[str, object]:
        """Persist the journal, replace targets, and mark the operation committed."""
        if not self.operations:
            raise ValueError("transaction contains no operations")
        record = self._persist("prepared")
        record["status"] = "applying"
        atomic_write(self.path / "transaction.json", json.dumps(record, indent=2) + "\n")
        _complete(self.root, self.path, record)
        return record


def _complete(root: Path, path: Path, record: dict[str, object]) -> None:
    operations = _operations(record)
    prepared: list[tuple[dict[str, Any], Path, Path | None]] = []
    for operation in operations:
        target = _contained(root, operation.get("target"), label="transaction target")
        deleting = operation.get("delete") is True
        staged = (
            None if deleting else _contained(path, operation.get("staged"), label="staged file")
        )
        expected_post = operation.get("post_sha256")
        if not deleting and (
            staged is None or not staged.is_file() or sha256_file(staged) != expected_post
        ):
            raise IntegrityError("staged transaction content failed its integrity check")
        expected_pre = operation.get("pre_sha256")
        if target.exists():
            current = sha256_file(target)
            if not deleting and current == expected_post:
                continue
            if expected_pre is None or current != expected_pre:
                raise RecoveryRequiredError("transaction target diverged from recorded pre-state")
        elif expected_pre is not None and not deleting:
            raise RecoveryRequiredError("transaction target disappeared after staging")
        prepared.append((operation, target, staged))
    for operation, target, staged in prepared:
        if operation.get("delete") is True:
            target.unlink(missing_ok=True)
            continue
        if target.exists() and sha256_file(target) == operation["post_sha256"]:
            continue
        if staged is None:  # pragma: no cover - guarded while preparing operations
            raise IntegrityError("transaction staged file is missing")
        atomic_write_bytes(target, staged.read_bytes(), mode=operation.get("mode"))
    record["status"] = "committed"
    record["committed_at"] = utc_now()
    atomic_write(path / "transaction.json", json.dumps(record, indent=2) + "\n")


def complete_transaction(root: Path, identifier: str) -> dict[str, object]:
    """Finish an incomplete prepared transaction after explicit confirmation."""
    validate_identifier(identifier, label="transaction ID")
    path = _journal_root(root) / identifier
    if not path.is_dir():
        raise FileNotFoundError(f"unknown transaction: {identifier}")
    with ProjectMutationLock(root, f"recovery complete {identifier}"):
        record = _metadata(path)
        if record.get("status") in {"committed", "rolled_back"}:
            raise RecoveryRequiredError("transaction does not require recovery")
        _complete(root, path, record)
        return record


def rollback_transaction(root: Path, identifier: str) -> dict[str, object]:
    """Restore pre-transaction bytes or remove newly created targets."""
    validate_identifier(identifier, label="transaction ID")
    path = _journal_root(root) / identifier
    if not path.is_dir():
        raise FileNotFoundError(f"unknown transaction: {identifier}")
    with ProjectMutationLock(root, f"recovery rollback {identifier}"):
        record = _metadata(path)
        if record.get("status") in {"committed", "rolled_back"}:
            raise RecoveryRequiredError("only incomplete transactions can be rolled back")
        operations = _operations(record)
        prepared: list[tuple[dict[str, Any], Path, Path | None]] = []
        for operation in operations:
            target = _contained(root, operation.get("target"), label="transaction target")
            backup_name = operation.get("backup")
            backup = (
                _contained(path, backup_name, label="transaction backup") if backup_name else None
            )
            expected_pre = operation.get("pre_sha256")
            expected_post = operation.get("post_sha256")
            if backup is not None and (not backup.is_file() or sha256_file(backup) != expected_pre):
                raise IntegrityError("transaction backup failed its integrity check")
            if target.exists():
                current = sha256_file(target)
                if current not in {expected_pre, expected_post}:
                    raise RecoveryRequiredError("transaction target diverged during recovery")
            elif expected_pre is not None and operation.get("delete") is not True:
                raise RecoveryRequiredError("transaction target disappeared during recovery")
            prepared.append((operation, target, backup))
        for operation, target, backup in reversed(prepared):
            if backup is not None:
                atomic_write_bytes(
                    target, backup.read_bytes(), mode=cast(int | None, operation.get("pre_mode"))
                )
            else:
                target.unlink(missing_ok=True)
        record["status"] = "rolled_back"
        record["rolled_back_at"] = utc_now()
        atomic_write(path / "transaction.json", json.dumps(record, indent=2) + "\n")
        return record
