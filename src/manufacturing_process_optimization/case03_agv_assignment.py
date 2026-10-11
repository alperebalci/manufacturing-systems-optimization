from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp


@dataclass(frozen=True)
class Robot:
    name: str
    payload_capacity: float
    battery_budget: float
    speed_m_per_min: float
    available_minutes: float


@dataclass(frozen=True)
class TransportTask:
    task_id: str
    distance_m: float
    payload: float
    due_minute: float
    service_minutes: float
    priority: float = 1.0


@dataclass(frozen=True)
class AGVAssignmentResult:
    objective: float
    assignment: dict[str, str]
    emergency_tasks: tuple[str, ...]
    robot_load_minutes: dict[str, float]
    robot_battery_use: dict[str, float]


def optimize_assignment(
    robots: tuple[Robot, ...],
    tasks: tuple[TransportTask, ...],
    battery_per_meter: float = 0.002,
    lateness_cost_per_minute: float = 2.0,
    emergency_cost: float = 250.0,
) -> AGVAssignmentResult:
    """Assign independent transport tasks to heterogeneous robots.

    The model is intentionally an assignment layer, not a route sequencer. Estimated
    completion time is travel + service from a common dispatch epoch.
    """

    R, T = len(robots), len(tasks)
    x_count = R * T
    emergency_offset = x_count
    n = x_count + T

    c = np.zeros(n)
    time_use = np.zeros((R, n))
    battery_use = np.zeros((R, n))
    task_rows = np.zeros((T, n))
    ub = np.ones(n)

    for r, robot in enumerate(robots):
        for t, task in enumerate(tasks):
            idx = r * T + t
            task_rows[t, idx] = 1.0
            if task.payload > robot.payload_capacity:
                ub[idx] = 0.0
                continue
            round_trip = 2.0 * task.distance_m
            minutes = round_trip / robot.speed_m_per_min + task.service_minutes
            battery = round_trip * battery_per_meter
            estimated_lateness = max(0.0, minutes - task.due_minute)
            c[idx] = minutes + lateness_cost_per_minute * task.priority * estimated_lateness
            time_use[r, idx] = minutes
            battery_use[r, idx] = battery

    for t in range(T):
        idx = emergency_offset + t
        task_rows[t, idx] = 1.0
        c[idx] = emergency_cost * tasks[t].priority

    constraints: list[LinearConstraint] = [
        LinearConstraint(task_rows, np.ones(T), np.ones(T)),
    ]
    for r, robot in enumerate(robots):
        constraints.append(
            LinearConstraint(time_use[r : r + 1], -np.inf, robot.available_minutes)
        )
        constraints.append(
            LinearConstraint(battery_use[r : r + 1], -np.inf, robot.battery_budget)
        )

    res = milp(
        c=c,
        integrality=np.ones(n),
        bounds=Bounds(np.zeros(n), ub),
        constraints=constraints,
        options={"time_limit": 10.0},
    )
    if not res.success or res.x is None:
        raise RuntimeError(f"AGV assignment MILP failed: {res.message}")

    assignment: dict[str, str] = {}
    emergency: list[str] = []
    robot_minutes = {r.name: 0.0 for r in robots}
    robot_battery = {r.name: 0.0 for r in robots}
    for t, task in enumerate(tasks):
        if res.x[emergency_offset + t] > 0.5:
            emergency.append(task.task_id)
            continue
        for r, robot in enumerate(robots):
            idx = r * T + t
            if res.x[idx] > 0.5:
                assignment[task.task_id] = robot.name
                robot_minutes[robot.name] += time_use[r, idx]
                robot_battery[robot.name] += battery_use[r, idx]
                break

    return AGVAssignmentResult(
        objective=float(res.fun),
        assignment=assignment,
        emergency_tasks=tuple(emergency),
        robot_load_minutes=robot_minutes,
        robot_battery_use=robot_battery,
    )


def demo_instance() -> tuple[tuple[Robot, ...], tuple[TransportTask, ...]]:
    robots = (
        Robot("AMR-1", 450, 6.0, 75, 55),
        Robot("AMR-2", 300, 5.0, 82, 50),
        Robot("AGV-1", 700, 8.5, 60, 60),
    )
    tasks = (
        TransportTask("T1", 220, 240, 12, 2.0, 2.0),
        TransportTask("T2", 330, 420, 16, 2.5, 1.5),
        TransportTask("T3", 180, 120, 9, 1.5, 1.0),
        TransportTask("T4", 410, 620, 20, 3.0, 2.5),
        TransportTask("T5", 280, 200, 13, 2.0, 1.0),
        TransportTask("T6", 150, 280, 8, 1.0, 1.8),
    )
    return robots, tasks
