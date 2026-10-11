from manufacturing_process_optimization.case07_tooling_scheduling import (
    demo_instance,
    optimize_exact,
)

machines, jobs, change = demo_instance()
result = optimize_exact(machines, jobs, change)
print("objective:", round(result.objective, 3))
print("makespan:", round(result.makespan, 3))
print("sequences:", result.machine_sequences)
