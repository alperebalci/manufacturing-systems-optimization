# Modeling notes

This repository is a collection of compact, inspectable manufacturing decision models. The problems are deliberately small enough to run in CI, but each case preserves the structure that makes the corresponding industrial problem nontrivial.

## 01 — Integrated production and maintenance

A single production resource processes jobs with family-dependent setup times. One preventive-maintenance activity must be inserted into the production sequence. Processing jobs before maintenance accumulates degradation exposure; maintenance resets the exposure. The exact solver enumerates all job permutations and maintenance insertion positions, which is globally exact for the bundled small instances.

## 02 — Milk-run / supermarket replenishment

Each production zone selects one replenishment interval from a discrete candidate set. The interval determines route frequency, average line-side inventory and expected shortage exposure. A MILP enforces one interval per zone and total tugger-hours capacity.

## 03 — AGV/AMR assignment

Transport tasks are assigned to heterogeneous robots. Eligibility, payload, battery and workload limits are enforced. The model penalizes estimated lateness and leaves an explicit emergency-manual-move option rather than silently making infeasible task sets disappear.

## 04 — Ergonomic worker rotation

Workers rotate across stations over multiple periods. Skill eligibility, one-worker-per-station, one-station-per-worker, cumulative ergonomic exposure and station changes are modeled. Exposure above a target is allowed through an explicit penalized excess variable.

## 05 — Quality inspection MDP

A small Markov Decision Process represents latent process-quality condition. Inspection intensity changes immediate appraisal cost and the probability/cost of escaping defects, while actions also influence the next quality state. Value iteration produces a stationary policy for the declared model.

## 06 — CNC parameters

Cutting speed, feed and depth of cut jointly affect material removal rate, tool life, surface roughness, power and total machining economics. A constrained nonlinear cost is solved with differential evolution. Equations are stylized engineering relations, not calibrated machine-tool physics.

## 07 — Tooling-constrained scheduling

Jobs require dies/tools and have machine eligibility. The exact small-instance solver enumerates assignments and machine sequences, accounting for tool changeovers. This is intended as a correctness reference for small cases rather than a scalable industrial scheduler.

## 08 — CONWIP / Kanban

A discrete-event serial line is simulated under alternative WIP caps. Candidate policies are compared using common random numbers. The objective combines throughput contribution, WIP holding cost and cycle-time cost.

## 09 — Energy-aware scheduling

Production quantities, inventory and machine on/off decisions are optimized over time-of-use prices. A peak-demand variable captures a demand charge. The model demonstrates the interaction between production smoothing, inventory, setup and electricity tariffs.

## 10 — Cutting stock with remnant reuse

Feasible cutting patterns are generated for purchased bars and a small set of existing remnants. An integer program selects patterns that meet piece demand while minimizing purchased-stock cost and waste. Remnants are modeled as individually limited resources.
