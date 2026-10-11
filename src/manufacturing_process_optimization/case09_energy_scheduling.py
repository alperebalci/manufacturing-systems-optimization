from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp


@dataclass(frozen=True)
class EnergyScheduleResult:
    objective: float
    production: np.ndarray
    inventory: np.ndarray
    machine_on: np.ndarray
    peak_kw: float
    energy_cost: float
    peak_cost: float
    holding_setup_cost: float


def optimize_energy_schedule(
    demand: np.ndarray,
    price_per_kwh: np.ndarray,
    capacity: float = 65.0,
    min_lot: float = 12.0,
    initial_inventory: float = 10.0,
    holding_cost: float = 0.18,
    setup_cost: float = 6.0,
    idle_kw: float = 5.0,
    variable_kw_per_unit: float = 0.22,
    period_hours: float = 1.0,
    demand_charge_per_kw: float = 3.8,
) -> EnergyScheduleResult:
    demand = np.asarray(demand, dtype=float)
    price = np.asarray(price_per_kwh, dtype=float)
    if demand.shape != price.shape:
        raise ValueError("demand and price vectors must have the same shape")
    T = len(demand)

    x0, i0, y0, pidx = 0, T, 2 * T, 3 * T
    n = 3 * T + 1
    c = np.zeros(n)
    integrality = np.zeros(n)
    integrality[y0 : y0 + T] = 1
    ub = np.full(n, np.inf)
    ub[y0 : y0 + T] = 1.0

    for t in range(T):
        c[x0 + t] = price[t] * variable_kw_per_unit * period_hours
        c[i0 + t] = holding_cost
        c[y0 + t] = setup_cost + price[t] * idle_kw * period_hours
    c[pidx] = demand_charge_per_kw

    constraints: list[LinearConstraint] = []

    A_bal = np.zeros((T, n))
    b_bal = demand.copy()
    for t in range(T):
        A_bal[t, x0 + t] = 1.0
        A_bal[t, i0 + t] = -1.0
        if t > 0:
            A_bal[t, i0 + t - 1] = 1.0
        else:
            b_bal[t] -= initial_inventory
    constraints.append(LinearConstraint(A_bal, b_bal, b_bal))

    A_cap = np.zeros((T, n))
    A_min = np.zeros((T, n))
    for t in range(T):
        A_cap[t, x0 + t] = 1.0
        A_cap[t, y0 + t] = -capacity
        A_min[t, x0 + t] = -1.0
        A_min[t, y0 + t] = min_lot
    constraints.append(LinearConstraint(A_cap, -np.inf, np.zeros(T)))
    constraints.append(LinearConstraint(A_min, -np.inf, np.zeros(T)))

    A_peak = np.zeros((T, n))
    for t in range(T):
        A_peak[t, x0 + t] = variable_kw_per_unit
        A_peak[t, y0 + t] = idle_kw
        A_peak[t, pidx] = -1.0
    constraints.append(LinearConstraint(A_peak, -np.inf, np.zeros(T)))

    A_terminal = np.zeros((1, n))
    A_terminal[0, i0 + T - 1] = 1.0
    constraints.append(LinearConstraint(A_terminal, 0.0, 0.0))

    res = milp(
        c=c,
        integrality=integrality,
        bounds=Bounds(np.zeros(n), ub),
        constraints=constraints,
        options={"time_limit": 10.0},
    )
    if not res.success or res.x is None:
        raise RuntimeError(f"Energy scheduling MILP failed: {res.message}")

    x = res.x[x0 : x0 + T]
    inv = res.x[i0 : i0 + T]
    y = np.rint(res.x[y0 : y0 + T]).astype(int)
    peak = float(res.x[pidx])
    energy_cost = float(np.sum(price * (variable_kw_per_unit * x + idle_kw * y) * period_hours))
    peak_cost = demand_charge_per_kw * peak
    hold_setup = float(holding_cost * np.sum(inv) + setup_cost * np.sum(y))
    return EnergyScheduleResult(
        objective=float(res.fun),
        production=x,
        inventory=inv,
        machine_on=y,
        peak_kw=peak,
        energy_cost=energy_cost,
        peak_cost=peak_cost,
        holding_setup_cost=hold_setup,
    )


def demo_instance() -> tuple[np.ndarray, np.ndarray]:
    demand = np.array([36, 42, 48, 34, 55, 44, 38, 46], dtype=float)
    price = np.array([0.11, 0.12, 0.15, 0.28, 0.31, 0.19, 0.13, 0.12], dtype=float)
    return demand, price
