"""Immutable run artifact manifests and verification."""

from __future__ import annotations

import json
import mimetypes
import re
from pathlib import Path
from typing import Any, cast

from smairt.utils import ensure_no_symlink, sha256_file, validate_identifier, write_json


def build_manifest(root: Path, run_dir: Path) -> dict[str, object]:
    """Hash a contained run tree and create its external integrity lock."""
    root = root.resolve()
    run_dir = ensure_no_symlink(root, run_dir)
    run_dir.relative_to(root / "results")
    validate_identifier(run_dir.name, label="run ID")
    artifacts = []
    for path in sorted(run_dir.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"run artifacts cannot be symlinks: {path.relative_to(run_dir)}")
        if path.is_file() and path.name != "manifest.json":
            artifacts.append(
                {
                    "path": str(path.relative_to(run_dir)),
                    "size": path.stat().st_size,
                    "media_type": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
                    "sha256": sha256_file(path),
                }
            )
    payload = {"schema_version": 1, "run_id": run_dir.name, "artifacts": artifacts}
    manifest_path = ensure_no_symlink(root, run_dir / "manifest.json")
    write_json(manifest_path, payload)
    lock = ensure_no_symlink(root, root / ".smairt/run-manifests" / f"{run_dir.name}.json")
    write_json(
        lock,
        {
            "run_id": run_dir.name,
            "manifest_path": str(manifest_path.relative_to(root)),
            "manifest_sha256": sha256_file(manifest_path),
        },
    )
    return payload


def _manifest_artifacts(manifest: object, run_id: str) -> list[dict[str, Any]]:
    """Validate the strict manifest envelope before filesystem traversal."""
    if not isinstance(manifest, dict):
        raise ValueError("manifest root must be an object")
    if manifest.get("schema_version") != 1 or manifest.get("run_id") != run_id:
        raise ValueError("manifest schema or run identity is invalid")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not all(isinstance(item, dict) for item in artifacts):
        raise ValueError("manifest artifacts must be a list of objects")
    return cast(list[dict[str, Any]], artifacts)


def _artifact_fields(item: dict[str, Any]) -> tuple[str, int, str]:
    """Return validated path, size, and digest fields for one artifact."""
    relative = item.get("path")
    size = item.get("size")
    digest = item.get("sha256")
    if not isinstance(relative, str) or not relative:
        raise ValueError("artifact path is missing")
    if not isinstance(size, int) or isinstance(size, bool) or size < 0:
        raise ValueError("artifact size is invalid")
    if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
        raise ValueError("artifact SHA-256 is invalid")
    return relative, size, digest


def verify_run(root: Path, run_id: str | None = None) -> dict[str, object]:
    """Verify manifest structure, lock identity, checksums, and complete file sets."""
    root = root.resolve()
    if run_id:
        validate_identifier(run_id, label="run ID")
    paths = sorted(
        (root / "results").glob(f"EXPERIMENT_*/ITERATION_*/{run_id or 'RUN_*'}/manifest.json")
    )
    findings: list[dict[str, str]] = []
    for manifest_path in paths:
        candidate_run_id = manifest_path.parent.name
        try:
            manifest_path = ensure_no_symlink(root, manifest_path)
            run_dir = ensure_no_symlink(root, manifest_path.parent)
            run_dir.relative_to(root / "results")
            validate_identifier(candidate_run_id, label="run ID")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            artifacts = _manifest_artifacts(manifest, candidate_run_id)
        except (json.JSONDecodeError, OSError, TypeError, ValueError) as exc:
            findings.append(
                {
                    "severity": "error",
                    "run_id": candidate_run_id,
                    "message": f"invalid manifest: {exc}",
                }
            )
            continue
        try:
            lock_path = ensure_no_symlink(
                root, root / ".smairt/run-manifests" / f"{run_dir.name}.json"
            )
        except ValueError as exc:
            findings.append(
                {
                    "severity": "error",
                    "run_id": run_dir.name,
                    "message": f"unsafe manifest lock: {exc}",
                }
            )
            lock_path = None
        if lock_path is None or not lock_path.exists():
            findings.append(
                {"severity": "error", "run_id": run_dir.name, "message": "manifest lock missing"}
            )
        else:
            try:
                lock = json.loads(lock_path.read_text(encoding="utf-8"))
                expected_manifest = str(manifest_path.relative_to(root))
                if (
                    not isinstance(lock, dict)
                    or lock.get("run_id") != run_dir.name
                    or lock.get("manifest_path") != expected_manifest
                    or not isinstance(lock.get("manifest_sha256"), str)
                ):
                    raise ValueError("manifest lock structure or identity is invalid")
            except (json.JSONDecodeError, OSError, TypeError, ValueError):
                findings.append(
                    {
                        "severity": "error",
                        "run_id": run_dir.name,
                        "message": "invalid manifest lock",
                    }
                )
                lock = {}
            if lock.get("manifest_sha256") != sha256_file(manifest_path):
                findings.append(
                    {
                        "severity": "error",
                        "run_id": run_dir.name,
                        "message": "manifest mutated",
                    }
                )
        recorded: set[str] = set()
        for item in artifacts:
            try:
                relative, size, digest = _artifact_fields(item)
                if relative in recorded:
                    raise ValueError("duplicate artifact path")
                recorded.add(relative)
                path = ensure_no_symlink(run_dir, run_dir / relative)
            except (OSError, TypeError, ValueError) as exc:
                findings.append(
                    {
                        "severity": "error",
                        "run_id": run_dir.name,
                        "message": f"manifest contains an invalid artifact: {exc}",
                    }
                )
                continue
            if not path.exists():
                findings.append(
                    {
                        "severity": "error",
                        "run_id": run_dir.name,
                        "message": f"missing {relative}",
                    }
                )
            elif not path.is_file() or path.stat().st_size != size or sha256_file(path) != digest:
                findings.append(
                    {
                        "severity": "error",
                        "run_id": run_dir.name,
                        "message": f"mutated {relative}",
                    }
                )
        try:
            current = {
                str(path.relative_to(run_dir))
                for path in run_dir.rglob("*")
                if path.is_file() and path.name != "manifest.json"
            }
        except OSError as exc:
            findings.append({"severity": "error", "run_id": run_dir.name, "message": str(exc)})
        else:
            for relative in sorted(current - recorded):
                findings.append(
                    {
                        "severity": "error",
                        "run_id": run_dir.name,
                        "message": f"unlisted artifact {relative}",
                    }
                )
    if run_id and not paths:
        findings.append(
            {"severity": "error", "run_id": run_id, "message": "run manifest not found"}
        )
    return {"ok": not findings, "runs_checked": len(paths), "findings": findings}
