from manufacturing_process_optimization.case10_cutting_stock import (
    demo_instance,
    optimize_cutting_stock,
)


def test_cutting_stock_meets_demand_and_limits_remnants():
    lengths, demand = demo_instance()
    result = optimize_cutting_stock(lengths, demand)
    assert all(p >= d for p, d in zip(result.produced, demand))
    assert tuple(p - d for p, d in zip(result.produced, demand)) == result.excess
    assert result.remnants_used <= 3
    assert result.new_bars >= 0
