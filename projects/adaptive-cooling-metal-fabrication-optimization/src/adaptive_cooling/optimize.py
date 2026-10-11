"""Constrained multi-objective optimization for adaptive cooling."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from scipy.optimize import differential_evolution

from .model import BOUNDS, simulate_process


@dataclass(frozen=True)
class OptimizationConfig:
    quality_weight: float = 0.72
    energy_weight: float = 0.28
    minimum_quality: float = 80.0
    maximum_final_temperature_c: float = 320.0
    seed: int = 42


def _normalized_energy(energy_kwh: float) -> float:
    return float(np.clip(energy_kwh / 1.6, 0.0, 2.0))


def optimize_cooling(
    initial_temperature_c: float,
    ambient_temperature_c: float,
    config: OptimizationConfig = OptimizationConfig(),
) -> dict[str, float | bool | str]:
    """Optimize flow, fan power, and duration for fixed measured temperatures."""
    if not (BOUNDS.initial_temperature_c[0] <= initial_temperature_c <= BOUNDS.initial_temperature_c[1]):
        raise ValueError("initial_temperature_c is outside the modeled range.")
    if not (BOUNDS.ambient_temperature_c[0] <= ambient_temperature_c <= BOUNDS.ambient_temperature_c[1]):
        raise ValueError("ambient_temperature_c is outside the modeled range.")

    bounds = [
        BOUNDS.coolant_flow_l_min,
        BOUNDS.fan_power_kw,
        BOUNDS.cooling_time_min,
    ]

    def objective(x: np.ndarray) -> float:
        flow, fan, time_min = x
        metrics = simulate_process(
            initial_temperature_c, ambient_temperature_c, flow, fan, time_min
        )
        quality_loss = (100.0 - metrics["quality_score"]) / 100.0
        energy_loss = _normalized_energy(metrics["energy_consumption_kwh"])

        quality_constraint = max(config.minimum_quality - metrics["quality_score"], 0.0)
        final_temp_constraint = max(
            metrics["final_temperature_c"] - config.maximum_final_temperature_c, 0.0
        )

        penalty = 0.03 * quality_constraint ** 2 + 0.002 * final_temp_constraint ** 2
        return (
            config.quality_weight * quality_loss
            + config.energy_weight * energy_loss
            + penalty
        )

    result = differential_evolution(
        objective,
        bounds=bounds,
        seed=config.seed,
        polish=True,
        tol=1e-8,
        atol=1e-10,
        maxiter=400,
        popsize=18,
        updating="immediate",
        workers=1,
    )

    flow, fan, time_min = result.x
    metrics = simulate_process(
        initial_temperature_c, ambient_temperature_c, flow, fan, time_min
    )

    feasible = (
        metrics["quality_score"] >= config.minimum_quality
        and metrics["final_temperature_c"] <= config.maximum_final_temperature_c
    )

    return {
        **metrics,
        "objective_value": float(result.fun),
        "optimization_success": bool(result.success),
        "feasible": bool(feasible),
        "optimizer_message": str(result.message),
    }


def baseline_process(
    initial_temperature_c: float,
    ambient_temperature_c: float,
) -> dict[str, float]:
    """Return a fixed-rule baseline for comparison."""
    return simulate_process(
        initial_temperature_c=initial_temperature_c,
        ambient_temperature_c=ambient_temperature_c,
        coolant_flow_l_min=12.0,
        fan_power_kw=2.2,
        cooling_time_min=18.0,
    )
