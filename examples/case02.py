from manufacturing_process_optimization.case02_milkrun import demo_instance, optimize_milkrun

result = optimize_milkrun(demo_instance())
print("objective:", round(result.objective, 2))
print("intervals [h]:", result.selected_interval)
print("tugger hours:", round(result.tugger_hours, 2))
