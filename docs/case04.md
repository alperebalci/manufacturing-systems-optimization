# Case 04 — Ergonomic worker rotation

Decision: assign qualified workers to stations over multiple periods.

The MILP covers every station each period, restricts each worker to at most one station, enforces the skill matrix, weights station ergonomic risk by within-shift fatigue, caps cumulative exposure and prevents consecutive assignments to the highest-risk station.

Baseline: greedy risk-balancing rotation.

Audit: station coverage, one-station-per-worker, qualification, exposure caps and high-risk rotation rule.

KPIs: maximum worker exposure and exposure dispersion.
