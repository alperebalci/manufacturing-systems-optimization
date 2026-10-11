from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations, product
from math import inf


@dataclass(frozen=True)
class ToolingJob:
    job_id: str
    tool: str
    eligible_machines: tuple[str, ...]
    processing_time: dict[str, float]


@dataclass(frozen=True)
class ToolingScheduleResult:
    objective: float
    makespan: float
    total_changeover: float
    machine_sequences: dict[str, tuple[str, ...]]
    machine_completion: dict[str, float]


def _sequence_time(
    sequence: tuple[int, ...],
    machine: str,
    jobs: tuple[ToolingJob, ...],
    tool_change: dict[tuple[str, str], float],
) -> tuple[float, float]:
    elapsed = 0.0
    change = 0.0
    previous_tool: str | None = None
    for j in sequence:
        job = jobs[j]
        if previous_tool is not None and previous_tool != job.tool:
            dt = float(tool_change.get((previous_tool, job.tool), 0.0))
            elapsed += dt
            change += dt
        elapsed += float(job.processing_time[machine])
        previous_tool = job.tool
    return elapsed, change


def optimize_exact(
    machines: tuple[str, ...],
    jobs: tuple[ToolingJob, ...],
    tool_change: dict[tuple[str, str], float],
    changeover_weight: float = 0.35,
) -> ToolingScheduleResult:
    """Exact assignment + sequencing enumeration for intentionally small fixtures."""

    if len(jobs) > 8:
        raise ValueError("Exact tooling scheduler is intentionally limited to <= 8 jobs")

    machine_pos = {m: i for i, m in enumerate(machines)}
    options: list[tuple[int, ...]] = []
    for job in jobs:
        eligible = tuple(machine_pos[m] for m in job.eligible_machines if m in machine_pos)
        if not eligible:
            raise ValueError(f"Job {job.job_id} has no eligible machine")
        options.append(eligible)

    best_obj = inf
    best_result: ToolingScheduleResult | None = None

    for assignment in product(*options):
        assigned = [tuple(j for j, a in enumerate(assignment) if a == m) for m in range(len(machines))]
        sequence_sets = [tuple(permutations(js)) if js else ((),) for js in assigned]
        for chosen_sequences in product(*sequence_sets):
            completion: dict[str, float] = {}
            total_change = 0.0
            for m_idx, machine in enumerate(machines):
                elapsed, change = _sequence_time(chosen_sequences[m_idx], machine, jobs, tool_change)
                completion[machine] = elapsed
                total_change += change
            makespan = max(completion.values(), default=0.0)
            objective = makespan + changeover_weight * total_change
            if objective < best_obj - 1e-12:
                best_obj = objective
                best_result = ToolingScheduleResult(
                    objective=objective,
                    makespan=makespan,
                    total_changeover=total_change,
                    machine_sequences={
                        machines[m_idx]: tuple(jobs[j].job_id for j in chosen_sequences[m_idx])
                        for m_idx in range(len(machines))
                    },
                    machine_completion=completion,
                )

    assert best_result is not None
    return best_result


def demo_instance() -> tuple[tuple[str, ...], tuple[ToolingJob, ...], dict[tuple[str, str], float]]:
    machines = ("Press-1", "Press-2")
    jobs = (
        ToolingJob("J1", "Die-A", machines, {"Press-1": 3.2, "Press-2": 3.8}),
        ToolingJob("J2", "Die-B", ("Press-1",), {"Press-1": 2.4}),
        ToolingJob("J3", "Die-A", machines, {"Press-1": 2.7, "Press-2": 2.5}),
        ToolingJob("J4", "Die-C", ("Press-2",), {"Press-2": 3.0}),
        ToolingJob("J5", "Die-B", machines, {"Press-1": 2.1, "Press-2": 2.6}),
        ToolingJob("J6", "Die-C", machines, {"Press-1": 3.4, "Press-2": 2.8}),
    )
    tool_change = {
        ("Die-A", "Die-B"): 0.8,
        ("Die-B", "Die-A"): 0.7,
        ("Die-A", "Die-C"): 1.0,
        ("Die-C", "Die-A"): 0.9,
        ("Die-B", "Die-C"): 0.6,
        ("Die-C", "Die-B"): 0.65,
    }
    return machines, jobs, tool_change
