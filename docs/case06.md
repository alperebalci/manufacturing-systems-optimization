# Case 06 — CNC process parameter optimization

Decision: cutting speed, feed and depth of cut.

The nonlinear model links parameters to material-removal rate, cycle time, Taylor-style tool life, roughness, spindle power and energy. The economic objective combines machine time, tool consumption and electricity while enforcing hard limits for surface finish, minimum tool life and spindle power.

Baseline: a conservative nominal engineering setting.

Audit: surface finish, tool-life and power constraints are re-evaluated from the final parameters.

KPIs: cost per part proxy, cycle time, tool life, energy and power. sensitivity() varies material hardness.
