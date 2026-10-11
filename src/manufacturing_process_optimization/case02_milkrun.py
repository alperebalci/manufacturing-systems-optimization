from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp


@dataclass(frozen=True)
class Zone:
    name: str
    consumption_per_hour: float
    container_qty: float
    route_minutes: float
    line_side_capacity: float
    shortage_cost_per_unit_hour: float
    inventory_cost_per_unit_hour: float


@dataclass(frozen=True)
class MilkRunResult:
    objective: float
    selected_interval: dict[str, float]
    tugger_hours: float
    avg_inventory: float
    expected_shortage: float


def optimize_milkrun(
    zones: tuple[Zone, ...],
    candidate_intervals_h: tuple[float, ...] = (0.5, 1.0, 1.5, 2.0),
    tugger_hours_available: float = 3.2,
    route_cost_per_hour: float = 28.0,
    shift_hours: float = 8.0,
) -> MilkRunResult:
    """Choose one replenishment interval per zone with a binary MILP."""

    pairs = [(i, k) for i in range(len(zones)) for k in range(len(candidate_intervals_h))]
    n = len(pairs)
    c = np.zeros(n)
    tugger = np.zeros(n)
    avg_inv = np.zeros(n)
    shortage = np.zeros(n)

    for idx, (i, k) in enumerate(pairs):
        z = zones[i]
        interval = candidate_intervals_h[k]
        route_frequency = shift_hours / interval
        tugger[idx] = route_frequency * z.route_minutes / 60.0
        cycle_demand = z.consumption_per_hour * interval
        avg_inv[idx] = min(z.line_side_capacity, cycle_demand) / 2.0
        shortage[idx] = max(0.0, cycle_demand - z.line_side_capacity)
        c[idx] = (
            route_cost_per_hour * tugger[idx]
            + z.inventory_cost_per_unit_hour * avg_inv[idx] * shift_hours
            + z.shortage_cost_per_unit_hour * shortage[idx] * shift_hours
        )

    Aeq = np.zeros((len(zones), n))
    for idx, (i, _) in enumerate(pairs):
        Aeq[i, idx] = 1.0

    constraints = [
        LinearConstraint(Aeq, np.ones(len(zones)), np.ones(len(zones))),
        LinearConstraint(tugger.reshape(1, -1), -np.inf, tugger_hours_available),
    ]
    res = milp(
        c=c,
        integrality=np.ones(n),
        bounds=Bounds(np.zeros(n), np.ones(n)),
        constraints=constraints,
        options={"time_limit": 10.0},
    )
    if not res.success or res.x is None:
        raise RuntimeError(f"Milk-run MILP failed: {res.message}")

    selected: dict[str, float] = {}
    total_tugger = total_inventory = total_shortage = 0.0
    for idx, (i, k) in enumerate(pairs):
        if res.x[idx] > 0.5:
            selected[zones[i].name] = candidate_intervals_h[k]
            total_tugger += tugger[idx]
            total_inventory += avg_inv[idx]
            total_shortage += shortage[idx]

    return MilkRunResult(float(res.fun), selected, total_tugger, total_inventory, total_shortage)


def baseline_hourly(zones: tuple[Zone, ...], shift_hours: float = 8.0) -> MilkRunResult:
    interval = 1.0
    tugger = sum(shift_hours * z.route_minutes / 60.0 for z in zones)
    inv = sum(min(z.line_side_capacity, z.consumption_per_hour * interval) / 2.0 for z in zones)
    shortage = sum(max(0.0, z.consumption_per_hour * interval - z.line_side_capacity) for z in zones)
    return MilkRunResult(float("nan"), {z.name: interval for z in zones}, tugger, inv, shortage)


def demo_instance() -> tuple[Zone, ...]:
    return (
        Zone("Welding", 36, 18, 9, 48, 18, 0.08),
        Zone("Assembly", 52, 26, 12, 70, 22, 0.07),
        Zone("Packaging", 24, 12, 7, 32, 14, 0.06),
        Zone("Machining", 30, 15, 10, 42, 20, 0.09),
    )
