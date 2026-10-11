from manufacturing_process_optimization.case01_production_maintenance import (
    baseline_edd,
    demo_instance,
    optimize_exact,
)


def test_exact_not_worse_than_edd():
    jobs, setup, maintenance = demo_instance()
    opt = optimize_exact(jobs, setup, maintenance)
    base = baseline_edd(jobs, setup, maintenance)
    assert opt.objective <= base.objective + 1e-9
    assert sorted(opt.sequence) == sorted(j.job_id for j in jobs)
    assert 0 <= opt.maintenance_position <= len(jobs)
