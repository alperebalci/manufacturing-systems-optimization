from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def make_orders(n_rows: int, seed: int, include_target: bool) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    product_family = rng.choice(["A", "B", "C", "D"], size=n_rows, p=[0.35, 0.30, 0.20, 0.15])
    shift = rng.choice(["day", "evening", "night"], size=n_rows, p=[0.50, 0.30, 0.20])
    machine_group = rng.choice(["M1", "M2", "M3", "M4"], size=n_rows)

    order_quantity = rng.integers(20, 600, size=n_rows)
    machine_utilization = np.clip(rng.beta(5, 2, size=n_rows), 0.05, 0.99)
    queue_length = rng.poisson(7, size=n_rows)
    setup_minutes = np.clip(rng.normal(55, 22, size=n_rows), 5, 180)
    operator_experience_years = np.clip(rng.gamma(2.3, 2.0, size=n_rows), 0, 25)
    material_availability_pct = np.clip(rng.normal(91, 8, size=n_rows), 45, 100)
    priority_score = rng.integers(1, 6, size=n_rows)

    frame = pd.DataFrame(
        {
            "order_id": [f"ORD-{seed}-{i:05d}" for i in range(n_rows)],
            "order_quantity": order_quantity,
            "machine_utilization": machine_utilization,
            "queue_length": queue_length,
            "setup_minutes": setup_minutes,
            "operator_experience_years": operator_experience_years,
            "material_availability_pct": material_availability_pct,
            "priority_score": priority_score,
            "product_family": product_family,
            "shift": shift,
            "machine_group": machine_group,
        }
    )

    if include_target:
        product_effect = pd.Series(product_family).map({"A": 0, "B": 3, "C": 7, "D": 12}).to_numpy()
        shift_effect = pd.Series(shift).map({"day": 0, "evening": 2, "night": 4}).to_numpy()
        machine_effect = pd.Series(machine_group).map({"M1": 0, "M2": 1, "M3": 3, "M4": 5}).to_numpy()

        lead_time = (
            8
            + 0.045 * order_quantity
            + 22 * machine_utilization
            + 1.7 * queue_length
            + 0.055 * setup_minutes
            - 0.45 * operator_experience_years
            + 0.28 * (100 - material_availability_pct)
            - 1.2 * priority_score
            + product_effect
            + shift_effect
            + machine_effect
            + rng.normal(0, 3.5, size=n_rows)
        )
        frame["lead_time_hours"] = np.clip(lead_time, 2, None)

    return frame


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-rows", type=int, default=2500)
    parser.add_argument("--score-rows", type=int, default=100)
    args = parser.parse_args()

    train_path = Path("data/training.csv")
    score_path = Path("data/incoming/orders_to_score.csv")
    train_path.parent.mkdir(parents=True, exist_ok=True)
    score_path.parent.mkdir(parents=True, exist_ok=True)

    make_orders(args.train_rows, seed=42, include_target=True).to_csv(train_path, index=False)
    make_orders(args.score_rows, seed=2026, include_target=False).to_csv(score_path, index=False)

    print(f"Wrote {train_path}")
    print(f"Wrote {score_path}")


if __name__ == "__main__":
    main()
