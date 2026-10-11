from manufacturing_process_optimization.case02_milkrun import demo_instance, optimize_milkrun


def test_milkrun_selects_one_interval_per_zone():
    zones = demo_instance()
    result = optimize_milkrun(zones)
    assert set(result.selected_interval) == {z.name for z in zones}
    assert result.tugger_hours <= 3.2 + 1e-7
    assert result.objective > 0
