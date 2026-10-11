# Industrialization standard

The original repository demonstrated ten optimization ideas. Version 0.2 applies a common decision-engineering standard so the cases resemble manufacturing analytics work rather than isolated algorithm examples.

## Model layer

Every case now represents at least one constraint that normally disappears from textbook formulations: preventive-maintenance downtime, emergency material supply, battery reserve, ergonomic exposure, defect escape, process-quality limits, mold compatibility, equipment breakdowns, maintenance blackout, or kerf/remnant availability.

## Baseline layer

An optimization result has little business meaning without an incumbent comparison. Each case therefore exposes a transparent baseline such as direct-cost assignment, greedy replenishment, earliest-due assignment, risk-balancing rotation, fixed inspection intensity, nominal machining settings, EDD press scheduling, high-WIP CONWIP, EDD production scheduling, or first-fit cutting.

## Validation layer

Solver success is not treated as proof of an operationally valid plan. Case-specific audits reconstruct capacity, inventory balance, task eligibility, battery reserve, station coverage, process constraints, job uniqueness, blackout feasibility and demand coverage independently from the solver status.

## Experiment layer

manufacturing_optimization.benchmarks.run_all() returns one DataFrame containing the industrial benchmark output from every case. Selected cases also expose explicit sensitivity functions for failure-risk economics, vehicle capacity and material hardness. CONWIP uses multiple seeded simulation replications and reports a standard error for throughput.

## Data policy

All bundled values are synthetic engineering fixtures. The models deliberately separate operational semantics from any claim about a named factory. See data_contracts.md for the fields that would be mapped from ERP/MES/WMS/CMMS/QMS/SCADA sources in a deployment.
