from __future__ import annotations

from itertools import combinations, product
from typing import Mapping, Sequence

import numpy as np
import pandas as pd


def full_factorial(
    levels: Mapping[str, tuple[float, float]],
) -> pd.DataFrame:
    """Create a two-level full-factorial design with coded and actual columns."""

    if not levels:
        raise ValueError("levels must contain at least one factor")

    factors = list(levels)
    for factor, bounds in levels.items():
        if len(bounds) != 2 or bounds[0] >= bounds[1]:
            raise ValueError(
                f"{factor} must have strictly increasing (low, high) levels"
            )

    coded_rows = list(product((-1.0, 1.0), repeat=len(factors)))
    data: dict[str, list[float]] = {}

    for index, factor in enumerate(factors):
        low, high = levels[factor]
        codes = [row[index] for row in coded_rows]
        data[f"{factor}_code"] = codes
        data[factor] = [low if code < 0 else high for code in codes]

    return pd.DataFrame(data)


def factorial_effects(
    design: pd.DataFrame,
    response: Sequence[float],
    factors: Sequence[str],
) -> pd.Series:
    """Estimate all factorial effects for a balanced two-level full factorial."""

    y = np.asarray(response, dtype=float)
    if len(design) != len(y):
        raise ValueError("design and response must have the same number of rows")
    if len(y) == 0:
        raise ValueError("response must not be empty")

    codes: dict[str, np.ndarray] = {}
    for factor in factors:
        column = f"{factor}_code"
        if column not in design:
            raise ValueError(f"missing coded factor column: {column}")
        values = design[column].to_numpy(dtype=float)
        if not np.all(np.isin(values, (-1.0, 1.0))):
            raise ValueError(f"{column} must contain only -1 and +1")
        codes[factor] = values

    effects: dict[str, float] = {}
    for order in range(1, len(factors) + 1):
        for term in combinations(factors, order):
            contrast = np.ones(len(y), dtype=float)
            for factor in term:
                contrast *= codes[factor]
            coefficient = float(np.mean(y * contrast))
            effects[":".join(term)] = 2.0 * coefficient

    return pd.Series(effects, name="effect")


def recommend_factorial_setting(
    design: pd.DataFrame,
    response: Sequence[float],
    factors: Sequence[str],
    *,
    minimize: bool = True,
) -> dict[str, float]:
    """Choose the best observed factorial setting using replicated mean response."""

    y = np.asarray(response, dtype=float)
    if len(design) != len(y):
        raise ValueError("design and response must have the same number of rows")

    frame = design[list(factors)].copy()
    frame["response"] = y
    grouped = (
        frame.groupby(list(factors), as_index=False, dropna=False)["response"]
        .mean()
        .sort_values("response", ascending=minimize)
    )
    best = grouped.iloc[0]

    result = {factor: float(best[factor]) for factor in factors}
    result["mean_response"] = float(best["response"])
    return result


def individuals_control_chart(
    values: Sequence[float],
    *,
    baseline_count: int | None = None,
    sigma_multiplier: float = 3.0,
) -> dict[str, object]:
    """Build an Individuals chart using the average-moving-range sigma estimate."""

    x = np.asarray(values, dtype=float)
    if x.ndim != 1 or len(x) < 3:
        raise ValueError("values must contain at least three observations")

    if baseline_count is None:
        baseline_count = len(x)
    if baseline_count < 3 or baseline_count > len(x):
        raise ValueError("baseline_count must be between 3 and len(values)")
    if sigma_multiplier <= 0:
        raise ValueError("sigma_multiplier must be positive")

    baseline = x[:baseline_count]
    moving_ranges = np.abs(np.diff(baseline))
    mean_moving_range = float(np.mean(moving_ranges))
    sigma_hat = mean_moving_range / 1.128

    if sigma_hat <= 0:
        raise ValueError("baseline variation must be positive")

    center = float(np.mean(baseline))
    lcl = center - sigma_multiplier * sigma_hat
    ucl = center + sigma_multiplier * sigma_hat
    out_of_control = (x < lcl) | (x > ucl)

    return {
        "center_line": center,
        "sigma_hat": sigma_hat,
        "lcl": float(lcl),
        "ucl": float(ucl),
        "out_of_control": out_of_control,
        "out_of_control_indices": np.flatnonzero(out_of_control),
    }


def process_capability(
    values: Sequence[float],
    *,
    lower_spec: float,
    upper_spec: float,
) -> dict[str, float]:
    """Compute Cp and Cpk from a stable process sample."""

    x = np.asarray(values, dtype=float)
    if x.ndim != 1 or len(x) < 2:
        raise ValueError("values must contain at least two observations")
    if lower_spec >= upper_spec:
        raise ValueError("lower_spec must be smaller than upper_spec")

    mean = float(np.mean(x))
    std = float(np.std(x, ddof=1))
    if std <= 0:
        raise ValueError("sample standard deviation must be positive")

    cp = (upper_spec - lower_spec) / (6.0 * std)
    cpu = (upper_spec - mean) / (3.0 * std)
    cpl = (mean - lower_spec) / (3.0 * std)
    cpk = min(cpu, cpl)

    return {
        "mean": mean,
        "std": std,
        "cp": float(cp),
        "cpk": float(cpk),
        "cpu": float(cpu),
        "cpl": float(cpl),
    }
