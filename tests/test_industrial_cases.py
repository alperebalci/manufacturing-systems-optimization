import numpy as np
from manufacturing_optimization import (
    case01_production_maintenance as c1, case02_milkrun as c2,
    case03_agv_assignment as c3, case04_worker_rotation as c4,
    case05_quality_mdp as c5, case06_cnc_process as c6,
    case07_tooling_scheduling as c7, case08_conwip as c8,
    case09_energy_scheduling as c9, case10_cutting_stock as c10,
)

def test_case01_industrial():
    r=c1.solve(); assert r["audit"].passed; assert len(r["assignment"])==8; assert np.all(r["overtime_hours"]>=0)

def test_case02_industrial():
    r=c2.solve(); assert r["audit"].passed; assert r["deliveries"].shape==(3,6)

def test_case03_industrial():
    r=c3.solve(); assert r["audit"].passed; assert len(r["assignment"])==8

def test_case04_industrial():
    r=c4.solve(); assert r["audit"].passed; assert r["schedule"].sum()==15

def test_case05_industrial():
    r=c5.solve(); assert r["audit"].passed; assert c5.industrial_benchmark()["exhaustive_optimum_match"]

def test_case06_industrial():
    r=c6.solve(); assert r["audit"].passed; assert r["success"]

def test_case07_industrial():
    r=c7.solve(); assert r["audit"].passed; assert len(r["press_0"])+len(r["press_1"])==6

def test_case08_industrial():
    r=c8.solve(caps=range(2,6),seeds=range(4)); assert 2<=r["wip_cap"]<=5; assert r["throughput"]>0

def test_case09_industrial():
    r=c9.solve(); assert r["audit"].passed; assert len(r["start_times"])==5

def test_case10_industrial():
    r=c10.solve(); assert r["audit"].passed; assert np.all(r["produced"]>=r["demand"])
