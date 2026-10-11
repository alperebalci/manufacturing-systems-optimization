"""Case 05 — condition-based quality inspection/rework policy with exact policy evaluation."""
from __future__ import annotations
import itertools
import numpy as np
from .validation import make_audit, pct_improvement

STATES=("stable","drifting","out_of_control")
ACTIONS=("light","standard","intensive")


def model():
    P=np.array([[[.88,.10,.02],[.93,.06,.01],[.97,.025,.005]],[[.12,.70,.18],[.28,.63,.09],[.55,.40,.05]],[[.02,.18,.80],[.08,.37,.55],[.45,.45,.10]]])
    inspection=np.array([5.,13.,26.]); expected_escape=np.array([[3,1.5,.5],[18,8,3],[70,32,8]],float); rework=np.array([[2,3,5],[12,15,18],[24,28,35]],float)
    cost=inspection[None,:]+expected_escape+rework
    return P,cost


def evaluate_policy(policy,gamma=.96):
    P,c=model(); rows=np.arange(len(STATES)); Pp=P[rows,policy,:]; cp=c[rows,policy]; V=np.linalg.solve(np.eye(len(STATES))-gamma*Pp,cp); return V


def solve(gamma=.96)->dict:
    P,c=model();V=np.zeros(len(STATES))
    for _ in range(10000):
        q=c+gamma*np.einsum("sak,k->sa",P,V);nv=q.min(axis=1)
        if np.max(np.abs(nv-V))<1e-11: V=nv;break
        V=nv
    q=c+gamma*np.einsum("sak,k->sa",P,V);pol=q.argmin(axis=1); exact=evaluate_policy(pol,gamma); residual=float(np.max(np.abs(V-exact)))
    audit=make_audit({"policy_value_consistency":residual<1e-7},max_value_difference=residual)
    return {"value":exact,"policy":{s:ACTIONS[int(a)] for s,a in zip(STATES,pol)},"policy_indices":pol,"audit":audit}


def baseline(action="standard",gamma=.96):
    a=ACTIONS.index(action);pol=np.full(len(STATES),a,dtype=int);V=evaluate_policy(pol,gamma);return {"value":V,"policy":{s:action for s in STATES}}


def exhaustive_check(gamma=.96):
    best=None
    for pol in itertools.product(range(len(ACTIONS)),repeat=len(STATES)):
        V=evaluate_policy(np.array(pol),gamma); score=V[0]
        if best is None or score<best[0]:best=(score,pol,V)
    return best


def industrial_benchmark():
    o=solve();b=baseline();ex=exhaustive_check();return {"optimized_cost_from_stable":float(o["value"][0]),"standard_policy_cost":float(b["value"][0]),"improvement_pct":pct_improvement(float(b["value"][0]),float(o["value"][0])),"exhaustive_optimum_match":abs(o["value"][0]-ex[0])<1e-7,"audit_passed":o["audit"].passed,"policy":o["policy"]}


if __name__=="__main__": print(industrial_benchmark())
