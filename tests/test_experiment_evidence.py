"""Offline unit tests for provenance-aware benchmark evidence exports."""

import json

import numpy as np
import pytest

from manufacturing_optimization.experiment_evidence import collect_evidence


def clock_from(values):
    iterator = iter(values)
    return lambda: next(iterator)


def test_serializes_numpy_and_marks_explicit_scope():
    report = collect_evidence(
        [(
            "case99",
            lambda: {
                "audit_passed": np.bool_(True),
                "optimized_cost": np.float64(12.25),
                "policy": np.array([0, 1, 0], dtype=np.int64),
            },
        )],
        clock=clock_from([1.0, 1.125]),
        captured_at="2026-10-10T00:00:00+00:00",
    )
    assert report["evidence_tier"] == "small_demo_validation"
    assert report["industrial_scalability_evaluated"] is False
    assert report["audit_summary"] == "all_reported_pass"
    assert report["cases"][0]["wall_time_seconds"] == pytest.approx(0.125)
    assert report["cases"][0]["result"]["policy"] == [0, 1, 0]
    assert len(report["result_fingerprint"]) == 64
    assert json.loads(json.dumps(report, allow_nan=False)) == report


def test_absent_audit_is_not_reported_not_success():
    report = collect_evidence(
        [("case08", lambda: {"throughput": 0.3})],
        clock=clock_from([2.0, 2.1]),
    )
    assert report["audit_summary"] == "partial_not_reported"
    assert report["cases"][0]["audit_status"] == "not_reported"


def test_rejects_failed_audit_and_nonfinite_measurements():
    with pytest.raises(ValueError, match="feasibility audit failed"):
        collect_evidence(
            [("case01", lambda: {"audit_passed": False})],
            clock=clock_from([1.0, 1.1]),
        )
    with pytest.raises(ValueError, match="nonfinite"):
        collect_evidence(
            [("case02", lambda: {"objective": float("nan")})],
            clock=clock_from([1.0, 1.1]),
        )


def test_fingerprint_ignores_runtime_and_collection_timestamp():
    runner = ("case01", lambda: {"audit_passed": True, "optimized_cost": 5.0})
    first = collect_evidence(
        [runner], clock=clock_from([1.0, 1.1]), captured_at="first"
    )
    second = collect_evidence(
        [runner], clock=clock_from([1.0, 5.0]), captured_at="second"
    )
    assert first["result_fingerprint"] == second["result_fingerprint"]
    assert first["cases"][0]["wall_time_seconds"] != second["cases"][0]["wall_time_seconds"]


def test_rejects_duplicate_cases_and_invalid_runtime():
    with pytest.raises(ValueError, match="unique"):
        collect_evidence(
            [("case01", lambda: {}), ("case01", lambda: {})],
            clock=clock_from([1.0, 1.1]),
        )
    with pytest.raises(ValueError, match="invalid elapsed"):
        collect_evidence(
            [("case01", lambda: {})],
            clock=clock_from([2.0, 1.0]),
        )
