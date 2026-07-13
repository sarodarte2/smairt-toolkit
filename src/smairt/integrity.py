"""Immutable run artifact manifests and verification."""

from __future__ import annotations

import json
import mimetypes
from pathlib import Path

from smairt.utils import sha256_file, write_json


def build_manifest(root: Path, run_dir: Path) -> dict[str, object]:
    """Hash every immutable run file and create an external manifest lock."""
    artifacts = []
    for path in sorted(run_dir.rglob("*")):
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
    write_json(run_dir / "manifest.json", payload)
    lock = root / ".smairt/run-manifests" / f"{run_dir.name}.json"
    write_json(
        lock,
        {
            "run_id": run_dir.name,
            "manifest_path": str((run_dir / "manifest.json").relative_to(root)),
            "manifest_sha256": sha256_file(run_dir / "manifest.json"),
        },
    )
    return payload


def verify_run(root: Path, run_id: str | None = None) -> dict[str, object]:
    """Verify locked manifests and every recorded run artifact checksum."""
    paths = sorted(
        (root / "results").glob(f"EXPERIMENT_*/ITERATION_*/{run_id or 'RUN_*'}/manifest.json")
    )
    findings: list[dict[str, str]] = []
    for manifest_path in paths:
        try:
            manifest = json.loads(manifest_path.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            findings.append(
                {
                    "severity": "error",
                    "run_id": manifest_path.parent.name,
                    "message": f"invalid manifest: {exc}",
                }
            )
            continue
        run_dir = manifest_path.parent
        lock_path = root / ".smairt/run-manifests" / f"{run_dir.name}.json"
        if not lock_path.exists():
            findings.append(
                {"severity": "error", "run_id": run_dir.name, "message": "manifest lock missing"}
            )
        else:
            lock = json.loads(lock_path.read_text())
            if lock.get("manifest_sha256") != sha256_file(manifest_path):
                findings.append(
                    {
                        "severity": "error",
                        "run_id": run_dir.name,
                        "message": "manifest mutated",
                    }
                )
        for item in manifest.get("artifacts", []):
            path = run_dir / item["path"]
            if not path.exists():
                findings.append(
                    {
                        "severity": "error",
                        "run_id": run_dir.name,
                        "message": f"missing {item['path']}",
                    }
                )
            elif path.stat().st_size != item["size"] or sha256_file(path) != item["sha256"]:
                findings.append(
                    {
                        "severity": "error",
                        "run_id": run_dir.name,
                        "message": f"mutated {item['path']}",
                    }
                )
    if run_id and not paths:
        findings.append(
            {"severity": "error", "run_id": run_id, "message": "run manifest not found"}
        )
    return {"ok": not findings, "runs_checked": len(paths), "findings": findings}
