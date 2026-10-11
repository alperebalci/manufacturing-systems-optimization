"""Case 01 — integrated heterogeneous production assignment and preventive maintenance.

The MILP jointly assigns jobs to machines, selects preventive maintenance (PM),
and buys overtime when regular shift capacity is insufficient. Failure-risk exposure
is job/machine specific and PM reduces that exposure through linearized interaction
variables.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from .validation import make_audit, pct_improvement


@dataclass(frozen=True)
class Instance:
    processing_hours: np.ndarray
    variable_cost: np.ndarray
    failure_risk_cost: np.ndarray
    maintenance_duration: np.ndarray
    maintenance_cost: np.ndarray
    regular_capacity: np.ndarray
    overtime_cost: np.ndarray
    pm_risk_reduction: float = 0.72
    max_overtime: float = 6.0


def demo_instance() -> Instance:
    return Instance(
        processing_hours=np.array([
            [4.0, 5.2], [3.1, 4.4], [5.8, 4.1], [2.7, 3.2],
            [4.6, 3.6], [3.4, 4.2], [4.1, 3.9], [2.9, 3.5],
        ]),
        variable_cost=np.array([
            [96, 111], [74, 91], [139, 112], [67, 73],
            [110, 92], [83, 101], [103, 95], [70, 82],
        ], dtype=float),
        failure_risk_cost=np.array([
            [38, 24], [32, 22], [62, 35], [26, 20],
            [55, 31], [41, 26], [49, 29], [30, 21],
        ], dtype=float),
        maintenance_duration=np.array([1.0, 0.75]),
        maintenance_cost=np.array([60.0, 55.0]),
        regular_capacity=np.array([14.0, 14.0]),
        overtime_cost=np.array([48.0, 44.0]),
    )


def _indices(jobs: int, machines: int):
    nx = jobs * machines
    pm0 = nx
    ot0 = pm0 + machines
    z0 = ot0 + machines
    n = z0 + nx
    return nx, pm0, ot0, z0, n


def solve(instance: Instance | None = None) -> dict:
    ins = instance or demo_instance()
    jobs, machines = ins.processing_hours.shape
    nx, pm0, ot0, z0, n = _indices(jobs, machines)

    c = np.zeros(n)
    c[:nx] = (ins.variable_cost + ins.failure_risk_cost).ravel()
    c[pm0:pm0 + machines] = ins.maintenance_cost
    c[ot0:ot0 + machines] = ins.overtime_cost
    c[z0:] = -(ins.pm_risk_reduction * ins.failure_risk_cost).ravel()

    integrality = np.zeros(n, dtype=int)
    integrality[:nx] = 1
    integrality[pm0:pm0 + machines] = 1
    integrality[z0:] = 1
    lb = np.zeros(n)
    ub = np.full(n, np.inf)
    ub[:nx] = 1
    ub[pm0:pm0 + machines] = 1
    ub[ot0:ot0 + machines] = ins.max_overtime
    ub[z0:] = 1

    rows, lo, hi = [], [], []

    for j in range(jobs):
        row = np.zeros(n)
        row[j * machines:(j + 1) * machines] = 1
        rows.append(row); lo.append(1); hi.append(1)

    for m in range(machines):
        row = np.zeros(n)
        for j in range(jobs):
            row[j * machines + m] = ins.processing_hours[j, m]
        row[pm0 + m] = ins.maintenance_duration[m]
        row[ot0 + m] = -1
        rows.append(row); lo.append(-np.inf); hi.append(ins.regular_capacity[m])

    for j in range(jobs):
        for m in range(machines):
            x = j * machines + m
            z = z0 + x
            row = np.zeros(n); row[z] = 1; row[x] = -1
            rows.append(row); lo.append(-np.inf); hi.append(0)
            row = np.zeros(n); row[z] = 1; row[pm0 + m] = -1
            rows.append(row); lo.append(-np.inf); hi.append(0)
            row = np.zeros(n); row[z] = -1; row[x] = 1; row[pm0 + m] = 1
            rows.append(row); lo.append(-np.inf); hi.append(1)

    result = milp(
        c=c,
        integrality=integrality,
        bounds=Bounds(lb, ub),
        constraints=LinearConstraint(np.vstack(rows), np.array(lo), np.array(hi)),
        options={"time_limit": 10.0},
    )
    if not result.success:
        raise RuntimeError(result.message)

    assignment_matrix = np.rint(result.x[:nx]).astype(int).reshape(jobs, machines)
    assignment = assignment_matrix.argmax(axis=1)
    pm = np.rint(result.x[pm0:pm0 + machines]).astype(int)
    overtime = result.x[ot0:ot0 + machines]
    loads = np.array([
        sum(ins.processing_hours[j, m] * assignment_matrix[j, m] for j in range(jobs))
        + pm[m] * ins.maintenance_duration[m]
        for m in range(machines)
    ])
    audit = validate(ins, assignment_matrix, pm, overtime)
    return {
        "assignment": assignment,
        "assignment_matrix": assignment_matrix,
        "preventive_maintenance": pm,
        "overtime_hours": overtime,
        "machine_loads": loads,
        "total_cost": float(result.fun),
        "audit": audit,
    }


def baseline(instance: Instance | None = None) -> dict:
    ins = instance or demo_instance()
    direct = ins.variable_cost + ins.failure_risk_cost
    assignment = direct.argmin(axis=1)
    machines = direct.shape[1]
    loads = np.array([
        sum(ins.processing_hours[j, m] for j in range(len(assignment)) if assignment[j] == m)
        for m in range(machines)
    ])
    overtime = np.maximum(0.0, loads - ins.regular_capacity)
    if np.any(overtime > ins.max_overtime + 1e-9):
        for m in range(machines):
            while overtime[m] > ins.max_overtime + 1e-9:
                candidates = [j for j, a in enumerate(assignment) if a == m]
                j = min(candidates, key=lambda k: direct[k, 1 - m] - direct[k, m])
                assignment[j] = 1 - m
                loads = np.array([
                    sum(ins.processing_hours[k, mm] for k in range(len(assignment)) if assignment[k] == mm)
                    for mm in range(machines)
                ])
                overtime = np.maximum(0.0, loads - ins.regular_capacity)
    cost = sum(direct[j, assignment[j]] for j in range(len(assignment))) + float(ins.overtime_cost @ overtime)
    return {"assignment": assignment, "overtime_hours": overtime, "total_cost": float(cost)}


def validate(ins: Instance, x: np.ndarray, pm: np.ndarray, overtime: np.ndarray):
    loads = np.array([
        np.sum(ins.processing_hours[:, m] * x[:, m]) + pm[m] * ins.maintenance_duration[m]
        for m in range(x.shape[1])
    ])
    checks = {
        "job_assignment": bool(np.all(x.sum(axis=1) == 1)),
        "binary_pm": bool(np.all(np.isin(pm, [0, 1]))),
        "capacity": bool(np.all(loads <= ins.regular_capacity + overtime + 1e-7)),
        "overtime_bound": bool(np.all(overtime <= ins.max_overtime + 1e-7)),
    }
    return make_audit(checks, max_capacity_violation=float(np.max(loads - ins.regular_capacity - overtime)))


def industrial_benchmark(instance: Instance | None = None) -> dict:
    ins = instance or demo_instance()
    opt = solve(ins)
    base = baseline(ins)
    return {
        "optimized_cost": opt["total_cost"],
        "baseline_cost": base["total_cost"],
        "cost_improvement_pct": pct_improvement(base["total_cost"], opt["total_cost"]),
        "pm_count": int(opt["preventive_maintenance"].sum()),
        "overtime_hours": float(opt["overtime_hours"].sum()),
        "audit_passed": opt["audit"].passed,
    }


def sensitivity(instance: Instance | None = None, risk_multipliers=(0.5, 1.0, 1.5, 2.0)) -> list[dict]:
    ins = instance or demo_instance()
    rows = []
    for mult in risk_multipliers:
        scenario = replace(ins, failure_risk_cost=ins.failure_risk_cost * mult)
        result = solve(scenario)
        rows.append({"risk_multiplier": mult, "cost": result["total_cost"], "pm_count": int(result["preventive_maintenance"].sum())})
    return rows


if __name__ == "__main__":
    print(industrial_benchmark())
