"""Run all ten industrial case-study benchmarks and return one comparison table."""
from __future__ import annotations
import pandas as pd
from . import (
    case01_production_maintenance as c1, case02_milkrun as c2,
    case03_agv_assignment as c3, case04_worker_rotation as c4,
    case05_quality_mdp as c5, case06_cnc_process as c6,
    case07_tooling_scheduling as c7, case08_conwip as c8,
    case09_energy_scheduling as c9, case10_cutting_stock as c10,
)

def run_all() -> pd.DataFrame:
    funcs=[c1.industrial_benchmark,c2.industrial_benchmark,c3.industrial_benchmark,c4.industrial_benchmark,c5.industrial_benchmark,c6.industrial_benchmark,c7.industrial_benchmark,c8.industrial_benchmark,c9.industrial_benchmark,c10.industrial_benchmark]
    rows=[]
    for i,f in enumerate(funcs,1):
        r=f(); rows.append({"case":f"case{i:02d}",**r})
    return pd.DataFrame(rows)

if __name__=="__main__":
    print(run_all().to_string(index=False))
