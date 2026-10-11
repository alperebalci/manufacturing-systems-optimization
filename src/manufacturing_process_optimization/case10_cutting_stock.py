from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp


@dataclass(frozen=True)
class Pattern:
    source: str
    source_length: int
    counts: tuple[int, ...]
    waste: int


@dataclass(frozen=True)
class CuttingStockResult:
    objective: float
    selected_patterns: tuple[tuple[Pattern, int], ...]
    produced: tuple[int, ...]
    excess: tuple[int, ...]
    new_bars: int
    remnants_used: int
    total_trim_waste: int


def generate_patterns(source: str, source_length: int, piece_lengths: tuple[int, ...]) -> tuple[Pattern, ...]:
    patterns: list[Pattern] = []

    def rec(i: int, remaining: int, counts: list[int]) -> None:
        if i == len(piece_lengths):
            if any(counts):
                used = sum(c * l for c, l in zip(counts, piece_lengths))
                patterns.append(Pattern(source, source_length, tuple(counts), source_length - used))
            return
        max_count = remaining // piece_lengths[i]
        for q in range(max_count + 1):
            counts.append(q)
            rec(i + 1, remaining - q * piece_lengths[i], counts)
            counts.pop()

    rec(0, source_length, [])
    unique = {(p.counts, p.waste): p for p in patterns}
    return tuple(unique.values())


def optimize_cutting_stock(
    piece_lengths: tuple[int, ...],
    demand: tuple[int, ...],
    new_bar_length: int = 6000,
    remnants: tuple[int, ...] = (3100, 2700, 1900),
    new_bar_cost: float = 42.0,
    waste_cost_per_mm: float = 0.002,
    excess_piece_cost: float = 5.0,
) -> CuttingStockResult:
    if len(piece_lengths) != len(demand):
        raise ValueError("piece_lengths and demand must align")

    new_patterns = generate_patterns("new", new_bar_length, piece_lengths)
    remnant_groups: list[list[int]] = []

    patterns = list(new_patterns)
    for r_idx, length in enumerate(remnants):
        group: list[int] = []
        for p in generate_patterns(f"remnant-{r_idx + 1}", length, piece_lengths):
            group.append(len(patterns))
            patterns.append(p)
        remnant_groups.append(group)

    P = len(patterns)
    K = len(piece_lengths)
    n = P + K
    c = np.zeros(n)
    integrality = np.ones(n)
    ub = np.full(n, np.inf)

    for j, p in enumerate(patterns):
        purchase = new_bar_cost if p.source == "new" else 0.0
        c[j] = purchase + waste_cost_per_mm * p.waste
        if p.source != "new":
            ub[j] = 1.0
    c[P:] = excess_piece_cost

    A_demand = np.zeros((K, n))
    for j, p in enumerate(patterns):
        for k, q in enumerate(p.counts):
            A_demand[k, j] = q
    for k in range(K):
        A_demand[k, P + k] = -1.0

    constraints: list[LinearConstraint] = [
        LinearConstraint(A_demand, np.array(demand, dtype=float), np.array(demand, dtype=float))
    ]

    for group in remnant_groups:
        if group:
            row = np.zeros((1, n))
            row[0, group] = 1.0
            constraints.append(LinearConstraint(row, -np.inf, 1.0))

    res = milp(
        c=c,
        integrality=integrality,
        bounds=Bounds(np.zeros(n), ub),
        constraints=constraints,
        options={"time_limit": 15.0},
    )
    if not res.success or res.x is None:
        raise RuntimeError(f"Cutting-stock MILP failed: {res.message}")

    selected: list[tuple[Pattern, int]] = []
    produced = np.zeros(K, dtype=int)
    new_bars = remnants_used = trim = 0
    for j, p in enumerate(patterns):
        count = round(res.x[j])
        if count <= 0:
            continue
        selected.append((p, count))
        produced += count * np.array(p.counts, dtype=int)
        trim += count * p.waste
        if p.source == "new":
            new_bars += count
        else:
            remnants_used += count

    excess = tuple(round(v) for v in res.x[P:])
    return CuttingStockResult(
        objective=float(res.fun),
        selected_patterns=tuple(selected),
        produced=tuple(int(v) for v in produced),
        excess=excess,
        new_bars=new_bars,
        remnants_used=remnants_used,
        total_trim_waste=trim,
    )


def demo_instance() -> tuple[tuple[int, ...], tuple[int, ...]]:
    return (2350, 1800, 1250, 950), (7, 9, 8, 10)
