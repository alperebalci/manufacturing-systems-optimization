from __future__ import annotations

import heapq
from collections import deque
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SimulationResult:
    wip_limit: int
    throughput_per_hour: float
    mean_cycle_time: float
    mean_wip: float
    contribution_per_hour: float


@dataclass(frozen=True)
class ConwipOptimizationResult:
    best: SimulationResult
    candidates: tuple[SimulationResult, ...]


def generate_service_scenarios(
    replications: int = 12,
    jobs: int = 700,
    station_means_min: tuple[float, ...] = (3.8, 4.5, 3.4),
    cv: float = 0.22,
    seed: int = 42,
) -> tuple[np.ndarray, ...]:
    rng = np.random.default_rng(seed)
    scenarios = []
    for _ in range(replications):
        arr = np.zeros((jobs, len(station_means_min)))
        for s, mean in enumerate(station_means_min):
            sigma2 = np.log(1.0 + cv**2)
            mu = np.log(mean) - 0.5 * sigma2
            arr[:, s] = rng.lognormal(mu, np.sqrt(sigma2), size=jobs)
        scenarios.append(arr)
    return tuple(scenarios)


def simulate_conwip(
    service_times: np.ndarray,
    wip_limit: int,
    warmup_completions: int = 80,
    measurement_completions: int = 320,
    unit_contribution: float = 18.0,
    wip_cost_per_unit_hour: float = 0.9,
    cycle_time_cost_per_hour: float = 1.8,
) -> SimulationResult:
    if wip_limit < 1:
        raise ValueError("wip_limit must be >= 1")

    n_jobs, n_stations = service_times.shape
    target = warmup_completions + measurement_completions
    if n_jobs < target + wip_limit + 5:
        raise ValueError("service_times does not contain enough jobs")

    queues = [deque() for _ in range(n_stations)]
    busy = [False] * n_stations
    events: list[tuple[float, int, int]] = []
    release_time: dict[int, float] = {}
    next_job = 0
    completed = 0
    current_wip = 0
    measure_start: float | None = None
    last_event_time = 0.0
    wip_area = 0.0
    measured_cycle_times: list[float] = []

    def start_if_possible(station: int, now: float) -> None:
        nonlocal busy
        if not busy[station] and queues[station]:
            job = queues[station].popleft()
            busy[station] = True
            finish = now + float(service_times[job, station])
            heapq.heappush(events, (finish, station, job))

    def release(now: float) -> None:
        nonlocal next_job, current_wip
        if next_job >= n_jobs:
            return
        job = next_job
        next_job += 1
        current_wip += 1
        release_time[job] = now
        queues[0].append(job)
        start_if_possible(0, now)

    for _ in range(wip_limit):
        release(0.0)

    while completed < target:
        time, station, job = heapq.heappop(events)
        if measure_start is not None:
            wip_area += current_wip * (time - last_event_time)
        last_event_time = time
        busy[station] = False

        if station == n_stations - 1:
            completed += 1
            current_wip -= 1
            if completed == warmup_completions:
                measure_start = time
                wip_area = 0.0
                measured_cycle_times.clear()
            elif completed > warmup_completions:
                measured_cycle_times.append(time - release_time[job])
            if completed < target:
                release(time)
        else:
            queues[station + 1].append(job)
            start_if_possible(station + 1, time)

        start_if_possible(station, time)

    assert measure_start is not None
    measurement_hours = (last_event_time - measure_start) / 60.0
    throughput = measurement_completions / measurement_hours
    mean_cycle = float(np.mean(measured_cycle_times))
    mean_wip = wip_area / max(last_event_time - measure_start, 1e-12)
    contribution = (
        throughput * unit_contribution
        - mean_wip * wip_cost_per_unit_hour
        - (mean_cycle / 60.0) * cycle_time_cost_per_hour * throughput
    )
    return SimulationResult(wip_limit, throughput, mean_cycle, mean_wip, contribution)


def optimize_conwip(
    wip_candidates: tuple[int, ...] = tuple(range(2, 13)),
    scenarios: tuple[np.ndarray, ...] | None = None,
) -> ConwipOptimizationResult:
    if scenarios is None:
        scenarios = generate_service_scenarios()

    results: list[SimulationResult] = []
    for wip in wip_candidates:
        reps = [simulate_conwip(s, wip) for s in scenarios]
        results.append(
            SimulationResult(
                wip_limit=wip,
                throughput_per_hour=float(np.mean([r.throughput_per_hour for r in reps])),
                mean_cycle_time=float(np.mean([r.mean_cycle_time for r in reps])),
                mean_wip=float(np.mean([r.mean_wip for r in reps])),
                contribution_per_hour=float(np.mean([r.contribution_per_hour for r in reps])),
            )
        )
    best = max(results, key=lambda r: r.contribution_per_hour)
    return ConwipOptimizationResult(best=best, candidates=tuple(results))
