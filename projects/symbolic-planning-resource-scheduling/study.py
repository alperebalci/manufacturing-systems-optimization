"""Bounded monotone symbolic planning integrated with resource-constrained scheduling."""
from __future__ import annotations
from dataclasses import dataclass
import argparse
import itertools
import json
from pathlib import Path
import numpy as np
from scipy.optimize import milp,Bounds,LinearConstraint

@dataclass(frozen=True)
class Action:
    name:str
    pre:frozenset
    add:frozenset
    duration:int
    resource:str
    cost:float=0.0


def audit(actions,starts,initial,goals,capacities,H):
    by={a.name:a for a in actions}
    if set(starts)-set(by):return False
    produced=set(initial)
    for name,t in starts.items():
        a=by[name]
        if type(t)!=int or t<0 or t+a.duration>H:return False
        if produced&a.add:return False
        produced|=a.add
    if not set(goals)<=produced:return False
    for name,t in starts.items():
        known=set(initial)
        for other,s in starts.items():
            if s+by[other].duration<=t:known|=by[other].add
        if not by[name].pre<=known:return False
    for r,caps in capacities.items():
        for t in range(H):
            busy=sum(by[name].resource==r and s<=t<s+by[name].duration for name,s in starts.items())
            if busy>caps[t]:return False
    return True


def plan(actions,initial,goals,capacities,H,fixed=None,earliest_new_start=0):
    fixed={} if fixed is None else dict(fixed)
    if (type(H)!=int or H<1 or not actions or len({a.name for a in actions})!=len(actions)
        or any(type(a.duration)!=int or a.duration<1 or a.cost<0 or not np.isfinite(a.cost)
               or a.resource not in capacities or not a.add for a in actions)):
        raise ValueError('Invalid actions/horizon/resources')
    for c in capacities.values():
        if len(c)!=H or not np.isfinite(c).all() or np.any(np.asarray(c)<0):raise ValueError('Capacity calendar')
    if type(earliest_new_start)!=int or not 0<=earliest_new_start<=H:raise ValueError('Replanning time')
    slots=[(a,t) for a in actions for t in range(H-a.duration+1)
           if a.name in fixed or t>=earliest_new_start]
    index={(a.name,t):j for j,(a,t) in enumerate(slots)};N=len(slots)+1
    rows=[];low=[];high=[]
    def add(terms,l=-np.inf,u=np.inf):
        row=np.zeros(N)
        for j,v in terms:row[j]+=v
        rows.append(row);low.append(l);high.append(u)
    for a in actions:add([(j,1) for j,(b,t) in enumerate(slots) if b.name==a.name],u=1)
    facts=set(initial)|set(goals)|set().union(*(a.pre|a.add for a in actions))
    for f in facts:
        terms=[(j,1) for j,(a,t) in enumerate(slots) if f in a.add]
        add(terms,l=int(f in goals and f not in initial),u=int(f not in initial))
    for j,(a,t) in enumerate(slots):
        for p in a.pre:
            add([(j,1)]+[(k,-1) for k,(b,s) in enumerate(slots) if p in b.add and s+b.duration<=t],u=int(p in initial))
        add([(j,t+a.duration),(N-1,-1)],u=0)
    for resource,caps in capacities.items():
        for t in range(H):
            add([(j,1) for j,(a,s) in enumerate(slots) if a.resource==resource and s<=t<s+a.duration],u=caps[t])
    for name,t in fixed.items():
        if (name,t) not in index:raise ValueError('Invalid fixed action start')
        add([(index[name,t],1)],1,1)
    weight=1+sum(a.cost for a in actions)
    c=np.r_[[a.cost for a,t in slots],weight]
    r=milp(c,integrality=np.r_[np.ones(N-1),0],bounds=Bounds(np.zeros(N),np.r_[np.ones(N-1),H]),
           constraints=LinearConstraint(np.array(rows),low,high),options={'time_limit':10.,'mip_rel_gap':0.0})
    if r.status==2:return {'status':'infeasible','starts':None}
    if r.status!=0 or r.x is None:raise RuntimeError(f'Unproven planning result: {r.message}')
    starts={a.name:int(t) for j,(a,t) in enumerate(slots) if r.x[j]>.5}
    if not audit(actions,starts,initial,goals,capacities,H):raise RuntimeError('Independent plan audit')
    makespan=max((t+next(a.duration for a in actions if a.name==name) for name,t in starts.items()),default=0)
    return {'status':'optimal_within_horizon','starts':starts,'makespan':makespan,
            'cost':sum(a.cost for a in actions if a.name in starts)}


def exhaustive(actions,initial,goals,capacities,H):
    options=[[-1]+list(range(H-a.duration+1)) for a in actions]
    if np.prod([len(x) for x in options])>200000:raise ValueError('Enumeration budget')
    best=None
    for times in itertools.product(*options):
        starts={a.name:t for a,t in zip(actions,times) if t>=0}
        if audit(actions,starts,initial,goals,capacities,H):
            value=(max((t+a.duration for a,t in zip(actions,times) if t>=0),default=0),
                   sum(a.cost for a,t in zip(actions,times) if t>=0))
            best=value if best is None or value<best else best
    return best


def fixture(H=7):
    A=[Action('cut_A',frozenset(),frozenset({'A'}),2,'mill',1),
       Action('cut_B',frozenset(),frozenset({'B'}),2,'mill',1),
       Action('buy_A',frozenset(),frozenset({'A'}),3,'vendor',5),
       Action('assemble',frozenset({'A','B'}),frozenset({'done'}),1,'bench',1)]
    return A,set(),{'done'},{r:[1]*H for r in ('mill','vendor','bench')},H


def benchmark():
    A,I,G,C,H=fixture();normal=plan(A,I,G,C,H)
    C['vendor']=[0]*H;outage=plan(A,I,G,C,H)
    repaired=plan(A,I,G,C,H,fixed={'cut_A':0},earliest_new_start=1)
    return {'scope':'finite monotone/add-only planning; NOT a PDDLStream implementation',
            'normal':normal,'vendor_outage':outage,'replanning_with_committed_start':repaired}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='results.json')
    args=p.parse_args();Path(args.output).write_text(json.dumps(benchmark(),indent=2))
