"""Case 09 — energy-aware single-machine scheduling with TOU price, peak demand and maintenance blackout."""
from __future__ import annotations
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from .validation import make_audit, pct_improvement


def data():
    p=np.array([3,2,4,2,3],int);power=np.array([5.,7.,4.,6.,5.5]);due=np.array([5,7,10,12,13],float);weight=np.array([2,1,3,2,2],float);tariff=np.array([.12,.11,.10,.32,.35,.30,.16,.14,.13,.12,.11,.10,.09,.10,.12,.15]);blackout={8};return p,power,due,weight,tariff,blackout


def solve()->dict:
    p,power,due,w,tariff,blackout=data();H=len(tariff);J=len(p);starts=[[s for s in range(H-p[j]+1) if not any(tt in blackout for tt in range(s,s+p[j]))] for j in range(J)];off=[];cur=0
    for ss in starts:off.append(cur);cur+=len(ss)
    tard0=cur;peak=tard0+J;n=peak+1;c=np.zeros(n)
    for j in range(J):
        for k,s in enumerate(starts[j]):c[off[j]+k]=power[j]*tariff[s:s+p[j]].sum()
    c[tard0:tard0+J]=9*w;c[peak]=1.4
    integ=np.zeros(n,dtype=int);integ[:tard0]=1;lb=np.zeros(n);ub=np.full(n,np.inf);ub[:tard0]=1;rows=[];lo=[];hi=[]
    for j in range(J):row=np.zeros(n);row[off[j]:off[j]+len(starts[j])]=1;rows.append(row);lo.append(1);hi.append(1)
    for tt in range(H):
        occ=np.zeros(n);pr=np.zeros(n)
        for j in range(J):
            for k,s in enumerate(starts[j]):
                if s<=tt<s+p[j]:occ[off[j]+k]=1;pr[off[j]+k]=power[j]
        rows.append(occ);lo.append(-np.inf);hi.append(1);pr[peak]=-1;rows.append(pr);lo.append(-np.inf);hi.append(0)
    for j in range(J):
        row=np.zeros(n)
        for k,s in enumerate(starts[j]):row[off[j]+k]=s+p[j]
        row[tard0+j]=-1;rows.append(row);lo.append(-np.inf);hi.append(due[j])
    res=milp(c=c,integrality=integ,bounds=Bounds(lb,ub),constraints=LinearConstraint(np.vstack(rows),np.array(lo),np.array(hi)))
    if not res.success:raise RuntimeError(res.message)
    chosen=[]
    for j in range(J):vals=res.x[off[j]:off[j]+len(starts[j])];chosen.append(starts[j][int(np.argmax(vals))])
    audit=validate(np.array(chosen),p,blackout);return {"start_times":np.array(chosen),"tardiness":res.x[tard0:tard0+J],"weighted_tardiness":float(w@res.x[tard0:tard0+J]),"peak_power":float(res.x[peak]),"total_cost":float(res.fun),"audit":audit}


def baseline()->dict:
    p,power,due,w,tariff,blackout=data();order=np.argsort(due);clock=0;starts=np.zeros(len(p),int)
    for j in order:
        while any(tt in blackout for tt in range(clock,clock+p[j])):clock+=1
        starts[j]=clock;clock+=p[j]
    tard=np.maximum(0,starts+p-due);energy=sum(power[j]*tariff[starts[j]:starts[j]+p[j]].sum() for j in range(len(p)));return {"start_times":starts,"weighted_tardiness":float(w@tard),"total_cost":float(energy+9*(w@tard)+1.4*power.max())}


def validate(starts,p,blackout):
    occupied=[]
    for j,s in enumerate(starts):occupied.extend((tt,j) for tt in range(int(s),int(s+p[j])))
    times=[x[0] for x in occupied];checks={"no_overlap":len(times)==len(set(times)),"blackout_respected":all(tt not in blackout for tt in times)};return make_audit(checks,scheduled_hours=len(times))


def industrial_benchmark():
    o=solve();b=baseline();return {"optimized_cost":o["total_cost"],"baseline_cost":b["total_cost"],"cost_improvement_pct":pct_improvement(b["total_cost"],o["total_cost"]),"weighted_tardiness":o["weighted_tardiness"],"peak_power":o["peak_power"],"audit_passed":o["audit"].passed}


if __name__=="__main__":print(industrial_benchmark())
