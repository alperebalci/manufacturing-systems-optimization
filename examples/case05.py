from manufacturing_process_optimization.case05_quality_mdp import build_default_mdp, value_iteration

result = value_iteration(build_default_mdp())
print("policy:", result.policy)
print("values:", {k: round(v, 2) for k, v in result.values.items()})
print("Bellman residual:", result.bellman_residual)
