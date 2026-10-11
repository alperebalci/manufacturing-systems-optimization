from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations
from math import inf


@dataclass(frozen=True)
class Job:
    job_id: str
    family: str
    processing_time: float
    due_date: float
    weight: float = 1.0


@dataclass(frozen=True)
class MaintenanceConfig:
    duration: float
    fixed_cost: float
    degradation_rate: float
    degradation_cost: float


@dataclass(frozen=True)
class ScheduleRow:
    item: str
    start: float
    finish: float
    family: str | None


@dataclass(frozen=True)
class ProductionMaintenanceResult:
    objective: float
    sequence: tuple[str, ...]
    maintenance_position: int
    weighted_tardiness: float
    setup_time: float
    degradation_cost: float
    rows: tuple[ScheduleRow, ...]


def _setup_time(prev_family: str | None, next_family: str, setup: dict[tuple[str, str], float]) -> float:
    if prev_family is None or prev_family == next_family:
        return 0.0
    return float(setup.get((prev_family, next_family), 0.0))


def evaluate_schedule(
    jobs: tuple[Job, ...],
    sequence: tuple[int, ...],
    maintenance_position: int,
    setup: dict[tuple[str, str], float],
    maintenance: MaintenanceConfig,
    setup_cost_per_hour: float = 1.0,
) -> ProductionMaintenanceResult:
    if not 0 <= maintenance_position <= len(sequence):
        raise ValueError("maintenance_position must be between 0 and number of jobs")

    t = 0.0
    prev_family: str | None = None
    degradation_age = 0.0
    weighted_tardiness = 0.0
    setup_hours = 0.0
    degradation_cost = 0.0
    rows: list[ScheduleRow] = []

    for position in range(len(sequence) + 1):
        if position == maintenance_position:
            rows.append(ScheduleRow("PM", t, t + maintenance.duration, None))
            t += maintenance.duration
            degradation_age = 0.0
            prev_family = None

        if position == len(sequence):
            break

        job = jobs[sequence[position]]
        st = _setup_time(prev_family, job.family, setup)
        t += st
        setup_hours += st

        start = t
        finish = start + job.processing_time
        rows.append(ScheduleRow(job.job_id, start, finish, job.family))
        t = finish

        degradation_age += job.processing_time
        degradation_cost += (
            maintenance.degradation_cost
            * maintenance.degradation_rate
            * degradation_age
            * job.processing_time
        )
        weighted_tardiness += job.weight * max(0.0, finish - job.due_date)
        prev_family = job.family

    objective = (
        weighted_tardiness
        + setup_cost_per_hour * setup_hours
        + maintenance.fixed_cost
        + degradation_cost
    )
    return ProductionMaintenanceResult(
        objective=objective,
        sequence=tuple(jobs[i].job_id for i in sequence),
        maintenance_position=maintenance_position,
        weighted_tardiness=weighted_tardiness,
        setup_time=setup_hours,
        degradation_cost=degradation_cost,
        rows=tuple(rows),
    )


def optimize_exact(
    jobs: tuple[Job, ...],
    setup: dict[tuple[str, str], float],
    maintenance: MaintenanceConfig,
    setup_cost_per_hour: float = 1.0,
) -> ProductionMaintenanceResult:
    """Globally solve the declared small instance by complete enumeration."""

    if len(jobs) > 9:
        raise ValueError("Exact enumeration is intentionally limited to <= 9 jobs")

    best: ProductionMaintenanceResult | None = None
    best_obj = inf
    for sequence in permutations(range(len(jobs))):
        for pm_position in range(len(jobs) + 1):
            result = evaluate_schedule(
                jobs,
                sequence,
                pm_position,
                setup,
                maintenance,
                setup_cost_per_hour,
            )
            if result.objective < best_obj - 1e-12:
                best_obj = result.objective
                best = result
    assert best is not None
    return best


def baseline_edd(
    jobs: tuple[Job, ...],
    setup: dict[tuple[str, str], float],
    maintenance: MaintenanceConfig,
    setup_cost_per_hour: float = 1.0,
) -> ProductionMaintenanceResult:
    order = tuple(sorted(range(len(jobs)), key=lambda i: jobs[i].due_date))
    pm_position = len(jobs) // 2
    return evaluate_schedule(jobs, order, pm_position, setup, maintenance, setup_cost_per_hour)


def demo_instance() -> tuple[tuple[Job, ...], dict[tuple[str, str], float], MaintenanceConfig]:
    jobs = (
        Job("J1", "A", 2.2, 5.5, 2.0),
        Job("J2", "B", 1.8, 7.0, 1.0),
        Job("J3", "A", 2.5, 9.0, 1.5),
        Job("J4", "C", 1.4, 6.2, 2.5),
        Job("J5", "B", 2.0, 11.0, 1.0),
    )
    setup = {
        ("A", "B"): 0.5,
        ("B", "A"): 0.4,
        ("A", "C"): 0.7,
        ("C", "A"): 0.6,
        ("B", "C"): 0.3,
        ("C", "B"): 0.35,
    }
    maintenance = MaintenanceConfig(
        duration=1.0,
        fixed_cost=1.2,
        degradation_rate=0.08,
        degradation_cost=1.6,
    )
    return jobs, setup, maintenance
