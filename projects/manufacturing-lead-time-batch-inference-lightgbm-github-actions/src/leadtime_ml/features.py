from __future__ import annotations

import pandas as pd

TARGET = "lead_time_hours"

NUMERIC_FEATURES = [
    "order_quantity",
    "machine_utilization",
    "queue_length",
    "setup_minutes",
    "operator_experience_years",
    "material_availability_pct",
    "priority_score",
]

CATEGORICAL_FEATURES = [
    "product_family",
    "shift",
    "machine_group",
]

FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def validate_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate and return model features in a deterministic column order."""
    missing = [column for column in FEATURES if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing required feature columns: {missing}")

    clean = frame.loc[:, FEATURES].copy()

    if (clean["order_quantity"] <= 0).any():
        raise ValueError("order_quantity must be positive")

    utilization = clean["machine_utilization"]
    if ((utilization < 0) | (utilization > 1)).any():
        raise ValueError("machine_utilization must be between 0 and 1")

    availability = clean["material_availability_pct"]
    if ((availability < 0) | (availability > 100)).any():
        raise ValueError("material_availability_pct must be between 0 and 100")

    return clean
