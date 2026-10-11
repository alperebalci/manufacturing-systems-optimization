from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp


@dataclass(frozen=True)
class Worker:
    name: str
    qualified_stations: frozenset[str]
    ergonomic_tolerance: float


@dataclass(frozen=True)
class Station:
    name: str
    ergonomic_load: float


@dataclass(frozen=True)
class RotationResult:
    objective: float
    assignment: dict[tuple[int, str], str]
    worker_exposure: dict[str, float]
    worker_excess: dict[str, float]
    switches: int


def optimize_rotation(
    workers: tuple[Worker, ...],
    stations: tuple[Station, ...],
    periods: int = 4,
    excess_penalty: float = 80.0,
    switch_penalty: float = 1.5,
) -> RotationResult:
    W, S, P = len(workers), len(stations), periods
    if W < S:
        raise ValueError("Need at least as many workers as simultaneously staffed stations")

    x_count = P * W * S
    y_count = max(0, P - 1) * W * S
    excess_offset = x_count + y_count
    n = excess_offset + W

    def xidx(p: int, w: int, s: int) -> int:
        return (p * W + w) * S + s

    def yidx(p: int, w: int, s: int) -> int:
        return x_count + ((p - 1) * W + w) * S + s

    c = np.zeros(n)
    integrality = np.zeros(n)
    integrality[: excess_offset] = 1
    ub = np.full(n, np.inf)
    ub[: excess_offset] = 1.0

    for p in range(P):
        for w, worker in enumerate(workers):
            for s, station in enumerate(stations):
                idx = xidx(p, w, s)
                if station.name not in worker.qualified_stations:
                    ub[idx] = 0.0
    for p in range(1, P):
        for w in range(W):
            for s in range(S):
                c[yidx(p, w, s)] = switch_penalty
    c[excess_offset:] = excess_penalty

    constraints: list[LinearConstraint] = []

    A_station = np.zeros((P * S, n))
    row = 0
    for p in range(P):
        for s in range(S):
            for w in range(W):
                A_station[row, xidx(p, w, s)] = 1.0
            row += 1
    constraints.append(LinearConstraint(A_station, np.ones(P * S), np.ones(P * S)))

    A_worker = np.zeros((P * W, n))
    row = 0
    for p in range(P):
        for w in range(W):
            for s in range(S):
                A_worker[row, xidx(p, w, s)] = 1.0
            row += 1
    constraints.append(LinearConstraint(A_worker, -np.inf, np.ones(P * W)))

    A_ergo = np.zeros((W, n))
    for w, worker in enumerate(workers):
        for p in range(P):
            for s, station in enumerate(stations):
                A_ergo[w, xidx(p, w, s)] = station.ergonomic_load
        A_ergo[w, excess_offset + w] = -1.0
    constraints.append(
        LinearConstraint(A_ergo, -np.inf, np.array([w.ergonomic_tolerance for w in workers]))
    )

    rows = []
    for p in range(1, P):
        for w in range(W):
            for s in range(S):
                r = np.zeros(n)
                r[xidx(p, w, s)] = 1.0
                r[xidx(p - 1, w, s)] = -1.0
                r[yidx(p, w, s)] = -1.0
                rows.append(r)
    if rows:
        constraints.append(LinearConstraint(np.array(rows), -np.inf, np.zeros(len(rows))))

    res = milp(
        c=c,
        integrality=integrality,
        bounds=Bounds(np.zeros(n), ub),
        constraints=constraints,
        options={"time_limit": 15.0},
    )
    if not res.success or res.x is None:
        raise RuntimeError(f"Worker-rotation MILP failed: {res.message}")

    assignment: dict[tuple[int, str], str] = {}
    exposure = {w.name: 0.0 for w in workers}
    switches = 0
    for p in range(P):
        for s, station in enumerate(stations):
            for w, worker in enumerate(workers):
                if res.x[xidx(p, w, s)] > 0.5:
                    assignment[(p, station.name)] = worker.name
                    exposure[worker.name] += station.ergonomic_load
                    break
    for p in range(1, P):
        for w in range(W):
            for s in range(S):
                switches += int(res.x[yidx(p, w, s)] > 0.5)

    excess = {workers[w].name: float(res.x[excess_offset + w]) for w in range(W)}
    return RotationResult(float(res.fun), assignment, exposure, excess, switches)


def demo_instance() -> tuple[tuple[Worker, ...], tuple[Station, ...]]:
    workers = (
        Worker("Ayse", frozenset({"Load", "Assembly", "Inspect"}), 12.0),
        Worker("Bora", frozenset({"Load", "Machine", "Assembly"}), 12.5),
        Worker("Cem", frozenset({"Machine", "Assembly", "Inspect"}), 11.5),
        Worker("Deniz", frozenset({"Load", "Machine", "Inspect"}), 12.0),
        Worker("Ece", frozenset({"Load", "Assembly", "Inspect", "Machine"}), 11.0),
    )
    stations = (
        Station("Load", 2.0),
        Station("Machine", 2.8),
        Station("Assembly", 3.4),
        Station("Inspect", 1.6),
    )
    return workers, stations
