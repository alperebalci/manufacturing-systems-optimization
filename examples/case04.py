from manufacturing_process_optimization.case04_worker_rotation import (
    demo_instance,
    optimize_rotation,
)

workers, stations = demo_instance()
result = optimize_rotation(workers, stations)
print("objective:", round(result.objective, 2))
print("exposure:", result.worker_exposure)
print("switches:", result.switches)
