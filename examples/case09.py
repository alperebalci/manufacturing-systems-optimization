from manufacturing_process_optimization.case09_energy_scheduling import (
    demo_instance,
    optimize_energy_schedule,
)

result = optimize_energy_schedule(*demo_instance())
print("objective:", round(result.objective, 2))
print("production:", result.production.round(2).tolist())
print("inventory:", result.inventory.round(2).tolist())
print("peak kW:", round(result.peak_kw, 2))
