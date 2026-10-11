from manufacturing_process_optimization.case03_agv_assignment import (
    demo_instance,
    optimize_assignment,
)

robots, tasks = demo_instance()
result = optimize_assignment(robots, tasks)
print("objective:", round(result.objective, 2))
print("assignment:", result.assignment)
print("emergency:", result.emergency_tasks)
