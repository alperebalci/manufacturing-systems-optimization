# Case 08 — CONWIP release control

Decision: select the plant-wide WIP cap.

A three-station event-driven line uses stochastic lognormal processing times and probabilistic failures with exponential repair. A warm-up period removes initial empty-system bias. Candidate WIP caps are compared using common seeded replications.

Baseline: a high-WIP cap of 10.

KPIs: throughput, cycle time, average WIP, downtime fraction and throughput standard error. The score penalizes insufficient throughput while charging cycle time and WIP.
