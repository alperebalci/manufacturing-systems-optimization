import numpy as np

from adaptive_cooling.model import (
    defect_probability,
    energy_consumption_kwh,
    generate_synthetic_data,
    simulate_process,
)


def test_synthetic_data_is_reproducible():
    a = generate_synthetic_data(n_samples=25, seed=123)
    b = generate_synthetic_data(n_samples=25, seed=123)
    assert a.equals(b)


def test_synthetic_data_ranges():
    df = generate_synthetic_data(n_samples=200, seed=7)
    assert len(df) == 200
    assert df["quality_score"].between(0, 100).all()
    assert (df["energy_consumption_kwh"] >= 0).all()
    assert df["defect_probability"].between(0, 1).all()


def test_energy_increases_with_fan_power():
    low = energy_consumption_kwh(8.0, 0.5, 10.0)
    high = energy_consumption_kwh(8.0, 2.5, 10.0)
    assert high > low


def test_defect_probability_decreases_with_quality():
    assert defect_probability(90.0) < defect_probability(60.0)


def test_simulation_outputs_are_finite():
    result = simulate_process(820.0, 25.0, 10.0, 1.5, 15.0)
    for value in result.values():
        assert np.isfinite(value)
