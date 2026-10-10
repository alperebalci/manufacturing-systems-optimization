# Two-scale benchmark protocol

The fixture system separates **correctness evidence** from **scalability evidence**.

## Validation fixtures

Validation fixtures are deliberately small. Their purpose is to support:

- exact solution where practical;
- exhaustive enumeration or independent oracle checks;
- reconstruction of feasibility outside the solver;
- deterministic regression tests;
- sensitivity tests where a known small model is easier to interpret.

A validation result should report objective/KPIs, feasibility audit and solver status. For cases with an independent oracle, the optimized objective should also match that oracle within tolerance.

## Industrial fixtures

Industrial fixtures are deliberately too large for the naive exact methods used by some validation cases. Their purpose is to benchmark:

- model-build time;
- solve or policy-computation time;
- incumbent objective / optimality gap when available;
- memory-relevant dimensions such as binary-variable count;
- fallback rate for rolling-horizon methods;
- simulation replication uncertainty;
- solution feasibility and KPI stability under scale.

The intended industrial algorithm can differ from the small-instance oracle. Case 03 moves from enumeration to assignment MILP + dispatch; Case 07 from permutation enumeration to CP-SAT/LNS; Case 10 from complete pattern enumeration to column generation or a restricted pattern set.

## Reproducibility

Each fixture records:

- fixed seed;
- schema version;
- explicit units;
- dimensions;
- intended solver mode;
- SHA-256 fingerprint over the complete payload.

A changed fingerprint means the benchmark data changed and performance numbers should not be compared as if they came from the same fixture.

## Machine-readable demo evidence

The `manufacturing_optimization.experiment_evidence` command executes the existing
ten **built-in demonstration** benchmark functions and writes an auditable JSON report:

- `evidence_tier: small_demo_validation` and `industrial_scalability_evaluated: false`;
- per-case objective/KPI output, wall-clock time and explicit audit status;
- Python, NumPy, SciPy, pandas, platform and GitHub commit (when available);
- a content-derived `result_fingerprint` that excludes unstable timings and timestamps;
- an overall `partial_not_reported` audit status if any case does not expose an audit.

This command does **not** run the large industrial fixtures and does not claim
paired-method comparison or statistical significance. Do not treat its runtime
numbers as a fair multi-method benchmark. In particular, it does not equate
built-in demo inputs with the fixture payloads in `fixtures/manifest.json`.

The workflow artifact is useful for **regression and provenance**, not publication
of industrial performance claims. To make a strong performance claim, record
the complete instance fingerprint, hardware, solver settings, stopping criteria,
repetitions, seeds, calibrated uncertainty, confidence intervals, and independent
feasibility/optimality audit as described above.

## CI policy

CI constructs and validates all 20 fixtures but does not solve every industrial fixture to optimality. This avoids turning correctness CI into an uncontrolled performance test. Full industrial campaigns should run separately and retain runtime, solver version, machine specification and result artifacts.
