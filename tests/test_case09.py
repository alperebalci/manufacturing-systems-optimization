from manufacturing_process_optimization.case09_energy_scheduling import (
    demo_instance,
    optimize_energy_schedule,
)


def test_energy_schedule_satisfies_inventory_balance():
    demand, price = demo_instance()
    result = optimize_energy_schedule(demand, price)
    inventory = 10.0
    for t in range(len(demand)):
        inventory += result.production[t] - demand[t]
        assert abs(inventory - result.inventory[t]) < 1e-6
        assert result.production[t] <= 65.0 * result.machine_on[t] + 1e-6
    assert abs(result.inventory[-1]) < 1e-6
    assert result.peak_kw >= 0
