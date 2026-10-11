# Case 01 — Integrated production and preventive maintenance

Decision: assign each job to one heterogeneous machine, choose machine-level PM, and buy limited overtime.

The MILP minimizes variable production cost + expected failure-risk exposure + PM cost + overtime. Binary interaction variables linearize assignment AND PM, allowing PM to reduce only the risk of work actually assigned to that machine. Capacity includes PM downtime.

Baseline: direct-cost assignment with no PM, repaired only when overtime feasibility is violated.

Audit: every job assigned once; PM binary; load + PM downtime <= regular capacity + overtime; overtime cap.

KPIs: total cost, PM count, overtime hours. sensitivity() scales failure-risk economics and demonstrates when maintenance becomes economically justified.
