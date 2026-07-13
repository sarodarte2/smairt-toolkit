"""Immutable run artifact manifests and verification."""

from __future__ import annotations

import json
import mimetypes
from pathlib import Path

from smairt.utils import sha256_file, write_json


def build_manifest(root: Path, run_dir: Path) -> dict[str, object]:
    artifacts = []
    for path in sorted(run_dir.rglob("*")):
        if path.is_file() and path.name not in {"manifest.json", "run.json"}:
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
    return payload


def verify_run(root: Path, run_id: str | None = None) -> dict[str, object]:
    paths = sorted(
        (root / "results").glob(f"EXPERIMENT_*/ITERATION_*/{run_id or 'RUN_*'}/manifest.json")
    )
    findings: list[dict[str, str]] = []
    for manifest_path in paths:
        manifest = json.loads(manifest_path.read_text())
        run_dir = manifest_path.parent
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
