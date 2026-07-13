#!/usr/bin/env python3
"""Enforce branch-aware coverage floors for mutation and evidence-critical modules."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

THRESHOLDS = {
    "src/smairt/corrections.py": 95.0,
    "src/smairt/harnesses.py": 95.0,
    "src/smairt/integrity.py": 95.0,
    "src/smairt/locking.py": 95.0,
    "src/smairt/migrations.py": 95.0,
    "src/smairt/research.py": 95.0,
    "src/smairt/runner.py": 95.0,
    "src/smairt/safety.py": 95.0,
    "src/smairt/transactions.py": 95.0,
}


def main(path: Path = Path("coverage.json")) -> int:
    """Return nonzero and print every critical module below its configured floor."""
    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    files: dict[str, Any] = payload.get("files", {})
    failures: list[str] = []
    for module, minimum in THRESHOLDS.items():
        summary = files.get(module, {}).get("summary")
        if not isinstance(summary, dict):
            failures.append(f"{module}: absent from coverage report")
            continue
        actual = float(summary["percent_covered"])
        if actual < minimum:
            failures.append(f"{module}: {actual:.2f}% < {minimum:.2f}%")
    if failures:
        print("Critical-module coverage gate failed:", file=sys.stderr)
        print("\n".join(f"- {failure}" for failure in failures), file=sys.stderr)
        return 1
    print("Critical-module coverage gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
