# Manufacturing Systems Optimization

<!-- portfolio-umbrella:start -->
## Portfolio role

This repository is the primary umbrella repository for this Jors Academy research area. Related projects have been consolidated under `projects/` so the methods, implementations, experiments, and case studies can be maintained and explored from one place.

### Native flagship

The repository root contains the actively maintained **manufacturing decision-systems benchmark suite** described below. The entries under `projects/` are consolidated companion projects.

### Included projects

- [`adaptive-cooling-metal-fabrication-optimization`](projects/adaptive-cooling-metal-fabrication-optimization/)
- [`manufacturing-lead-time-batch-inference-lightgbm-github-actions`](projects/manufacturing-lead-time-batch-inference-lightgbm-github-actions/)

Each consolidated project keeps its own files and a `SOURCE_REPOSITORY.md` provenance record. The snapshot preserves the source repository's default-branch files at consolidation time; repository-level history and metadata remain separate from the snapshot.
<!-- portfolio-umbrella:end -->

Industrial Engineering / Operations Research monorepo with 10 manufacturing decision systems implemented in Python.

Version **0.3** adds a formal **dual-scale fixture standard** to every case:

- a **small validation fixture** for exactness, exhaustive checking, independent feasibility audits and regression testing;
- a **large industrial benchmark fixture** for scale, sparse model construction, rolling-horizon methods, simulation campaigns, decomposition or scalable heuristics.

## Case portfolio and benchmark scale

| Case | Decision problem | Validation fixture | Industrial fixture |
|---|---|---:|---:|
| 01 | Production assignment + preventive maintenance | 8 jobs × 2 machines | 500 jobs × 20 machines |
| 02 | Milk-run / line-side replenishment | 3 stations × 6 periods | 40 stations × 96 periods |
| 03 | AGV/AMR task allocation | 8 tasks × 3 AGVs | 250 tasks × 20 AGVs |
| 04 | Ergonomic worker rotation | 4 workers × 3 stations × 5 periods | 120 × 36 × 8 |
| 05 | Quality inspection policy | 3 states × 3 actions | 12 states × 4 actions |
| 06 | CNC process parameters | 1 machining operation | 1,000 operations |
| 07 | Mold/tooling-aware press scheduling | 6 jobs × 2 presses | 180 jobs × 12 presses |
| 08 | CONWIP simulation optimization | 3 stations, 20 reps | 12 stations, 50 reps |
| 09 | Energy-aware scheduling | 5 jobs × 1 machine × 16 periods | 120 jobs × 4 machines × 168 periods |
| 10 | Cutting stock + remnants | 3 item × 3 stock types | 30 item × 6 stock types |

The small and large fixtures intentionally do **not** imply the same algorithm. Small fixtures can use exact enumeration where that improves verification. Large fixtures declare an industrial solver mode such as sparse MILP, rolling-horizon MILP/CP-SAT, LNS, simulation optimization, batched NLP, or column generation.

## Cross-cutting quality engineering lab\n\nA new statistical quality-engineering module complements the 10 optimization cases without pretending that SPC or DOE is itself an optimization problem.\n\n- `quality_engineering.py` implements two-level full-factorial DOE, factorial effects, best observed setting selection, Individuals-chart SPC, and Cp/Cpk capability analysis.\n- `docs/quality_engineering_spc_doe.md` connects the methods into a measurement -> stability -> DOE -> optimization -> monitoring workflow.\n- `tests/test_quality_engineering.py` verifies effect recovery, setting selection, out-of-control detection, and capability calculations.\n\nThis fills the classical SPC/DOE component of a modern IE curriculum while keeping it computational and testable.\n\n## Engineering standard

Every case now has six evidence layers:

1. explicit manufacturing decision model;
2. operational baseline;
3. independent feasibility audit;
4. KPI comparison;
5. sensitivity/stress logic where relevant;
6. **dual-scale reproducible fixtures with fixed seed and payload fingerprint**.

The benchmark data are synthetic engineering fixtures, not measurements from a named factory.

## Fixture library

List all committed fixture contracts:

```bash
python -m manufacturing_optimization.fixture_library
```

Materialize all 20 fixtures as JSON:

```bash
python -m manufacturing_optimization.fixture_library --materialize generated_fixtures
```

Each materialized fixture contains:

- case id and scale;
- seed and schema version;
- dimensions;
- physical units;
- intended solver mode;
- SHA-256 fingerprint;
- complete payload.

The committed reference fingerprints live in `fixtures/manifest.json`.

## Install and validate

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
pytest
```

## Run the small-case benchmark panel

```bash
python -m manufacturing_optimization.benchmarks
```

For an auditable **small-demo** JSON artifact with per-case wall time, library versions,
commit SHA (in GitHub Actions), numeric outputs, audit reporting status, and a stable
result fingerprint, run:

```bash
python -m manufacturing_optimization.experiment_evidence \
  --output artifacts/manufacturing-demo-evidence.json
```

This is **not** the large-instance industrial benchmark. The case-specific functions
use their existing built-in demo inputs, and the output does not claim that those
inputs are identical to `fixtures/manifest.json`. Case 08 currently reports
simulation metrics but does not expose an independent feasibility audit; the
export records that audit as `not_reported` rather than a pass.
CI stores the JSON as a downloadable workflow artifact. See
[the two-scale benchmark protocol](docs/benchmark_protocol.md).

## Repository structure

```text
src/manufacturing_optimization/
  validation.py
  benchmarks.py
  fixture_library.py
  case01_production_maintenance.py
  ...
  case10_cutting_stock.py

fixtures/
  README.md
  manifest.json

docs/
  benchmark_protocol.md
  industrialization.md
  data_contracts.md
  case01.md ... case10.md

tests/
  test_cases.py
  test_industrial_cases.py
  test_fixture_library.py
```

## Benchmark interpretation

Validation CI and industrial performance benchmarking are deliberately separated. CI constructs and validates all 20 fixtures, but it does not attempt to solve every large industrial instance to optimality. Industrial campaigns should additionally record solver/runtime version, hardware, wall-clock time, incumbent objective, optimality gap or fallback rate, memory-relevant dimensions and result artifacts.

This separation prevents a small exact demonstrator from being presented as evidence of industrial scalability while preserving a rigorous correctness oracle for every case.
