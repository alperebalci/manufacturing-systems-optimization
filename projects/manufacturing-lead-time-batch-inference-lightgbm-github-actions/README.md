# Manufacturing Lead-Time Batch Inference with LightGBM, MAPIE, and GitHub Actions

A small production-style machine-learning project that predicts manufacturing order lead time in batch mode and reports calibrated prediction intervals.

Unlike a notebook-only demo, the project separates data generation, model fitting, conformal calibration, holdout evaluation, inference, tests, and automation. The preprocessing + LightGBM estimator is wrapped by MAPIE's split-conformal regressor so batch outputs contain both a point estimate and a 95% marginal prediction interval.

## Architecture

```text
data/training.csv
        |
        v
      train.py
        |
        +--> 60% fit LightGBM pipeline
        |
        +--> 20% conformalize MAPIE
        |
        +--> 20% evaluate point error + interval coverage
        |
        v
models/lead_time_pipeline.joblib
        |
        +-----------------------+
                                |
data/incoming/orders_to_score.csv
                                |
                                v
                            score.py
                                |
                                v
data/predictions/latest_predictions.csv
```

GitHub Actions runs CI on pushes/PRs and can run the batch scoring workflow every Monday.

## Project structure

```text
.
├── .github/
│   └── workflows/
│       ├── batch-inference.yml
│       └── ci.yml
├── data/
│   ├── incoming/
│   └── predictions/
├── models/
├── src/
│   └── leadtime_ml/
│       ├── __init__.py
│       ├── features.py
│       └── modeling.py
├── tests/
│   ├── test_features.py
│   └── test_pipeline.py
├── generate_demo_data.py
├── score.py
├── train.py
└── pyproject.toml
```

## Local run

Python 3.13 is used in CI.

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"

python generate_demo_data.py
python train.py
python score.py

pytest -q
ruff check .
```

The prediction output is written to:

```text
data/predictions/latest_predictions.csv
```

Each scored row includes:

- `predicted_lead_time_hours`
- `prediction_lower_hours`
- `prediction_upper_hours`
- `prediction_interval_confidence`
- `scored_at_utc`

Training metrics are written to:

```text
models/metrics.json
```

In addition to MAE and MAPE, the metrics include nominal interval confidence, empirical holdout coverage, and mean prediction-interval width.

## Why this design?

- One serialized artifact contains preprocessing, LightGBM, and the fitted conformal calibrator.
- MAPIE adds distribution-free split-conformal prediction intervals without replacing the underlying LightGBM model.
- Training, conformalization, and final evaluation use disjoint rows; the test split is not reused for calibration.
- Batch inference validates the input schema before predicting.
- Unknown categorical values are handled safely.
- Predictions and uncertainty bounds are machine-readable CSV columns instead of unstructured log text.
- CI is read-only.
- Scheduled inference publishes outputs as a GitHub Actions artifact instead of committing generated files back into `main`.
- `workflow_dispatch` allows manual runs.
- `concurrency` prevents overlapping scheduled jobs.
- Tests cover schema validation, model serialization, conformal calibration, and interval inference.

## Interpreting the interval

The 95% number is a target marginal coverage level, not a claim that every individual order has a 95% probability of falling inside its interval. Split-conformal coverage relies on the conformalization rows being representative/exchangeable with future scoring rows.

For production use, monitor empirical coverage and interval width over time and by operationally meaningful groups such as product family, shift, or machine group. Drift or subgroup undercoverage is a reason to recalibrate or redesign the uncertainty model.

Prediction intervals quantify predictive uncertainty. They do not establish root cause or causality.

## Replacing demo data with real production data

In a real project, remove the `Generate demo inputs` step from `batch-inference.yml` and replace it with a step that reads data from your approved source: object storage, a database export, an API, or a generated CSV.

Keep the contract expected by `src/leadtime_ml/features.py`, or update the feature schema intentionally and retrain/recalibrate the model. For time-dependent production data, replace the random split with a chronological fit/conformalize/test split to avoid leakage and to make the calibration sample reflect the deployment horizon.
