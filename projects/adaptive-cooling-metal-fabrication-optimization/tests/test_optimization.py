from adaptive_cooling.optimize import OptimizationConfig, baseline_process, optimize_cooling


def test_optimizer_returns_feasible_solution():
    result = optimize_cooling(
        820.0,
        25.0,
        OptimizationConfig(
            minimum_quality=80.0,
            maximum_final_temperature_c=320.0,
            seed=11,
        ),
    )
    assert result["optimization_success"]
    assert result["feasible"]
    assert result["quality_score"] >= 80.0
    assert result["final_temperature_c"] <= 320.0


def test_optimizer_improves_energy_vs_baseline_while_meeting_quality():
    baseline = baseline_process(820.0, 25.0)
    result = optimize_cooling(820.0, 25.0, OptimizationConfig(seed=42))
    assert result["quality_score"] >= 80.0
    assert result["energy_consumption_kwh"] < baseline["energy_consumption_kwh"]
