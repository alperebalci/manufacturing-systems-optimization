from manufacturing_process_optimization.case01_production_maintenance import (
    baseline_edd,
    demo_instance,
    optimize_exact,
)

jobs, setup, maintenance = demo_instance()
opt = optimize_exact(jobs, setup, maintenance)
base = baseline_edd(jobs, setup, maintenance)
print("optimal objective:", round(opt.objective, 3))
print("baseline objective:", round(base.objective, 3))
print("sequence:", opt.sequence, "PM position:", opt.maintenance_position)
