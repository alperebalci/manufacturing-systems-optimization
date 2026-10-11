"""Core synthetic process model for adaptive cooling in metal fabrication."""

from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ProcessBounds:
    initial_temperature_c: tuple[float, float] = (650.0, 950.0)
    ambient_temperature_c: tuple[float, float] = (15.0, 40.0)
    coolant_flow_l_min: tuple[float, float] = (2.0, 18.0)
    fan_power_kw: tuple[float, float] = (0.2, 3.0)
    cooling_time_min: tuple[float, float] = (4.0, 25.0)


BOUNDS = ProcessBounds()


def cooling_rate_c_min(
    initial_temperature_c: float,
    ambient_temperature_c: float,
    coolant_flow_l_min: float,
    fan_power_kw: float,
) -> float:
    """Estimate average cooling rate from a compact surrogate heat-transfer model."""
    delta_t = max(initial_temperature_c - ambient_temperature_c, 1.0)
    convective_term = 0.0028 * delta_t
    coolant_term = 0.42 * math.sqrt(max(coolant_flow_l_min, 0.0))
    fan_term = 0.70 * math.sqrt(max(fan_power_kw, 0.0))
    return convective_term + coolant_term + fan_term


def final_temperature_c(
    initial_temperature_c: float,
    ambient_temperature_c: float,
    coolant_flow_l_min: float,
    fan_power_kw: float,
    cooling_time_min: float,
) -> float:
    """Estimate final part temperature using exponential cooling toward ambient."""
    delta_t = max(initial_temperature_c - ambient_temperature_c, 0.0)
    heat_transfer_factor = (
        0.018
        + 0.0055 * math.sqrt(max(coolant_flow_l_min, 0.0))
        + 0.0080 * math.sqrt(max(fan_power_kw, 0.0))
    )
    return ambient_temperature_c + delta_t * math.exp(-heat_transfer_factor * cooling_time_min)


def energy_consumption_kwh(
    coolant_flow_l_min: float,
    fan_power_kw: float,
    cooling_time_min: float,
) -> float:
    """Estimate cooling-system energy use.

    Pump power increases nonlinearly with flow, while fan energy is proportional
    to fan electrical power and operating time.
    """
    pump_power_kw = 0.08 + 0.0045 * coolant_flow_l_min ** 1.8
    total_power_kw = pump_power_kw + fan_power_kw
    return total_power_kw * cooling_time_min / 60.0


def quality_score(
    initial_temperature_c: float,
    ambient_temperature_c: float,
    coolant_flow_l_min: float,
    fan_power_kw: float,
    cooling_time_min: float,
) -> float:
    """Return a synthetic quality score in [0, 100].

    Quality degrades for excessive thermal gradients, cooling that is too fast
    or too slow, and final temperatures that remain too high.
    """
    rate = cooling_rate_c_min(
        initial_temperature_c, ambient_temperature_c, coolant_flow_l_min, fan_power_kw
    )
    final_temp = final_temperature_c(
        initial_temperature_c,
        ambient_temperature_c,
        coolant_flow_l_min,
        fan_power_kw,
        cooling_time_min,
    )

    rate_penalty = 1.25 * (rate - 6.0) ** 2
    final_temp_penalty = 0.0010 * max(final_temp - 300.0, 0.0) ** 2
    shock_penalty = 0.0010 * max(initial_temperature_c - final_temp - 650.0, 0.0) ** 2
    undercool_penalty = 0.010 * max(180.0 - (initial_temperature_c - final_temp), 0.0) ** 2

    raw = 100.0 - rate_penalty - final_temp_penalty - shock_penalty - undercool_penalty
    return float(np.clip(raw, 0.0, 100.0))


def defect_probability(quality: float) -> float:
    """Map quality score to a smooth synthetic defect probability."""
    return float(1.0 / (1.0 + math.exp((quality - 72.0) / 6.5)))


def simulate_process(
    initial_temperature_c: float,
    ambient_temperature_c: float,
    coolant_flow_l_min: float,
    fan_power_kw: float,
    cooling_time_min: float,
) -> dict[str, float]:
    """Evaluate one cooling configuration."""
    rate = cooling_rate_c_min(
        initial_temperature_c, ambient_temperature_c, coolant_flow_l_min, fan_power_kw
    )
    final_temp = final_temperature_c(
        initial_temperature_c,
        ambient_temperature_c,
        coolant_flow_l_min,
        fan_power_kw,
        cooling_time_min,
    )
    energy = energy_consumption_kwh(coolant_flow_l_min, fan_power_kw, cooling_time_min)
    quality = quality_score(
        initial_temperature_c,
        ambient_temperature_c,
        coolant_flow_l_min,
        fan_power_kw,
        cooling_time_min,
    )

    return {
        "initial_temperature_c": float(initial_temperature_c),
        "ambient_temperature_c": float(ambient_temperature_c),
        "coolant_flow_l_min": float(coolant_flow_l_min),
        "fan_power_kw": float(fan_power_kw),
        "cooling_time_min": float(cooling_time_min),
        "cooling_rate_c_min": float(rate),
        "final_temperature_c": float(final_temp),
        "energy_consumption_kwh": float(energy),
        "quality_score": float(quality),
        "defect_probability": defect_probability(quality),
    }


def generate_synthetic_data(
    n_samples: int = 5000,
    seed: int = 42,
    noise_std_quality: float = 1.5,
    noise_std_energy: float = 0.015,
) -> pd.DataFrame:
    """Generate reproducible synthetic process observations."""
    if n_samples <= 0:
        raise ValueError("n_samples must be positive.")

    rng = np.random.default_rng(seed)
    b = BOUNDS

    rows = []
    for _ in range(n_samples):
        initial_temp = rng.uniform(*b.initial_temperature_c)
        ambient_temp = rng.uniform(*b.ambient_temperature_c)
        flow = rng.uniform(*b.coolant_flow_l_min)
        fan = rng.uniform(*b.fan_power_kw)
        time_min = rng.uniform(*b.cooling_time_min)

        row = simulate_process(initial_temp, ambient_temp, flow, fan, time_min)
        row["quality_score"] = float(
            np.clip(row["quality_score"] + rng.normal(0.0, noise_std_quality), 0.0, 100.0)
        )
        row["energy_consumption_kwh"] = float(
            max(row["energy_consumption_kwh"] + rng.normal(0.0, noise_std_energy), 0.0)
        )
        row["defect_probability"] = defect_probability(row["quality_score"])
        rows.append(row)

    return pd.DataFrame(rows)
