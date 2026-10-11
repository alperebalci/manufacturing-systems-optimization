"""Compatibility smoke tests for the industrialized v0.2 case APIs."""
from manufacturing_optimization import benchmarks

def test_all_case_benchmarks_return_rows():
    frame = benchmarks.run_all()
    assert len(frame) == 10
    assert frame["case"].tolist() == [f"case{i:02d}" for i in range(1, 11)]
