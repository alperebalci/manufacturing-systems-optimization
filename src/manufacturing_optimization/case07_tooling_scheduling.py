"""Case 07 — mold/tool constrained parallel-press scheduling with sequence setups and tardiness."""
from __future__ import annotations
from dataclasses import dataclass
from itertools import permutations, product
import numpy as np
from .validation import make_audit, pct_improvement


@dataclass(frozen=True)
class Job:
    duration: tuple[float,float]
    mold:str
    compatible:tuple[int,...]
    due:float
    weight:float


def demo_jobs():
    return [Job((4,5),"A",(0,1),8,2),Job((3,4),"A",(0,1),11,1),Job((6,5),"B",(0,1),13,3),Job((4,3),"C",(1,),9,2),Job((5,6),"B",(0,1),17,2),Job((2,3),"C",(0,1),15,1)]


def setup_time(prev,curr):
    if prev is None:return 0.0
    if prev==curr:return .3
    return {("A","B"):1.8,("B","A"):2.2,("A","C"):1.5,("C","A"):1.6,("B","C"):2.0,("C","B"):2.1}.get((prev,curr),1.8)


def evaluate(jobs,seq,machine):
    clock=0.; tard=0.; setups=0.; prev=None; detail=[]
    for j in seq:
        st=setup_time(prev,jobs[j].mold);setups+=st;clock+=st;start=clock;clock+=jobs[j].duration[machine];tard+=jobs[j].weight*max(0,clock-jobs[j].due);detail.append((j,start,clock,st));prev=jobs[j].mold
    return clock,tard,setups,detail


def solve(jobs=None)->dict:
    jobs=jobs or demo_jobs();choices=[j.compatible for j in jobs];best=None
    for a in product(*choices):
        groups=[[j for j,v in enumerate(a) if v==m] for m in(0,1)]
        for s0 in permutations(groups[0]) if groups[0] else [()]:
            e0,t0,u0,d0=evaluate(jobs,s0,0)
            for s1 in permutations(groups[1]) if groups[1] else [()]:
                e1,t1,u1,d1=evaluate(jobs,s1,1);score=7*(t0+t1)+max(e0,e1)+.6*(u0+u1)
                if best is None or score<best[0]:best=(score,s0,s1,e0,e1,t0+t1,u0+u1,d0+d1)
    score,s0,s1,e0,e1,tard,setups,detail=best;audit=validate(jobs,s0,s1)
    return {"press_0":s0,"press_1":s1,"makespan":float(max(e0,e1)),"weighted_tardiness":float(tard),"setup_hours":float(setups),"objective":float(score),"schedule":detail,"audit":audit}


def baseline(jobs=None)->dict:
    jobs=jobs or demo_jobs();groups=[[],[]]
    for j in sorted(range(len(jobs)),key=lambda k:jobs[k].due):
        m=min(jobs[j].compatible,key=lambda mm:sum(jobs[k].duration[mm] for k in groups[mm]));groups[m].append(j)
    e0,t0,u0,_=evaluate(jobs,groups[0],0);e1,t1,u1,_=evaluate(jobs,groups[1],1);score=7*(t0+t1)+max(e0,e1)+.6*(u0+u1);return {"objective":float(score),"weighted_tardiness":float(t0+t1),"makespan":float(max(e0,e1))}


def validate(jobs,s0,s1):
    allj=list(s0)+list(s1);checks={"all_jobs_once":sorted(allj)==list(range(len(jobs))),"compatibility":all(0 in jobs[j].compatible for j in s0) and all(1 in jobs[j].compatible for j in s1)};return make_audit(checks,scheduled_jobs=len(allj))


def industrial_benchmark(jobs=None):
    jobs=jobs or demo_jobs();o=solve(jobs);b=baseline(jobs);return {"optimized_objective":o["objective"],"baseline_objective":b["objective"],"improvement_pct":pct_improvement(b["objective"],o["objective"]),"weighted_tardiness":o["weighted_tardiness"],"setup_hours":o["setup_hours"],"audit_passed":o["audit"].passed}


if __name__=="__main__":print(industrial_benchmark())
