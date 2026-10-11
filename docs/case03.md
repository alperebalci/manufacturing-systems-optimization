# Case 03 — AGV/AMR production feeding

Decision: assign transport tasks to eligible vehicles while maintaining battery reserve.

Tasks carry service time, energy use, deadline and priority. Each vehicle has speed factor, usable battery and eligibility restrictions. For the small benchmark, all feasible allocations are enumerated exactly; each vehicle then executes its assigned tasks by due date.

Baseline: EDD task processing with assignment to the least-loaded feasible vehicle.

Audit: task eligibility and end-of-horizon battery reserve.

KPIs: weighted tardiness, makespan/workload balance and energy slack.
