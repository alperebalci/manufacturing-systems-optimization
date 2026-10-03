from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from leadtime_ml.features import validate_features
from leadtime_ml.modeling import load_predictor, predict_with_interval


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run batch inference with conformal prediction intervals."
    )
    parser.add_argument("--input", default="data/incoming/orders_to_score.csv")
    parser.add_argument("--model", default="models/lead_time_pipeline.joblib")
    parser.add_argument("--output", default="data/predictions/latest_predictions.csv")
    args = parser.parse_args()

    source = pd.read_csv(args.input)
    features = validate_features(source)
    predictor = load_predictor(args.model)

    predictions, lower, upper = predict_with_interval(predictor, features)

    output = source.copy()
    output["predicted_lead_time_hours"] = predictions.round(2)
    output["prediction_lower_hours"] = lower.round(2)
    output["prediction_upper_hours"] = upper.round(2)
    output["prediction_interval_confidence"] = float(predictor.confidence_level)
    output["scored_at_utc"] = datetime.now(UTC).replace(microsecond=0).isoformat()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(output_path, index=False)

    print(f"Scored {len(output)} orders -> {output_path}")


if __name__ == "__main__":
    main()
