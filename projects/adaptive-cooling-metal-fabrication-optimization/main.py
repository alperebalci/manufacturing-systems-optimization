"""Run a reproducible adaptive-cooling simulation and optimization example."""

from pathlib import Path

from adaptive_cooling.model import generate_synthetic_data
from adaptive_cooling.optimize import OptimizationConfig, baseline_process, optimize_cooling


def pct_change(new: float, old: float) -> float:
    if old == 0:
        return float("nan")
    return 100.0 * (new - old) / old


def main() -> None:
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)

    dataset = generate_synthetic_data(n_samples=5000, seed=42)
    dataset_path = output_dir / "synthetic_cooling_data.csv"
    dataset.to_csv(dataset_path, index=False)

    initial_temperature_c = 820.0
    ambient_temperature_c = 25.0

    baseline = baseline_process(initial_temperature_c, ambient_temperature_c)
    optimized = optimize_cooling(
        initial_temperature_c,
        ambient_temperature_c,
        OptimizationConfig(
            quality_weight=0.72,
            energy_weight=0.28,
            minimum_quality=80.0,
            maximum_final_temperature_c=320.0,
            seed=42,
        ),
    )

    print("Adaptive Cooling Optimization")
    print("=" * 30)
    print(f"Synthetic dataset: {dataset_path} ({len(dataset):,} rows)")
    print()
    print("Baseline")
    print(f"  Quality score: {baseline['quality_score']:.2f}/100")
    print(f"  Energy: {baseline['energy_consumption_kwh']:.4f} kWh")
    print(f"  Final temperature: {baseline['final_temperature_c']:.2f} °C")
    print()
    print("Optimized")
    print(f"  Coolant flow: {optimized['coolant_flow_l_min']:.3f} L/min")
    print(f"  Fan power: {optimized['fan_power_kw']:.3f} kW")
    print(f"  Cooling time: {optimized['cooling_time_min']:.3f} min")
    print(f"  Cooling rate: {optimized['cooling_rate_c_min']:.3f} °C/min")
    print(f"  Final temperature: {optimized['final_temperature_c']:.2f} °C")
    print(f"  Quality score: {optimized['quality_score']:.2f}/100")
    print(f"  Energy: {optimized['energy_consumption_kwh']:.4f} kWh")
    print(f"  Defect probability: {100 * optimized['defect_probability']:.2f}%")
    print(f"  Feasible: {optimized['feasible']}")
    print()
    print("Change vs baseline")
    print(
        f"  Quality: {pct_change(optimized['quality_score'], baseline['quality_score']):+.2f}%"
    )
    print(
        f"  Energy: {pct_change(optimized['energy_consumption_kwh'], baseline['energy_consumption_kwh']):+.2f}%"
    )


if __name__ == "__main__":
    main()
