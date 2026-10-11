from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import lightgbm as lgb
import numpy as np
from mapie.regression import SplitConformalRegressor
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from .features import CATEGORICAL_FEATURES, NUMERIC_FEATURES


def build_pipeline(random_state: int = 42) -> Pipeline:
    numeric = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )

    categorical = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "one_hot",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=True,
                ),
            ),
        ]
    )

    preprocessing = ColumnTransformer(
        transformers=[
            ("numeric", numeric, NUMERIC_FEATURES),
            ("categorical", categorical, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )

    model = lgb.LGBMRegressor(
        objective="regression_l1",
        n_estimators=500,
        learning_rate=0.035,
        num_leaves=31,
        subsample=0.9,
        colsample_bytree=0.9,
        reg_lambda=0.5,
        random_state=random_state,
        n_jobs=-1,
        verbosity=-1,
    )

    return Pipeline(
        steps=[
            ("preprocess", preprocessing),
            ("model", model),
        ]
    )


def build_conformal_predictor(
    pipeline: Pipeline,
    X_conformalize: Any,
    y_conformalize: Any,
    *,
    confidence_level: float = 0.95,
) -> SplitConformalRegressor:
    """Calibrate marginal prediction intervals around an already-fitted pipeline."""
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must be between 0 and 1")

    predictor = SplitConformalRegressor(
        estimator=pipeline,
        confidence_level=confidence_level,
        prefit=True,
    )
    predictor.conformalize(X_conformalize, y_conformalize)
    return predictor


def predict_with_interval(
    predictor: SplitConformalRegressor,
    X: Any,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return point predictions plus lower/upper conformal prediction bounds."""
    predictions, intervals = predictor.predict_interval(X)
    bounds = np.asarray(intervals, dtype=float)

    if bounds.ndim != 3 or bounds.shape[1:] != (2, 1):
        raise RuntimeError(f"Unexpected MAPIE interval shape: {bounds.shape}")

    return (
        np.asarray(predictions, dtype=float),
        bounds[:, 0, 0],
        bounds[:, 1, 0],
    )


def save_pipeline(pipeline: Pipeline, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, path)


def load_pipeline(path: str | Path) -> Pipeline:
    return joblib.load(path)


def save_predictor(predictor: SplitConformalRegressor, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(predictor, path)


def load_predictor(path: str | Path) -> SplitConformalRegressor:
    return joblib.load(path)
