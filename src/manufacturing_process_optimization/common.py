from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class OptimizationResult:
    """Small common result envelope used by several case studies."""

    objective: float
    decision: Any
    metrics: dict[str, float]


def seeded_rng(seed: int = 42) -> np.random.Generator:
    return np.random.default_rng(seed)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)
