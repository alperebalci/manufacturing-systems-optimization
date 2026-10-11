from pathlib import Path

import numpy as np
import pandas as pd

from leadtime_ml.features import TARGET, validate_features
from leadtime_ml.modeling import (
    build_conformal_predictor,
    build_pipeline,
    load_pipeline,
    load_predictor,
    predict_with_interval,
    save_pipeline,
    save_predictor,
)


def _training_frame() -> pd.DataFrame:
    base = pd.DataFrame(
        [
            [100, 0.60, 3, 30, 4, 95, 3, "A", "day", "M1", 24.0],
            [220, 0.80, 8, 60, 2, 82, 2, "B", "night", "M3", 49.0],
            [160, 0.72, 5, 40, 8, 97, 5, "C", "evening", "M2", 32.0],
            [320, 0.90, 12, 75, 3, 76, 1, "D", "night", "M4", 69.0],
            [90, 0.55, 2, 25, 10, 99, 4, "A", "day", "M1", 18.0],
            [260, 0.84, 7, 55, 5, 88, 2, "B", "evening", "M2", 45.0],
        ],
        columns=[
            "order_quantity",
            "machine_utilization",
            "queue_length",
            "setup_minutes",
            "operator_experience_years",
            "material_availability_pct",
            "priority_score",
            "product_family",
            "shift",
            "machine_group",
            TARGET,
        ],
    )

    frames = []
    for offset in np.linspace(-2.0, 2.0, 5):
        copy = base.copy()
        copy[TARGET] = copy[TARGET] + offset
        frames.append(copy)
    return pd.concat(frames, ignore_index=True)


def test_pipeline_round_trip(tmp_path: Path):
    frame = _training_frame()
    X = validate_features(frame)
    y = frame[TARGET]

    pipeline = build_pipeline()
    pipeline.set_params(model__n_estimators=10)
    pipeline.fit(X, y)

    path = tmp_path / "model.joblib"
    save_pipeline(pipeline, path)
    loaded = load_pipeline(path)

    predictions = loaded.predict(X)
    assert len(predictions) == len(frame)


def test_conformal_predictor_round_trip(tmp_path: Path):
    frame = _training_frame()
    X = validate_features(frame)
    y = frame[TARGET]

    X_train = X.iloc[:18]
    y_train = y.iloc[:18]
    X_conformalize = X.iloc[18:]
    y_conformalize = y.iloc[18:]

    pipeline = build_pipeline()
    pipeline.set_params(model__n_estimators=10)
    pipeline.fit(X_train, y_train)

    predictor = build_conformal_predictor(
        pipeline,
        X_conformalize,
        y_conformalize,
        confidence_level=0.90,
    )

    path = tmp_path / "conformal_model.joblib"
    save_predictor(predictor, path)
    loaded = load_predictor(path)

    predictions, lower, upper = predict_with_interval(loaded, X.iloc[:5])

    assert len(predictions) == 5
    assert np.all(lower <= predictions)
    assert np.all(predictions <= upper)
    assert float(loaded.confidence_level) == 0.90
