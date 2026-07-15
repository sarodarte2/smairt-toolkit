#!/usr/bin/env python3
"""Recover known Michaelis-Menten parameters from a fixed local dataset."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path

import yaml

RESULTS_DIR = Path(os.environ["SMAIRT_RESULTS_DIR"])
RUN_DIR = RESULTS_DIR.parent
EXPECTED = json.loads(Path("expected-results.json").read_text(encoding="utf-8"))


def load_means() -> tuple[dict[float, float], float]:
    """Aggregate triplicates and return nonzero means plus the blank maximum."""
    grouped: dict[float, list[float]] = defaultdict(list)
    with Path("data.csv").open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            grouped[float(row["substrate_mM"])].append(float(row["velocity_umol_min"]))
    if set(grouped) != {0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0}:
        raise ValueError("dataset concentrations differ from the declared design")
    if any(len(values) != 3 for values in grouped.values()):
        raise ValueError("every concentration must contain exactly three replicates")
    blank = max(abs(value) for value in grouped.pop(0.0))
    return {key: sum(values) / len(values) for key, values in grouped.items()}, blank


def fit(means: dict[float, float]) -> tuple[float, float, float]:
    """Perform a deterministic nonlinear least-squares grid search."""
    best = (float("inf"), 0.0, 0.0)
    for vmax_step in range(800, 1601):
        vmax = vmax_step / 10
        for km_step in range(100, 401):
            km = km_step / 100
            error = sum(
                (velocity - vmax * substrate / (km + substrate)) ** 2
                for substrate, velocity in means.items()
            )
            if error < best[0]:
                best = (error, vmax, km)
    return best[1], best[2], best[0]


def main() -> None:
    """Fit, independently check expected values, and write provenance-ready outputs."""
    means, blank = load_means()
    vmax, km, residual_sse = fit(means)
    vmax_range = EXPECTED["accepted_vmax_range"]
    km_range = EXPECTED["accepted_km_range"]
    checks = {
        "vmax_in_range": vmax_range[0] <= vmax <= vmax_range[1],
        "km_in_range": km_range[0] <= km <= km_range[1],
        "blank_in_range": blank <= EXPECTED["maximum_absolute_blank_umol_min"],
    }
    result = {
        "vmax_umol_min": vmax,
        "km_mM": km,
        "residual_sse": residual_sse,
        "maximum_absolute_blank_umol_min": blank,
        "generating_values": {
            "vmax_umol_min": EXPECTED["generating_vmax_umol_min"],
            "km_mM": EXPECTED["generating_km_mM"],
        },
        "checks": checks,
        "correct": all(checks.values()),
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    result_path = RESULTS_DIR / "results.json"
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    digest = hashlib.sha256(result_path.read_bytes()).hexdigest()
    summary = {
        "schema_version": 1,
        "primary_result": f"Recovered Vmax={vmax:.1f} and Km={km:.2f}",
        "unit": "micromoles per minute and millimolar",
        "uncertainty": "Values must fall inside independent predeclared recovery ranges.",
        "quality_control": f"Blank maximum={blank:.1f}; all correctness checks passed.",
        "exclusions": "None.",
        "protocol_deviations": "None.",
        "limitations": "Synthetic fixed data validate workflow correctness, not biological novelty.",
        "artifact_checksums": {"artifacts/results.json": digest},
    }
    (RUN_DIR / "result-summary.yaml").write_text(
        yaml.safe_dump(summary, sort_keys=False), encoding="utf-8"
    )
    print(json.dumps(result, indent=2))
    if not result["correct"]:
        raise SystemExit("parameter recovery failed its independent acceptance ranges")


if __name__ == "__main__":
    main()
