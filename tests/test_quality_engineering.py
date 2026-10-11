import numpy as np

from manufacturing_optimization.quality_engineering import (
    factorial_effects,
    full_factorial,
    individuals_control_chart,
    process_capability,
    recommend_factorial_setting,
)


def test_full_factorial_and_effect_recovery():
    design = full_factorial(
        {
            "speed": (100.0, 200.0),
            "feed": (0.10, 0.20),
            "coolant": (1.0, 2.0),
        }
    )

    assert len(design) == 8

    a = design["speed_code"].to_numpy()
    b = design["feed_code"].to_numpy()
    y = 10.0 - 2.0 * a + 3.0 * b + 1.5 * a * b

    effects = factorial_effects(
        design,
        y,
        factors=("speed", "feed", "coolant"),
    )

    assert np.isclose(effects["speed"], -4.0)
    assert np.isclose(effects["feed"], 6.0)
    assert np.isclose(effects["speed:feed"], 3.0)
    assert np.isclose(effects["coolant"], 0.0)


def test_recommend_setting_uses_mean_response():
    design = full_factorial(
        {"temperature": (180.0, 220.0), "pressure": (4.0, 8.0)}
    )
    repeated = design.loc[design.index.repeat(2)].reset_index(drop=True)

    t = repeated["temperature_code"].to_numpy()
    p = repeated["pressure_code"].to_numpy()
    response = 50.0 + 4.0 * t - 3.0 * p

    best = recommend_factorial_setting(
        repeated,
        response,
        factors=("temperature", "pressure"),
        minimize=True,
    )

    assert best["temperature"] == 180.0
    assert best["pressure"] == 8.0


def test_individuals_chart_flags_large_shift():
    values = [10.00, 10.08, 9.96, 10.02, 10.06, 9.98, 10.04, 10.01, 11.00]
    chart = individuals_control_chart(values, baseline_count=8)

    assert 8 in chart["out_of_control_indices"]
    assert not np.any(chart["out_of_control"][:8])


def test_process_capability_is_finite_and_positive():
    values = [9.9, 10.0, 10.1, 10.05, 9.95, 10.02, 9.98]
    capability = process_capability(
        values,
        lower_spec=9.5,
        upper_spec=10.5,
    )

    assert capability["cp"] > 0
    assert capability["cpk"] > 0
    assert capability["cpk"] <= capability["cp"] + 1e-12
