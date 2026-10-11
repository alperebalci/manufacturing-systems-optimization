from manufacturing_process_optimization.case05_quality_mdp import (
    ACTIONS,
    STATES,
    build_default_mdp,
    evaluate_stationary_policy,
    value_iteration,
)


def test_mdp_policy_and_exact_policy_value_agree():
    mdp = build_default_mdp()
    result = value_iteration(mdp)
    exact = evaluate_stationary_policy(mdp, result.policy)
    assert set(result.policy) == set(STATES)
    assert all(a in ACTIONS for a in result.policy.values())
    assert result.bellman_residual < 1e-7
    assert max(abs(result.values[s] - exact[s]) for s in STATES) < 1e-5
