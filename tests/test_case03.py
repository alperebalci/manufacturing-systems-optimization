from manufacturing_process_optimization.case03_agv_assignment import (
    demo_instance,
    optimize_assignment,
)


def test_every_transport_task_is_accounted_for():
    robots, tasks = demo_instance()
    result = optimize_assignment(robots, tasks)
    covered = set(result.assignment) | set(result.emergency_tasks)
    assert covered == {t.task_id for t in tasks}
    for robot in robots:
        assert result.robot_load_minutes[robot.name] <= robot.available_minutes + 1e-7
        assert result.robot_battery_use[robot.name] <= robot.battery_budget + 1e-7
