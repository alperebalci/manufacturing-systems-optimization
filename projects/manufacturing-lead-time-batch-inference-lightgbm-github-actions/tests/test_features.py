import pandas as pd
import pytest

from leadtime_ml.features import validate_features


def valid_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "order_quantity": 120,
                "machine_utilization": 0.75,
                "queue_length": 4,
                "setup_minutes": 35,
                "operator_experience_years": 6,
                "material_availability_pct": 94,
                "priority_score": 3,
                "product_family": "B",
                "shift": "day",
                "machine_group": "M2",
            }
        ]
    )


def test_validate_features_accepts_valid_data():
    clean = validate_features(valid_frame())
    assert len(clean) == 1


def test_validate_features_rejects_bad_utilization():
    frame = valid_frame()
    frame.loc[0, "machine_utilization"] = 1.2
    with pytest.raises(ValueError, match="machine_utilization"):
        validate_features(frame)
