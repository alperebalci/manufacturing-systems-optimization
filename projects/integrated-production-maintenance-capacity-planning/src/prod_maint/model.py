"""Joint production, inventory, backlog, and preventive-maintenance planning MILP."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike,NDArray
from scipy.optimize import Bounds,LinearConstraint,milp


@dataclass(frozen=True)
class PMInstance:
    demand:NDArray[np.float64]
    capacity:NDArray[np.float64]
    initial_age:float
    maintenance_hours:float
    maintenance_cost:float
    production_cost:float
    holding_cost:float
    backlog_cost:float
    risk_cost:float
    max_age:float

    @classmethod
    def from_arrays(
        cls,
        demand:ArrayLike,
        capacity:ArrayLike,
        *,
        initial_age:float=0.0,
        maintenance_hours:float=2.0,
        maintenance_cost:float=4.0,
        production_cost:float=1.0,
        holding_cost:float=.2,
        backlog_cost:float=30.0,
        risk_cost:float=.1,
        max_age:float=100.0,
    )->"PMInstance":
        d=np.asarray(demand,float);cap=np.asarray(capacity,float)
        if d.ndim!=1 or cap.shape!=d.shape:
            raise ValueError("demand/capacity mismatch")
        return cls(d,cap,float(initial_age),float(maintenance_hours),float(maintenance_cost),
                   float(production_cost),float(holding_cost),float(backlog_cost),
                   float(risk_cost),float(max_age))


@dataclass(frozen=True)
class PMResult:
    production:NDArray[np.float64]
    maintenance:NDArray[np.int64]
    age:NDArray[np.float64]
    inventory:NDArray[np.float64]
    backlog:NDArray[np.float64]
    objective:float


def solve_joint(instance:PMInstance)->PMResult:
    T=len(instance.demand)
    # prod, maint, age, inv, back
    p0=0;m0=T;a0=2*T;i0=3*T;b0=4*T;n=5*T
    c=np.zeros(n)
    c[p0:m0]=instance.production_cost
    c[m0:a0]=instance.maintenance_cost
    c[a0:i0]=instance.risk_cost
    c[i0:b0]=instance.holding_cost
    c[b0:]=instance.backlog_cost
    lb=np.zeros(n);ub=np.full(n,np.inf);integ=np.zeros(n,int)
    ub[m0:a0]=1;integ[m0:a0]=1
    ub[a0:i0]=instance.max_age
    rows=[];lows=[];highs=[]
    # capacity: maintenance consumes capacity
    for t in range(T):
        row=np.zeros(n);row[p0+t]=1;row[m0+t]=instance.maintenance_hours
        rows.append(row);lows.append(-np.inf);highs.append(instance.capacity[t])
    # age reset/update with big-M; maintenance at start, then current production adds usage
    M=instance.max_age+float(np.sum(instance.capacity))+1.0
    for t in range(T):
        prev_const=instance.initial_age if t==0 else 0.0
        # age = prev_age + production when no maintenance
        row=np.zeros(n);row[a0+t]=1;row[p0+t]=-1
        if t>0: row[a0+t-1]-=1
        row[m0+t]-=M
        rows.append(row);lows.append(prev_const-M);highs.append(np.inf)
        row=np.zeros(n);row[a0+t]=1;row[p0+t]=-1
        if t>0: row[a0+t-1]-=1
        row[m0+t]+=M
        rows.append(row);lows.append(-np.inf);highs.append(prev_const+M)
        # if maintenance=1, age cannot exceed production in that period
        row=np.zeros(n);row[a0+t]=1;row[p0+t]=-1;row[m0+t]+=M
        rows.append(row);lows.append(-np.inf);highs.append(M)
    # inventory-backlog balance
    for t in range(T):
        row=np.zeros(n);row[i0+t]=1;row[b0+t]=-1;row[p0+t]=-1
        if t>0:
            row[i0+t-1]-=1;row[b0+t-1]+=1
        rows.append(row);lows.append(-instance.demand[t]);highs.append(-instance.demand[t])
    res=milp(c=c,integrality=integ,bounds=Bounds(lb,ub),constraints=LinearConstraint(np.stack(rows),lows,highs))
    if not res.success or res.x is None:
        raise RuntimeError(res.message)
    x=res.x
    return PMResult(
        production=x[p0:m0],
        maintenance=np.rint(x[m0:a0]).astype(int),
        age=x[a0:i0],
        inventory=x[i0:b0],
        backlog=x[b0:],
        objective=float(res.fun),
    )
