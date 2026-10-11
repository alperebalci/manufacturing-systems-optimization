from manufacturing_process_optimization.case10_cutting_stock import (
    demo_instance,
    optimize_cutting_stock,
)

lengths, demand = demo_instance()
result = optimize_cutting_stock(lengths, demand)
print("objective:", round(result.objective, 2))
print("new bars:", result.new_bars, "remnants used:", result.remnants_used)
print("produced:", result.produced, "excess:", result.excess)
for pattern, count in result.selected_patterns:
    print(count, "x", pattern)
