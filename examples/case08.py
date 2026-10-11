from manufacturing_process_optimization.case08_conwip import optimize_conwip

result = optimize_conwip()
print("best WIP limit:", result.best.wip_limit)
print("throughput/h:", round(result.best.throughput_per_hour, 3))
print("cycle time [min]:", round(result.best.mean_cycle_time, 3))
print("contribution/h:", round(result.best.contribution_per_hour, 2))
