"""Case 10 — cutting-stock planning with kerf, finite remnants, trim loss and overproduction penalty."""
from __future__ import annotations
from itertools import product
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from .validation import make_audit, pct_improvement


def patterns(length,item_lengths,kerf=4):
    maxc=[length//x for x in item_lengths];out=[]
    for counts in product(*[range(c+1) for c in maxc]):
        pieces=sum(counts);used=sum(c*l for c,l in zip(counts,item_lengths))+max(0,pieces-1)*kerf
        if 0<used<=length:out.append((counts,length-used))
    return out


def solve()->dict:
    items=np.array([180,260,310]);demand=np.array([8,6,5]);stocks=[(1000,1.0,"new",None),(620,.26,"remnant_620",2),(540,.22,"remnant_540",2)];allp=[]
    for L,c,lbl,av in stocks:
        for cnt,waste in patterns(L,items):allp.append((np.array(cnt),waste,c,lbl,av))
    n=len(allp);prod=np.column_stack([x[0] for x in allp]);cost=np.array([x[2]+.001*x[1] for x in allp]);over0=n;N=n+len(demand);c=np.r_[cost,np.full(len(demand),.12)];integ=np.r_[np.ones(n,int),np.zeros(len(demand),int)];lb=np.zeros(N);ub=np.full(N,np.inf);rows=[];lo=[];hi=[]
    for i in range(len(demand)):
        row=np.zeros(N);row[:n]=prod[i];row[over0+i]=-1;rows.append(row);lo.append(demand[i]);hi.append(demand[i])
    for lbl in("remnant_620","remnant_540"):
        row=np.zeros(N);av=0
        for k,x in enumerate(allp):
            if x[3]==lbl:row[k]=1;av=x[4]
        rows.append(row);lo.append(-np.inf);hi.append(av)
    res=milp(c=c,integrality=integ,bounds=Bounds(lb,ub),constraints=LinearConstraint(np.vstack(rows),np.array(lo),np.array(hi)))
    if not res.success:raise RuntimeError(res.message)
    x=np.rint(res.x[:n]).astype(int);used=np.where(x>0)[0];produced=prod@x;waste=sum(allp[k][1]*x[k] for k in used);plan=[{"stock":allp[k][3],"pattern":allp[k][0].tolist(),"waste":int(allp[k][1]),"count":int(x[k])} for k in used];audit=make_audit({"demand":bool(np.all(produced>=demand)),"remnant_620":sum(x[k] for k in used if allp[k][3]=="remnant_620")<=2,"remnant_540":sum(x[k] for k in used if allp[k][3]=="remnant_540")<=2},total_waste=float(waste))
    return {"plan":plan,"produced":produced,"demand":demand,"total_cost":float(res.fun),"total_waste":float(waste),"audit":audit}


def baseline()->dict:
    items=np.array([180,260,310]);demand=np.array([8,6,5]);remaining=demand.copy();bars=0;waste=0
    while np.any(remaining>0):
        cap=1000;used=0
        for i in np.argsort(-items):
            while remaining[i]>0 and used+items[i]+(4 if used else 0)<=cap:
                used+=items[i]+(4 if used else 0);remaining[i]-=1
        bars+=1;waste+=cap-used
    return {"total_cost":float(bars+.001*waste),"total_waste":float(waste)}


def industrial_benchmark():
    o=solve();b=baseline();return {"optimized_cost":o["total_cost"],"baseline_cost":b["total_cost"],"cost_improvement_pct":pct_improvement(b["total_cost"],o["total_cost"]),"optimized_waste":o["total_waste"],"baseline_waste":b["total_waste"],"audit_passed":o["audit"].passed}


if __name__=="__main__":print(industrial_benchmark())
