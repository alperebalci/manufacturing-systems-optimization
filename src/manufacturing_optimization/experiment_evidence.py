"""Export inspectable *small demo* evidence without claiming industrial-scale results.

This runner calls the existing case-specific demo benchmarks. It does NOT solve
the large synthetic fixtures and must not be cited as industrial scalability evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import time
from collections.abc import Callable, Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import scipy

from . import (
    case01_production_maintenance as c1,
    case02_milkrun as c2,
    case03_agv_assignment as c3,
    case04_worker_rotation as c4,
    case05_quality_mdp as c5,
    case06_cnc_process as c6,
    case07_tooling_scheduling as c7,
    case08_conwip as c8,
    case09_energy_scheduling as c9,
    case10_cutting_stock as c10,
)

CaseRunner = tuple[str, Callable[[], dict[str, Any]]]

CASE_RUNNERS: tuple[CaseRunner, ...] = (
    ("case01", c1.industrial_benchmark),
    ("case02", c2.industrial_benchmark),
    ("case03", c3.industrial_benchmark),
    ("case04", c4.industrial_benchmark),
    ("case05", c5.industrial_benchmark),
    ("case06", c6.industrial_benchmark),
    ("case07", c7.industrial_benchmark),
    ("case08", c8.industrial_benchmark),
    ("case09", c9.industrial_benchmark),
    ("case10", c10.industrial_benchmark),
)


def _json_safe(value: Any) -> Any:
    """Normalize numpy results and fail rather than publishing NaN/Infinity."""
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise TypeError("result keys must be strings")
        return {key: _json_safe(part) for key, part in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(part) for part in value]
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("nonfinite benchmark output")
        return value
    raise TypeError(f"unsupported result value type: {type(value).__name__}")


def collect_evidence(
    runners: Iterable[CaseRunner] | None = None,
    *,
    clock: Callable[[], float] = time.perf_counter,
    captured_at: str | None = None,
) -> dict[str, Any]:
    """Return one auditable, explicitly demo-scoped evidence record.

    `result_fingerprint` hashes only case IDs and numeric/policy results; it
    intentionally excludes elapsed times, collection timestamps, and machine
    identity so that repeated computations can be compared.
    """
    choices = tuple(CASE_RUNNERS if runners is None else runners)
    if not choices:
        raise ValueError("at least one case is required")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()

    for case_id, run in choices:
        if not case_id or case_id in seen:
            raise ValueError("case IDs must be nonempty and unique")
        seen.add(case_id)
        before = clock()
        raw_result = run()
        elapsed = clock() - before
        if not math.isfinite(elapsed) or elapsed < 0:
            raise ValueError("invalid elapsed runtime")
        if not isinstance(raw_result, dict):
            raise TypeError("a benchmark must return a result mapping")
        result = _json_safe(raw_result)
        audit_value = result.get("audit_passed")
        if audit_value is False:
            raise ValueError(f"{case_id}: reported feasibility audit failed")
        if audit_value is None:
            audit_status = "not_reported"
        elif audit_value is True:
            audit_status = "reported_pass"
        else:
            raise TypeError(f"{case_id}: audit_passed must be boolean when supplied")

        rows.append(
            {
                "case": case_id,
                "input_scope": "built-in demo inputs (not large industrial fixtures)",
                "audit_status": audit_status,
                "wall_time_seconds": elapsed,
                "result": result,
            }
        )

    fingerprint_input = [
        {"case": row["case"], "result": row["result"]} for row in rows
    ]
    canonical = json.dumps(
        fingerprint_input, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    result_fingerprint = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    return {
        "schema_version": 1,
        "evidence_tier": "small_demo_validation",
        "industrial_scalability_evaluated": False,
        "source_kind": "built-in synthetic/demo instances",
        "claims": (
            "case-specific demo outputs and per-case runtime only; "
            "no controlled industrial speedup, generalization, or statistical significance claim"
        ),
        "input_fixture_note": (
            "The committed fixtures/manifest.json is maintained separately; "
            "this runner does not assert identity between those fixture payloads "
            "and the built-in demo instances."
        ),
        "captured_at_utc": (
            captured_at if captured_at is not None
            else datetime.now(timezone.utc).isoformat()
        ),
        "environment": {
            "python": platform.python_version(),
            "system": platform.platform(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "pandas": pd.__version__,
            "commit": os.environ.get("GITHUB_SHA", "not_recorded"),
        },
        "result_fingerprint": result_fingerprint,
        "audit_summary": (
            "all_reported_pass" if all(row["audit_status"] == "reported_pass" for row in rows)
            else "partial_not_reported"
        ),
        "cases": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("artifacts/manufacturing-demo-evidence.json")
    )
    args = parser.parse_args()
    report = collect_evidence()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"Wrote {len(report['cases'])} demo-case results to {args.output}; "
        f"audit={report['audit_summary']}; "
        "industrial scalability: NOT EVALUATED"
    )


if __name__ == "__main__":
    main()
