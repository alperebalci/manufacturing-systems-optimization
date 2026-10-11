from __future__ import annotations

from dataclasses import dataclass

import numpy as np

STATES = ("stable", "drifting", "unstable")
ACTIONS = ("skip", "sample", "full")


@dataclass(frozen=True)
class QualityMDP:
    transitions: dict[str, np.ndarray]
    immediate_cost: dict[str, np.ndarray]
    discount: float = 0.97


@dataclass(frozen=True)
class QualityPolicyResult:
    values: dict[str, float]
    policy: dict[str, str]
    iterations: int
    bellman_residual: float


def build_default_mdp() -> QualityMDP:
    transitions = {
        "skip": np.array(
            [
                [0.82, 0.16, 0.02],
                [0.05, 0.72, 0.23],
                [0.01, 0.14, 0.85],
            ],
            dtype=float,
        ),
        "sample": np.array(
            [
                [0.90, 0.09, 0.01],
                [0.20, 0.68, 0.12],
                [0.06, 0.42, 0.52],
            ],
            dtype=float,
        ),
        "full": np.array(
            [
                [0.96, 0.04, 0.00],
                [0.58, 0.39, 0.03],
                [0.30, 0.58, 0.12],
            ],
            dtype=float,
        ),
    }
    immediate_cost = {
        "skip": np.array([7.0, 38.0, 132.0]),
        "sample": np.array([14.0, 27.0, 74.0]),
        "full": np.array([31.0, 36.0, 48.0]),
    }
    return QualityMDP(transitions=transitions, immediate_cost=immediate_cost, discount=0.97)


def value_iteration(
    mdp: QualityMDP,
    tolerance: float = 1e-10,
    max_iter: int = 100_000,
) -> QualityPolicyResult:
    n_states = len(STATES)
    V = np.zeros(n_states)
    for iteration in range(1, max_iter + 1):
        q = np.vstack(
            [
                mdp.immediate_cost[a] + mdp.discount * mdp.transitions[a] @ V
                for a in ACTIONS
            ]
        )
        V_new = np.min(q, axis=0)
        residual = float(np.max(np.abs(V_new - V)))
        V = V_new
        if residual < tolerance:
            break
    else:
        raise RuntimeError("Value iteration failed to converge")

    q_final = np.vstack(
        [mdp.immediate_cost[a] + mdp.discount * mdp.transitions[a] @ V for a in ACTIONS]
    )
    action_idx = np.argmin(q_final, axis=0)
    policy = {state: ACTIONS[int(action_idx[i])] for i, state in enumerate(STATES)}
    values = {state: float(V[i]) for i, state in enumerate(STATES)}
    bellman = np.min(q_final, axis=0)
    bellman_residual = float(np.max(np.abs(V - bellman)))
    return QualityPolicyResult(values, policy, iteration, bellman_residual)


def evaluate_stationary_policy(mdp: QualityMDP, policy: dict[str, str]) -> dict[str, float]:
    P = np.zeros((len(STATES), len(STATES)))
    c = np.zeros(len(STATES))
    for i, state in enumerate(STATES):
        action = policy[state]
        P[i] = mdp.transitions[action][i]
        c[i] = mdp.immediate_cost[action][i]
    V = np.linalg.solve(np.eye(len(STATES)) - mdp.discount * P, c)
    return {state: float(V[i]) for i, state in enumerate(STATES)}
