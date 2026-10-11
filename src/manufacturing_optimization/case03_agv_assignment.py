"""Case 03 — AGV task assignment with battery reserve, eligibility, deadlines and workload balancing."""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product
import numpy as np
from .validation import make_audit, pct_improvement


@dataclass(frozen=True)
class Instance:
    task_time: np.ndarray
    task_energy: np.ndarray
    due_time: np.ndarray
    priority: np.ndarray
    battery: np.ndarray
    reserve: np.ndarray
    speed_factor: np.ndarray
    eligible: np.ndarray


def demo_instance()->Instance:
    return Instance(
        task_time=np.array([8,6,10,7,5,9,4,6],float),task_energy=np.array([7,5,9,6,4,8,3,5],float),
        due_time=np.array([14,16,22,18,15,25,12,20],float),priority=np.array([2,1,3,2,1,3,2,2],float),
        battery=np.array([29,30,27],float),reserve=np.array([4,4,3],float),speed_factor=np.array([1.0,1.08,0.94]),
        eligible=np.array([[1,1,0],[1,1,1],[1,0,1],[1,1,1],[0,1,1],[1,1,1],[1,1,1],[1,0,1]],int))


def evaluate(ins,assignment):
    v=len(ins.battery); load=np.zeros(v); energy=np.zeros(v); tard=0.0; completion=np.zeros(len(assignment))
    for vehicle in range(v):
        tasks=[j for j,a in enumerate(assignment) if a==vehicle]
        tasks.sort(key=lambda j:(ins.due_time[j],-ins.priority[j]))
        clock=0.0
        for j in tasks:
            clock+=ins.task_time[j]/ins.speed_factor[vehicle]; completion[j]=clock; tard+=ins.priority[j]*max(0,clock-ins.due_time[j]); load[vehicle]=clock; energy[vehicle]+=ins.task_energy[j]
    return load,energy,completion,tard


def solve(instance=None)->dict:
    ins=instance or demo_instance(); nt=len(ins.task_time); nv=len(ins.battery); best=None
    choices=[tuple(np.where(ins.eligible[j]>0)[0]) for j in range(nt)]
    for a in product(*choices):
        load,energy,comp,tard=evaluate(ins,a)
        if np.any(energy>ins.battery-ins.reserve+1e-9): continue
        score=tard+0.8*load.max()+0.2*load.std()
        if best is None or score<best[0]: best=(score,a,load,energy,comp,tard)
    if best is None: raise RuntimeError("No feasible AGV plan")
    score,a,load,energy,comp,tard=best; audit=validate(ins,np.array(a),energy)
    return {"assignment":np.array(a),"vehicle_load":load,"vehicle_energy":energy,"completion":comp,"weighted_tardiness":float(tard),"objective":float(score),"audit":audit}


def baseline(instance=None)->dict:
    ins=instance or demo_instance(); nv=len(ins.battery); a=[]; load=np.zeros(nv); energy=np.zeros(nv)
    for j in np.argsort(ins.due_time):
        feasible=[v for v in range(nv) if ins.eligible[j,v] and energy[v]+ins.task_energy[j]<=ins.battery[v]-ins.reserve[v]+1e-9]
        if not feasible: raise RuntimeError("Baseline infeasible")
        v=min(feasible,key=lambda k:load[k]); a.append((j,v)); load[v]+=ins.task_time[j]/ins.speed_factor[v]; energy[v]+=ins.task_energy[j]
    assignment=np.empty(len(a),dtype=int)
    for j,v in a: assignment[j]=v
    load,energy,comp,tard=evaluate(ins,assignment)
    return {"assignment":assignment,"weighted_tardiness":float(tard),"objective":float(tard+0.8*load.max()+0.2*load.std())}


def validate(ins,a,energy):
    checks={"eligibility":bool(all(ins.eligible[j,v] for j,v in enumerate(a))),"battery_reserve":bool(np.all(energy<=ins.battery-ins.reserve+1e-9)),"all_tasks":len(a)==len(ins.task_time)}
    return make_audit(checks,min_battery_slack=float(np.min(ins.battery-ins.reserve-energy)))


def industrial_benchmark(instance=None):
    ins=instance or demo_instance(); o=solve(ins); b=baseline(ins)
    return {"optimized_objective":o["objective"],"baseline_objective":b["objective"],"objective_improvement_pct":pct_improvement(b["objective"],o["objective"]),"optimized_weighted_tardiness":o["weighted_tardiness"],"baseline_weighted_tardiness":b["weighted_tardiness"],"audit_passed":o["audit"].passed}


if __name__=="__main__": print(industrial_benchmark())
