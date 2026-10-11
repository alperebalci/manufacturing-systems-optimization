"""Case 04 — skill-feasible ergonomic worker rotation with cumulative exposure fairness."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from .validation import make_audit, pct_improvement


@dataclass(frozen=True)
class Instance:
    skill: np.ndarray
    ergonomic_risk: np.ndarray
    fatigue_multiplier: np.ndarray
    exposure_cap: np.ndarray
    periods:int=5


def demo_instance()->Instance:
    return Instance(skill=np.array([[1,1,0],[1,1,1],[0,1,1],[1,0,1]],int),ergonomic_risk=np.array([5.,8.,4.]),fatigue_multiplier=np.array([1.,1.08,1.16,1.25,1.35]),exposure_cap=np.array([32.,35.,34.,33.]),periods=5)


def solve(instance=None)->dict:
    ins=instance or demo_instance(); w,s=ins.skill.shape; p=ins.periods; nx=w*s*p; z=nx; n=nx+1
    c=np.zeros(n); c[z]=1; integ=np.zeros(n,dtype=int); integ[:nx]=1; lb=np.zeros(n); ub=np.ones(n); ub[z]=np.inf
    ix=lambda ww,ss,pp: pp*w*s+ww*s+ss
    rows=[]; lo=[]; hi=[]
    for pp in range(p):
        for ss in range(s):
            row=np.zeros(n); [row.__setitem__(ix(ww,ss,pp),1) for ww in range(w)]; rows.append(row);lo.append(1);hi.append(1)
        for ww in range(w):
            row=np.zeros(n); [row.__setitem__(ix(ww,ss,pp),1) for ss in range(s)]; rows.append(row);lo.append(-np.inf);hi.append(1)
    for pp in range(p):
        for ww in range(w):
            for ss in range(s):
                if not ins.skill[ww,ss]:
                    row=np.zeros(n);row[ix(ww,ss,pp)]=1;rows.append(row);lo.append(0);hi.append(0)
    for ww in range(w):
        row=np.zeros(n)
        for pp in range(p):
            for ss in range(s): row[ix(ww,ss,pp)]=ins.ergonomic_risk[ss]*ins.fatigue_multiplier[pp]
        row[z]=-1; rows.append(row);lo.append(-np.inf);hi.append(0)
        row2=row.copy(); row2[z]=0; rows.append(row2);lo.append(-np.inf);hi.append(ins.exposure_cap[ww])
    high=int(np.argmax(ins.ergonomic_risk))
    for ww in range(w):
        for pp in range(p-1):
            row=np.zeros(n); row[ix(ww,high,pp)]=1;row[ix(ww,high,pp+1)]=1;rows.append(row);lo.append(-np.inf);hi.append(1)
    res=milp(c=c,integrality=integ,bounds=Bounds(lb,ub),constraints=LinearConstraint(np.vstack(rows),np.array(lo),np.array(hi)))
    if not res.success: raise RuntimeError(res.message)
    sch=np.rint(res.x[:nx]).astype(int).reshape(p,w,s); risk=np.array([sum(ins.ergonomic_risk[ss]*ins.fatigue_multiplier[pp]*sch[pp,ww,ss] for pp in range(p) for ss in range(s)) for ww in range(w)])
    audit=validate(ins,sch,risk)
    return {"schedule":sch,"worker_risk":risk,"max_risk":float(risk.max()),"risk_std":float(risk.std()),"audit":audit}


def baseline(instance=None)->dict:
    ins=instance or demo_instance(); w,s=ins.skill.shape; sch=np.zeros((ins.periods,w,s),int); last=np.full(w,-1); risk=np.zeros(w)
    for pp in range(ins.periods):
        used=set()
        for ss in np.argsort(-ins.ergonomic_risk):
            cand=[ww for ww in range(w) if ww not in used and ins.skill[ww,ss] and not(last[ww]==ss==int(np.argmax(ins.ergonomic_risk)))]
            ww=min(cand,key=lambda q:risk[q]); sch[pp,ww,ss]=1;used.add(ww);last[ww]=ss;risk[ww]+=ins.ergonomic_risk[ss]*ins.fatigue_multiplier[pp]
    return {"max_risk":float(risk.max()),"risk_std":float(risk.std())}


def validate(ins,sch,risk):
    high=int(np.argmax(ins.ergonomic_risk)); checks={"station_coverage":bool(np.all(sch.sum(axis=1)==1)),"one_station_per_worker":bool(np.all(sch.sum(axis=2)<=1)),"skills":bool(all(not sch[pp,ww,ss] or ins.skill[ww,ss] for pp in range(ins.periods) for ww in range(ins.skill.shape[0]) for ss in range(ins.skill.shape[1]))),"exposure_cap":bool(np.all(risk<=ins.exposure_cap+1e-7)),"high_risk_rotation":bool(all(sch[pp,ww,high]+sch[pp+1,ww,high]<=1 for pp in range(ins.periods-1) for ww in range(ins.skill.shape[0])))}
    return make_audit(checks,max_exposure=float(risk.max()))


def industrial_benchmark(instance=None):
    ins=instance or demo_instance();o=solve(ins);b=baseline(ins)
    return {"optimized_max_risk":o["max_risk"],"baseline_max_risk":b["max_risk"],"max_risk_improvement_pct":pct_improvement(b["max_risk"],o["max_risk"]),"optimized_risk_std":o["risk_std"],"baseline_risk_std":b["risk_std"],"audit_passed":o["audit"].passed}


if __name__=="__main__": print(industrial_benchmark())
