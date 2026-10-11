"""Case 08 — CONWIP simulation optimization under stochastic processing and breakdowns."""
from __future__ import annotations
from dataclasses import dataclass
import heapq
import numpy as np
from .validation import pct_improvement


@dataclass(frozen=True)
class Replication:
    throughput:float
    mean_cycle_time:float
    mean_wip:float
    downtime_fraction:float


def simulate(wip_cap:int,seed:int,horizon=720.,warmup=120.)->Replication:
    rng=np.random.default_rng(seed);means=np.array([5.,7.,4.]);mtbf=np.array([150.,110.,180.]);mttr=np.array([8.,12.,7.]);machine_free=np.zeros(3);queues=[[],[],[]];events=[];released=completed=in_system=0;entry={};cycles=[];area=down=0.;last=0.
    def release(now):
        nonlocal released,in_system
        while in_system<wip_cap: entry[released]=now;queues[0].append(released);released+=1;in_system+=1
    def start(st,now):
        if machine_free[st]<=now+1e-12 and queues[st]:
            job=queues[st].pop(0);p=rng.lognormal(np.log(means[st])-.5*.22**2,.22);repair=0.
            if rng.random()<1-np.exp(-p/mtbf[st]):repair=rng.exponential(mttr[st])
            finish=now+p+repair;machine_free[st]=finish;heapq.heappush(events,(finish,st,job,repair))
    release(0);start(0,0)
    while events:
        now,st,job,repair=heapq.heappop(events)
        if now>horizon:break
        if now>warmup:
            left=max(last,warmup);area+=in_system*(now-left);down+=repair
        last=now
        if st<2:queues[st+1].append(job)
        else:
            completed+=int(now>=warmup);in_system-=1
            if entry[job]>=warmup:cycles.append(now-entry[job])
            entry.pop(job,None);release(now)
        start(st,now)
        if st<2:start(st+1,now)
        start(0,now)
    measure=horizon-warmup
    return Replication(completed/measure,float(np.mean(cycles)) if cycles else np.inf,area/measure,down/(measure*3))


def evaluate_cap(cap,seeds=range(20)):
    reps=[simulate(cap,s) for s in seeds];tp=np.array([r.throughput for r in reps]);ct=np.array([r.mean_cycle_time for r in reps]);w=np.array([r.mean_wip for r in reps]);dt=np.array([r.downtime_fraction for r in reps]);score=ct.mean()+120*max(0,.115-tp.mean())+.35*w.mean();return {"wip_cap":cap,"throughput":float(tp.mean()),"cycle_time":float(ct.mean()),"mean_wip":float(w.mean()),"downtime_fraction":float(dt.mean()),"throughput_se":float(tp.std(ddof=1)/np.sqrt(len(tp))),"score":float(score)}


def solve(caps=range(2,13),seeds=range(20))->dict:
    rows=[evaluate_cap(c,seeds) for c in caps];best=min(rows,key=lambda x:x["score"]);return {**best,"frontier":rows}


def baseline(seeds=range(20))->dict:
    return evaluate_cap(10,seeds)


def industrial_benchmark():
    o=solve();b=baseline();return {"selected_wip_cap":o["wip_cap"],"optimized_score":o["score"],"baseline_score":b["score"],"score_improvement_pct":pct_improvement(b["score"],o["score"]),"throughput":o["throughput"],"cycle_time":o["cycle_time"],"throughput_se":o["throughput_se"]}


if __name__=="__main__":print(industrial_benchmark())
