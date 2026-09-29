# Integrated Production–Maintenance–Capacity Planning

A multi-period MILP that jointly chooses production quantities and preventive-maintenance timing.

The model combines:

- finite production capacity,
- maintenance downtime,
- inventory/backlog balance,
- maintenance cost,
- a usage-since-maintenance age/risk state.

Preventive maintenance consumes capacity and money, but resets accumulated equipment age before current-period production. The objective therefore exposes the real trade-off between short-term throughput and future reliability exposure.

This is intentionally a planning model rather than a detailed reliability simulator. Natural extensions include multiple machines, Weibull hazard calibration, condition-monitoring signals, spare-parts limits, maintenance crews, stochastic breakdown recourse, and joint scheduling.
