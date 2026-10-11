# Case 05 — Quality inspection and rework policy

Decision: choose light, standard or intensive inspection for each process condition state.

States are stable, drifting, and out_of_control. Action costs include inspection effort, expected defect escape and rework. Action-dependent transition matrices capture how stronger control can return the process toward stable operation.

The discounted MDP is solved by value iteration, then the selected policy is evaluated exactly from the fixed-policy linear system. Every deterministic stationary policy is also enumerated as an independent oracle.

Baseline: standard inspection in every state.

KPIs: discounted lifecycle quality cost and selected state-dependent policy.
