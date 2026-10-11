from manufacturing_process_optimization.case06_cnc_parameters import (
    CNCConfig,
    baseline_cnc,
    optimize_cnc,
)


def test_cnc_solution_is_feasible_and_improves_default_baseline():
    cfg = CNCConfig()
    result = optimize_cnc(cfg, seed=7)
    baseline = baseline_cnc(cfg)
    assert result.power_kw <= cfg.max_power_kw + 1e-4
    assert result.roughness_um <= cfg.max_roughness_um + 1e-4
    assert result.tool_life_minutes >= 2.0 - 1e-4
    assert result.objective <= baseline.objective + 1e-6
