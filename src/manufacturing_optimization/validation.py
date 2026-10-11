from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Audit:
    passed: bool
    checks: dict[str, bool]
    details: dict[str, float | int | str]


def make_audit(checks: dict[str, bool], **details) -> Audit:
    return Audit(passed=all(checks.values()), checks=checks, details=details)


def pct_improvement(baseline: float, optimized: float, lower_is_better: bool = True) -> float:
    if abs(baseline) < 1e-12:
        return 0.0
    delta = baseline - optimized if lower_is_better else optimized - baseline
    return 100.0 * delta / abs(baseline)


def mean(values: Iterable[float]) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0
