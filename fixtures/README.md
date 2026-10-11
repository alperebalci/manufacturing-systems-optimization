# Dual-scale fixture library

Every manufacturing case has two deterministic synthetic fixtures.

- **validation**: intentionally small enough for exact solution, exhaustive checking, or detailed independent feasibility auditing.
- **industrial**: sized to exercise realistic data volume, sparse model construction, rolling-horizon logic, simulation replication management, or scalable heuristics/decomposition.

The large fixtures are not claims about a named plant. They are reproducible benchmark workloads with explicit units, seeds, dimensions, intended solver mode and SHA-256 payload fingerprints.

## Materialize all 20 fixtures

```bash
python -m manufacturing_optimization.fixture_library --materialize generated_fixtures
```

This creates:

```text
generated_fixtures/
  manifest.json
  case01/
    validation.json
    industrial.json
  ...
  case10/
    validation.json
    industrial.json
```

The JSON files are generated rather than committed because several industrial fixtures contain large matrices. The generator seed and payload fingerprint are committed in `fixtures/manifest.json`.

## Benchmark scale

| Case | Validation fixture | Industrial fixture | Intended industrial solver mode |
|---|---|---|---|
| 01 | 8 jobs × 2 machines | 500 jobs × 20 machines | sparse MILP |
| 02 | 3 stations × 6 periods | 40 stations × 96 periods | sparse MILP |
| 03 | 8 tasks × 3 AGVs | 250 tasks × 20 AGVs | assignment MILP + dispatch |
| 04 | 4 workers × 3 stations × 5 periods | 120 × 36 × 8 | sparse MILP |
| 05 | 3 states × 3 actions | 12 states × 4 actions | value/policy iteration |
| 06 | 1 machining operation | 1,000 operations | batched NLP / surrogate |
| 07 | 6 jobs × 2 presses | 180 jobs × 12 presses | CP-SAT / LNS |
| 08 | 3 stations, 20 reps | 12 stations, 50 reps | CRN simulation optimization |
| 09 | 5 jobs × 1 machine × 16 periods | 120 jobs × 4 machines × 168 periods | rolling-horizon MILP / CP-SAT |
| 10 | 3 item types × 3 stock types | 30 item types × 6 stock types | column generation / restricted-pattern MILP |
