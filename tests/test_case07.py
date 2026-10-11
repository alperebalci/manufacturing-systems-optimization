from manufacturing_process_optimization.case07_tooling_scheduling import (
    demo_instance,
    optimize_exact,
)


def test_tooling_schedule_assigns_every_job_once():
    machines, jobs, change = demo_instance()
    result = optimize_exact(machines, jobs, change)
    scheduled = [j for seq in result.machine_sequences.values() for j in seq]
    assert sorted(scheduled) == sorted(j.job_id for j in jobs)
    assert abs(result.makespan - max(result.machine_completion.values())) < 1e-9
