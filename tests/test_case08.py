from manufacturing_process_optimization.case08_conwip import (
    generate_service_scenarios,
    optimize_conwip,
)


def test_conwip_policy_search_returns_declared_candidate():
    scenarios = generate_service_scenarios(replications=3, jobs=500, seed=3)
    candidates = (2, 3, 4, 5, 6)
    result = optimize_conwip(candidates, scenarios)
    assert result.best.wip_limit in candidates
    assert len(result.candidates) == len(candidates)
    assert result.best.throughput_per_hour > 0
    assert result.best.mean_cycle_time > 0
