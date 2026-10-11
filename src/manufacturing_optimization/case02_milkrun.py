"""Case 02 — capacitated milk-run replenishment with storage, safety stock and emergency supply."""
from __future__ import annotations
from dataclasses import dataclass, replace
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from .validation import make_audit, pct_improvement


@dataclass(frozen=True)
class Instance:
    demand: np.ndarray
    initial_inventory: np.ndarray
    storage_capacity: np.ndarray
    safety_stock: np.ndarray
    vehicle_capacity: float = 34.0
    trip_cost: float = 58.0
    holding_cost: float = 0.7
    emergency_cost: float = 28.0
    max_trips_per_period: int = 2


def demo_instance() -> Instance:
    return Instance(
        demand=np.array([[8,10,7,11,9,10],[6,9,8,7,10,8],[5,6,9,8,7,9]],dtype=float),
        initial_inventory=np.array([12,10,9],dtype=float),
        storage_capacity=np.array([24,21,20],dtype=float),
        safety_stock=np.array([3,2,2],dtype=float),
    )


def solve(instance: Instance|None=None)->dict:
    ins=instance or demo_instance(); s,t=ins.demand.shape
    nq=s*t; ni=s*t; ne=s*t; q0=0; i0=nq; e0=nq+ni; y0=nq+ni+ne; n=y0+t
    c=np.zeros(n); c[i0:i0+ni]=ins.holding_cost; c[e0:e0+ne]=ins.emergency_cost; c[y0:]=ins.trip_cost
    integ=np.zeros(n,dtype=int); integ[y0:]=1
    lb=np.zeros(n); ub=np.full(n,np.inf); ub[y0:]=ins.max_trips_per_period
    rows=[]; lo=[]; hi=[]
    idx=lambda base,st,p: base+st*t+p
    for st in range(s):
        for p in range(t):
            row=np.zeros(n); row[idx(i0,st,p)]=1; row[idx(q0,st,p)]=-1; row[idx(e0,st,p)]=-1
            rhs=-ins.demand[st,p]
            if p==0: rhs+=ins.initial_inventory[st]
            else: row[idx(i0,st,p-1)]=-1
            rows.append(row); lo.append(rhs); hi.append(rhs)
            row=np.zeros(n); row[idx(i0,st,p)]=1
            rows.append(row); lo.append(ins.safety_stock[st]); hi.append(ins.storage_capacity[st])
    for p in range(t):
        row=np.zeros(n)
        for st in range(s): row[idx(q0,st,p)]=1
        row[y0+p]=-ins.vehicle_capacity
        rows.append(row); lo.append(-np.inf); hi.append(0)
    res=milp(c=c,integrality=integ,bounds=Bounds(lb,ub),constraints=LinearConstraint(np.vstack(rows),np.array(lo),np.array(hi)))
    if not res.success: raise RuntimeError(res.message)
    q=res.x[q0:q0+nq].reshape(s,t); inv=res.x[i0:i0+ni].reshape(s,t); emerg=res.x[e0:e0+ne].reshape(s,t); trips=np.rint(res.x[y0:]).astype(int)
    audit=validate(ins,q,inv,emerg,trips)
    return {"deliveries":q,"inventory":inv,"emergency":emerg,"trips":trips,"total_cost":float(res.fun),"emergency_units":float(emerg.sum()),"audit":audit}


def baseline(instance: Instance|None=None)->dict:
    ins=instance or demo_instance(); s,t=ins.demand.shape
    inv=ins.initial_inventory.copy(); cost=0.0; emergency=0.0; trips=[]
    for p in range(t):
        target=np.minimum(ins.storage_capacity, ins.demand[:,p]+ins.safety_stock)
        required=np.maximum(0,target-inv)
        cap=ins.vehicle_capacity*ins.max_trips_per_period
        delivered=np.zeros(s)
        for st in np.argsort(inv-ins.safety_stock):
            qty=min(required[st],cap-delivered.sum()); delivered[st]=qty
        needed=np.maximum(0,ins.demand[:,p]+ins.safety_stock-(inv+delivered))
        emergency+=needed.sum(); inv=inv+delivered+needed-ins.demand[:,p]
        k=int(np.ceil(delivered.sum()/ins.vehicle_capacity-1e-12)) if delivered.sum()>0 else 0
        trips.append(k); cost+=k*ins.trip_cost+ins.holding_cost*inv.sum()+ins.emergency_cost*needed.sum()
    return {"total_cost":float(cost),"emergency_units":float(emergency),"trips":np.array(trips)}


def validate(ins,q,inv,emerg,trips):
    s,t=ins.demand.shape; prev=ins.initial_inventory.copy(); maxbal=0.0
    for p in range(t):
        calc=prev+q[:,p]+emerg[:,p]-ins.demand[:,p]
        maxbal=max(maxbal,float(np.max(np.abs(calc-inv[:,p])))); prev=inv[:,p]
    checks={"balance":maxbal<1e-7,"storage":bool(np.all(inv<=ins.storage_capacity[:,None]+1e-7)),"safety_stock":bool(np.all(inv>=ins.safety_stock[:,None]-1e-7)),"vehicle_capacity":bool(np.all(q.sum(axis=0)<=trips*ins.vehicle_capacity+1e-7)),"trip_limit":bool(np.all(trips<=ins.max_trips_per_period))}
    return make_audit(checks,max_balance_error=maxbal)


def industrial_benchmark(instance=None):
    ins=instance or demo_instance(); o=solve(ins); b=baseline(ins)
    return {"optimized_cost":o["total_cost"],"baseline_cost":b["total_cost"],"cost_improvement_pct":pct_improvement(b["total_cost"],o["total_cost"]),"optimized_emergency_units":o["emergency_units"],"baseline_emergency_units":b["emergency_units"],"audit_passed":o["audit"].passed}


def sensitivity(instance=None,capacities=(24,30,34,40,48)):
    ins=instance or demo_instance(); out=[]
    for cap in capacities:
        r=solve(replace(ins,vehicle_capacity=float(cap))); out.append({"vehicle_capacity":cap,"cost":r["total_cost"],"emergency_units":r["emergency_units"],"trips":int(r["trips"].sum())})
    return out


if __name__=="__main__": print(industrial_benchmark())
