import numpy as np

from prod_maint import PMInstance,solve_joint


def test_joint_plan_meets_demand_when_capacity_allows():
    inst=PMInstance.from_arrays([4,4,4],[8,8,8],risk_cost=.2,maintenance_cost=2)
    r=solve_joint(inst)
    assert np.all(r.backlog<1e-7)
    assert np.all(r.production+r.maintenance*inst.maintenance_hours<=inst.capacity+1e-8)


def test_high_risk_penalty_can_trigger_preventive_maintenance():
    low=solve_joint(PMInstance.from_arrays([3,3,3],[8,8,8],initial_age=10,risk_cost=0,maintenance_cost=1))
    high=solve_joint(PMInstance.from_arrays([3,3,3],[8,8,8],initial_age=10,risk_cost=5,maintenance_cost=1))
    assert high.maintenance.sum()>=low.maintenance.sum()
    assert high.age.sum()<=low.age.sum()+1e-8
