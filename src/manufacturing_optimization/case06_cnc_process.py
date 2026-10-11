"""Case 06 — CNC cutting-parameter optimization with hard process constraints and benchmark setting."""
from __future__ import annotations
from dataclasses import dataclass, replace
import numpy as np
from scipy.optimize import differential_evolution
from .validation import make_audit, pct_improvement


@dataclass(frozen=True)
class Instance:
    volume: float=9000.0
    roughness_limit: float=2.4
    min_tool_life: float=14.0
    max_power: float=7.2
    hardness_factor: float=1.0


def metrics(x,instance=None):
    ins=instance or Instance(); speed,feed,depth=x
    mrr=speed*feed*depth; cycle=ins.volume/mrr
    tool_life=2.5e8/(ins.hardness_factor*speed**2.35*feed**0.85*depth**0.25)
    roughness=115*feed**2*(1+0.08*(depth-1))
    power=2.5+0.0048*mrr*ins.hardness_factor
    energy=power*cycle/60
    return {"speed":float(speed),"feed":float(feed),"depth":float(depth),"mrr":float(mrr),"cycle_time":float(cycle),"tool_life":float(tool_life),"roughness":float(roughness),"power":float(power),"energy":float(energy)}


def economics(m):
    return 1.15*m["cycle_time"]+20*m["cycle_time"]/max(m["tool_life"],1e-9)+0.24*m["energy"]


def solve(instance=None,seed=42)->dict:
    ins=instance or Instance()
    def obj(x):
        m=metrics(x,ins);pen=2e4*max(0,m["roughness"]-ins.roughness_limit)**2+2e4*max(0,ins.min_tool_life-m["tool_life"])**2+2e4*max(0,m["power"]-ins.max_power)**2
        return economics(m)+pen
    res=differential_evolution(obj,[(90,260),(.08,.28),(.8,2.5)],seed=seed,maxiter=300,polish=True,tol=1e-8)
    x=res.x.copy(); m=metrics(x,ins)
    if m["roughness"]>ins.roughness_limit:
        x[1]*=np.sqrt(ins.roughness_limit/m["roughness"])*0.9999
        m=metrics(x,ins)
    audit=validate(ins,m);m.update({"objective":float(economics(m)),"success":bool(res.success),"audit":audit});return m


def baseline(instance=None)->dict:
    ins=instance or Instance();m=metrics(np.array([160.,.14,1.4]),ins);m["objective"]=economics(m);return m


def validate(ins,m):
    checks={"surface_finish":m["roughness"]<=ins.roughness_limit+1e-4,"tool_life":m["tool_life"]>=ins.min_tool_life-1e-4,"spindle_power":m["power"]<=ins.max_power+1e-4}
    return make_audit(checks,roughness=m["roughness"],tool_life=m["tool_life"],power=m["power"])


def industrial_benchmark(instance=None):
    ins=instance or Instance();o=solve(ins);b=baseline(ins);return {"optimized_cost":o["objective"],"baseline_cost":b["objective"],"cost_improvement_pct":pct_improvement(b["objective"],o["objective"]),"cycle_time_reduction_pct":pct_improvement(b["cycle_time"],o["cycle_time"]),"audit_passed":o["audit"].passed}


def sensitivity(instance=None,hardness=(.85,1.,1.15,1.3)):
    ins=instance or Instance();return [{"hardness_factor":h,**{k:v for k,v in solve(replace(ins,hardness_factor=h)).items() if k in("objective","cycle_time","tool_life","power")}} for h in hardness]


if __name__=="__main__": print(industrial_benchmark())
