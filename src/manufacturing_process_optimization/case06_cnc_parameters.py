from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import differential_evolution


@dataclass(frozen=True)
class CNCConfig:
    diameter_mm: float = 60.0
    cutting_length_mm: float = 180.0
    machine_rate_per_min: float = 1.2
    tool_cost: float = 22.0
    energy_cost_per_kwh: float = 0.16
    max_power_kw: float = 11.0
    max_roughness_um: float = 3.2
    tool_change_minutes: float = 3.5


@dataclass(frozen=True)
class CNCResult:
    objective: float
    cutting_speed_m_min: float
    feed_mm_rev: float
    depth_mm: float
    machining_minutes: float
    tool_life_minutes: float
    roughness_um: float
    power_kw: float
    material_removal_rate: float


def _metrics(x: np.ndarray, cfg: CNCConfig) -> dict[str, float]:
    speed, feed, depth = map(float, x)
    rpm = 1000.0 * speed / (np.pi * cfg.diameter_mm)
    feed_rate = feed * rpm
    machining_min = cfg.cutting_length_mm / max(feed_rate, 1e-9)

    tool_life = 8.0e8 / (speed**2.35 * feed**0.55 * depth**0.22)
    roughness = 0.42 + 17.0 * feed**1.55 + 0.015 * depth**1.2
    mrr = speed * feed * depth * 1000.0
    power_kw = 1.1 + 0.0000075 * mrr

    tool_fraction = machining_min / max(tool_life, 1e-9)
    machine_cost = cfg.machine_rate_per_min * machining_min
    tool_cost = cfg.tool_cost * tool_fraction
    tool_change_cost = cfg.machine_rate_per_min * cfg.tool_change_minutes * tool_fraction
    energy_cost = cfg.energy_cost_per_kwh * power_kw * machining_min / 60.0
    quality_risk = 0.8 * max(0.0, roughness - 0.85 * cfg.max_roughness_um) ** 2

    return {
        "machining_min": machining_min,
        "tool_life": tool_life,
        "roughness": roughness,
        "mrr": mrr,
        "power_kw": power_kw,
        "base_cost": machine_cost + tool_cost + tool_change_cost + energy_cost + quality_risk,
    }


def optimize_cnc(cfg: CNCConfig | None = None, seed: int = 42) -> CNCResult:
    if cfg is None:
        cfg = CNCConfig()
    bounds = [(90.0, 280.0), (0.08, 0.38), (0.5, 3.2)]

    def objective(x: np.ndarray) -> float:
        m = _metrics(x, cfg)
        penalty = 0.0
        penalty += 500.0 * max(0.0, m["power_kw"] - cfg.max_power_kw) ** 2
        penalty += 120.0 * max(0.0, m["roughness"] - cfg.max_roughness_um) ** 2
        penalty += 20.0 * max(0.0, 2.0 - m["tool_life"]) ** 2
        return m["base_cost"] + penalty

    res = differential_evolution(
        objective,
        bounds=bounds,
        seed=seed,
        polish=True,
        tol=1e-9,
        maxiter=350,
        popsize=15,
    )
    if not res.success:
        raise RuntimeError(f"CNC optimization failed: {res.message}")

    m = _metrics(res.x, cfg)
    if m["power_kw"] > cfg.max_power_kw + 1e-4 or m["roughness"] > cfg.max_roughness_um + 1e-4:
        raise RuntimeError("Optimizer returned a penalized but infeasible CNC solution")

    return CNCResult(
        objective=float(m["base_cost"]),
        cutting_speed_m_min=float(res.x[0]),
        feed_mm_rev=float(res.x[1]),
        depth_mm=float(res.x[2]),
        machining_minutes=float(m["machining_min"]),
        tool_life_minutes=float(m["tool_life"]),
        roughness_um=float(m["roughness"]),
        power_kw=float(m["power_kw"]),
        material_removal_rate=float(m["mrr"]),
    )


def baseline_cnc(cfg: CNCConfig | None = None) -> CNCResult:
    if cfg is None:
        cfg = CNCConfig()
    x = np.array([160.0, 0.16, 1.5])
    m = _metrics(x, cfg)
    return CNCResult(
        objective=float(m["base_cost"]),
        cutting_speed_m_min=float(x[0]),
        feed_mm_rev=float(x[1]),
        depth_mm=float(x[2]),
        machining_minutes=float(m["machining_min"]),
        tool_life_minutes=float(m["tool_life"]),
        roughness_um=float(m["roughness"]),
        power_kw=float(m["power_kw"]),
        material_removal_rate=float(m["mrr"]),
    )
