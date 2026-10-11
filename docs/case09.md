# Case 09 — Energy-aware production scheduling

Decision: start time of each non-preemptive job on a single machine.

The time-indexed MILP includes time-of-use electricity price, job power draw, weighted tardiness, peak-demand charge and a maintenance blackout period that no job may overlap.

Baseline: earliest-due-date scheduling shifted around the same blackout.

Audit: reconstructed machine occupancy checks overlap and blackout feasibility.

KPIs: total operating objective, weighted tardiness and peak kW.
