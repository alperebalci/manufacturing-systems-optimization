from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
from sklearn.model_selection import train_test_split

from leadtime_ml.features import TARGET, validate_features
from leadtime_ml.modeling import (
    build_conformal_predictor,
    build_pipeline,
    predict_with_interval,
    save_predictor,
)

CONFIDENCE_LEVEL = 0.95


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the manufacturing lead-time model.")
    parser.add_argument("--data", default="data/training.csv")
    parser.add_argument("--model-out", default="models/lead_time_pipeline.joblib")
    parser.add_argument("--metrics-out", default="models/metrics.json")
    args = parser.parse_args()

    frame = pd.read_csv(args.data)
    if TARGET not in frame.columns:
        raise ValueError(f"Training data must contain target column: {TARGET}")

    X = validate_features(frame)
    y = frame[TARGET].astype(float)

    X_train, X_holdout, y_train, y_holdout = train_test_split(
        X,
        y,
        test_size=0.4,
        random_state=42,
    )
    X_conformalize, X_test, y_conformalize, y_test = train_test_split(
        X_holdout,
        y_holdout,
        test_size=0.5,
        random_state=42,
    )

    pipeline = build_pipeline(random_state=42)
    pipeline.fit(X_train, y_train)

    predictor = build_conformal_predictor(
        pipeline,
        X_conformalize,
        y_conformalize,
        confidence_level=CONFIDENCE_LEVEL,
    )
    predictions, lower, upper = predict_with_interval(predictor, X_test)

    covered = (y_test.to_numpy() >= lower) & (y_test.to_numpy() <= upper)
    metrics = {
        "mae_hours": round(float(mean_absolute_error(y_test, predictions)), 4),
        "mape": round(float(mean_absolute_percentage_error(y_test, predictions)), 4),
        "prediction_interval_confidence": CONFIDENCE_LEVEL,
        "empirical_interval_coverage": round(float(np.mean(covered)), 4),
        "mean_interval_width_hours": round(float(np.mean(upper - lower)), 4),
        "train_rows": len(y_train),
        "conformalize_rows": len(y_conformalize),
        "test_rows": len(y_test),
        "mean_actual_hours": round(float(np.mean(y_test)), 4),
        "mean_prediction_hours": round(float(np.mean(predictions)), 4),
    }

    save_predictor(predictor, args.model_out)

    metrics_path = Path(args.metrics_out)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
