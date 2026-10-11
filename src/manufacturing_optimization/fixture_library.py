from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import argparse, json, hashlib
import numpy as np

@dataclass(frozen=True)
class FixtureBundle:
    case_id: str
    scale: str
    seed: int
    payload: dict[str, Any]
    dimensions: dict[str, int]
    units: dict[str, str]
    solver_mode: str
    source: str = "synthetic"
    schema_version: str = "1.0"

    def fingerprint(self) -> str:
        blob = json.dumps(_jsonable(self.payload), sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(blob).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "scale": self.scale,
            "seed": self.seed,
            "schema_version": self.schema_version,
            "source": self.source,
            "solver_mode": self.solver_mode,
            "dimensions": self.dimensions,
            "units": self.units,
            "fingerprint": self.fingerprint(),
            "payload": _jsonable(self.payload),
        }


def _jsonable(x: Any) -> Any:
    if isinstance(x, np.ndarray): return x.tolist()
    if isinstance(x, np.generic): return x.item()
    if isinstance(x, dict): return {k: _jsonable(v) for k,v in x.items()}
    if isinstance(x, (list,tuple)): return [_jsonable(v) for v in x]
    return x


def _rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def case01_validation_fixture(seed: int = 101) -> FixtureBundle:
    p=np.array([[4,5.2],[3.1,4.4],[5.8,4.1],[2.7,3.2],[4.6,3.6],[3.4,4.2],[4.1,3.9],[2.9,3.5]],float)
    v=np.array([[96,111],[74,91],[139,112],[67,73],[110,92],[83,101],[103,95],[70,82]],float)
    risk=np.array([[38,24],[32,22],[62,35],[26,20],[55,31],[41,26],[49,29],[30,21]],float)
    payload={"processing_hours":p,"variable_cost":v,"failure_risk_cost":risk,"maintenance_duration":np.array([1,.75]),"maintenance_cost":np.array([60,55]),"regular_capacity":np.array([14,14]),"overtime_cost":np.array([48,44]),"pm_risk_reduction":.72,"max_overtime":6.0}
    return FixtureBundle("case01","validation",seed,payload,{"jobs":8,"machines":2},{"processing_hours":"h","cost":"currency"},"exact_milp")


def case01_industrial_fixture(seed: int = 1001) -> FixtureBundle:
    g=_rng(seed); J,M=500,20
    base=g.uniform(1.5,7.5,(J,1)); eff=g.uniform(.75,1.35,(1,M)); p=np.round(base*eff*g.lognormal(0,.08,(J,M)),2)
    variable=np.round(22*p+g.uniform(15,70,(J,M)),2); risk=np.round(g.gamma(2.2,16,(J,M))*(.8+eff),2)
    cap=np.full(M,8*5*4.0)
    payload={"processing_hours":p,"variable_cost":variable,"failure_risk_cost":risk,"maintenance_duration":np.round(g.uniform(3,8,M),2),"maintenance_cost":np.round(g.uniform(350,950,M),2),"regular_capacity":cap,"overtime_cost":np.round(g.uniform(55,95,M),2),"pm_risk_reduction":.72,"max_overtime":40.0}
    return FixtureBundle("case01","industrial",seed,payload,{"jobs":J,"machines":M},{"processing_hours":"h","cost":"currency"},"sparse_milp")


def case02_validation_fixture(seed:int=102)->FixtureBundle:
    demand=np.array([[8,10,7,11,9,10],[6,9,8,7,10,8],[5,6,9,8,7,9]],float)
    payload={"demand":demand,"initial_inventory":np.array([12,10,9],float),"storage_capacity":np.array([24,21,20],float),"safety_stock":np.array([3,2,2],float),"vehicle_capacity":34.,"trip_cost":58.,"holding_cost":.7,"emergency_cost":28.,"max_trips_per_period":2}
    return FixtureBundle("case02","validation",seed,payload,{"stations":3,"periods":6},{"demand":"containers/period","inventory":"containers"},"exact_milp")


def case02_industrial_fixture(seed:int=1002)->FixtureBundle:
    g=_rng(seed);S,T=40,96
    base=g.uniform(4,18,(S,1)); profile=1+.25*np.sin(np.linspace(0,8*np.pi,T))[None,:]; demand=np.maximum(0,np.rint(base*profile*g.lognormal(0,.15,(S,T))))
    storage=np.maximum(20,np.ceil(demand.max(1)*3)); safety=np.maximum(2,np.ceil(demand.mean(1)*.45)); init=np.minimum(storage,np.ceil(safety+demand[:,0]*.8))
    payload={"demand":demand,"initial_inventory":init,"storage_capacity":storage,"safety_stock":safety,"vehicle_capacity":260.,"trip_cost":185.,"holding_cost":.35,"emergency_cost":95.,"max_trips_per_period":4}
    return FixtureBundle("case02","industrial",seed,payload,{"stations":S,"periods":T},{"demand":"containers/period","inventory":"containers"},"sparse_milp")


def case03_validation_fixture(seed:int=103)->FixtureBundle:
    payload={"task_time":np.array([8,6,10,7,5,9,4,6],float),"task_energy":np.array([7,5,9,6,4,8,3,5],float),"due_time":np.array([14,16,22,18,15,25,12,20],float),"priority":np.array([2,1,3,2,1,3,2,2],float),"battery":np.array([29,30,27],float),"reserve":np.array([4,4,3],float),"speed_factor":np.array([1.,1.08,.94]),"eligible":np.array([[1,1,0],[1,1,1],[1,0,1],[1,1,1],[0,1,1],[1,1,1],[1,1,1],[1,0,1]],int)}
    return FixtureBundle("case03","validation",seed,payload,{"tasks":8,"vehicles":3},{"task_time":"min","task_energy":"kWh"},"exact_enumeration")


def case03_industrial_fixture(seed:int=1003)->FixtureBundle:
    g=_rng(seed);N,V=250,20
    tt=np.round(g.lognormal(np.log(12),.45,N),2); en=np.round(.45*tt+g.uniform(1,5,N),2); eligible=(g.random((N,V))<.72).astype(int)
    for i in range(N):
        if not eligible[i].any(): eligible[i,g.integers(V)]=1
    payload={"task_time":tt,"task_energy":en,"due_time":np.round(np.cumsum(np.sort(tt))/V*1.35+g.uniform(20,90,N),2),"priority":g.integers(1,5,N).astype(float),"battery":g.uniform(180,240,V).round(2),"reserve":g.uniform(25,40,V).round(2),"speed_factor":g.uniform(.85,1.18,V).round(3),"eligible":eligible}
    return FixtureBundle("case03","industrial",seed,payload,{"tasks":N,"vehicles":V},{"task_time":"min","task_energy":"kWh"},"assignment_milp_plus_dispatch")


def case04_validation_fixture(seed:int=104)->FixtureBundle:
    payload={"skill":np.array([[1,1,0],[1,1,1],[0,1,1],[1,0,1]],int),"ergonomic_risk":np.array([5.,8.,4.]),"fatigue_multiplier":np.array([1.,1.08,1.16,1.25,1.35]),"exposure_cap":np.array([32.,35.,34.,33.]),"periods":5}
    return FixtureBundle("case04","validation",seed,payload,{"workers":4,"stations":3,"periods":5},{"ergonomic_risk":"score"},"exact_milp")


def case04_industrial_fixture(seed:int=1004)->FixtureBundle:
    g=_rng(seed);W,S,P=120,36,8; skill=(g.random((W,S))<.58).astype(int)
    for s in range(S):
        if skill[:,s].sum()<4: skill[g.choice(W,4,replace=False),s]=1
    risk=g.uniform(2.5,9.5,S).round(2); fatigue=np.linspace(1,1.5,P).round(3); cap=np.full(W,52.)+g.uniform(-5,8,W)
    payload={"skill":skill,"ergonomic_risk":risk,"fatigue_multiplier":fatigue,"exposure_cap":cap.round(2),"periods":P}
    return FixtureBundle("case04","industrial",seed,payload,{"workers":W,"stations":S,"periods":P},{"ergonomic_risk":"score"},"sparse_milp")


def case05_validation_fixture(seed:int=105)->FixtureBundle:
    P=np.array([[[.88,.10,.02],[.93,.06,.01],[.97,.025,.005]],[[.12,.70,.18],[.28,.63,.09],[.55,.40,.05]],[[.02,.18,.80],[.08,.37,.55],[.45,.45,.10]]])
    c=np.array([[10,17.5,31.5],[35,36,47],[99,73,69]],float)
    payload={"transition":P,"cost":c,"states":["stable","drifting","out_of_control"],"actions":["light","standard","intensive"],"discount":.96}
    return FixtureBundle("case05","validation",seed,payload,{"states":3,"actions":3},{"cost":"currency/review"},"value_iteration_plus_exhaustive_oracle")


def case05_industrial_fixture(seed:int=1005)->FixtureBundle:
    g=_rng(seed);S,A=12,4; P=np.zeros((S,A,S))
    for s in range(S):
        for a in range(A):
            center=max(0,s-a); weights=np.exp(-.5*((np.arange(S)-center)/(1.1+.15*s))**2); weights+=.02; P[s,a]=weights/weights.sum()
    state_cost=np.linspace(0,420,S)[:,None]; action_cost=np.array([4,14,38,95])[None,:]; escape=(np.linspace(3,180,S)[:,None]/(1+np.arange(A)[None,:]*1.3)); cost=state_cost*.22+action_cost+escape
    payload={"transition":P,"cost":cost.round(3),"states":[f"condition_{i:02d}" for i in range(S)],"actions":["light","standard","intensive","containment"],"discount":.985}
    return FixtureBundle("case05","industrial",seed,payload,{"states":S,"actions":A},{"cost":"currency/review"},"value_or_policy_iteration")


def case06_validation_fixture(seed:int=106)->FixtureBundle:
    payload={"volume":np.array([9000.]),"roughness_limit":np.array([2.4]),"min_tool_life":np.array([14.]),"max_power":np.array([7.2]),"hardness_factor":np.array([1.])}
    return FixtureBundle("case06","validation",seed,payload,{"operations":1},{"volume":"mm3","power":"kW"},"global_nlp")


def case06_industrial_fixture(seed:int=1006)->FixtureBundle:
    g=_rng(seed);N=1000
    payload={"volume":g.uniform(3500,25000,N).round(2),"roughness_limit":g.choice([1.6,2.4,3.2],N,p=[.2,.55,.25]),"min_tool_life":g.uniform(10,28,N).round(2),"max_power":g.uniform(5.5,11,N).round(2),"hardness_factor":g.uniform(.8,1.4,N).round(3),"material_family":g.choice(["Al","mild_steel","alloy_steel","stainless"],N)}
    return FixtureBundle("case06","industrial",seed,payload,{"operations":N},{"volume":"mm3","power":"kW"},"batched_nlp_or_surrogate")


def case07_validation_fixture(seed:int=107)->FixtureBundle:
    payload={"duration":np.array([[4,5],[3,4],[6,5],[99,3],[5,6],[2,3]],float),"mold":np.array([0,0,1,2,1,2]),"eligible":np.array([[1,1],[1,1],[1,1],[0,1],[1,1],[1,1]],int),"due":np.array([8,11,13,9,17,15],float),"weight":np.array([2,1,3,2,2,1],float)}
    return FixtureBundle("case07","validation",seed,payload,{"jobs":6,"presses":2,"molds":3},{"duration":"h"},"exact_assignment_and_permutation")


def case07_industrial_fixture(seed:int=1007)->FixtureBundle:
    g=_rng(seed);J,M,K=180,12,8; eligible=(g.random((J,M))<.55).astype(int)
    for j in range(J):
        if not eligible[j].any(): eligible[j,g.integers(M)]=1
    base=g.uniform(.5,5,J)[:,None]; eff=g.uniform(.75,1.35,M)[None,:]; dur=(base*eff*g.lognormal(0,.12,(J,M))).round(2); dur[eligible==0]=1e6
    setup=g.uniform(.2,2.8,(K,K));np.fill_diagonal(setup,.15)
    payload={"duration":dur,"mold":g.integers(0,K,J),"eligible":eligible,"due":np.sort(g.uniform(8,160,J)).round(2),"weight":g.integers(1,5,J).astype(float),"setup_matrix":setup.round(2)}
    return FixtureBundle("case07","industrial",seed,payload,{"jobs":J,"presses":M,"molds":K},{"duration":"h"},"cp_sat_or_lns")


def case08_validation_fixture(seed:int=108)->FixtureBundle:
    payload={"mean_processing":np.array([5.,7.,4.]),"mtbf":np.array([150.,110.,180.]),"mttr":np.array([8.,12.,7.]),"buffer_capacity":np.array([6,6]),"horizon":720.,"warmup":120.,"candidate_wip_caps":np.arange(2,13)}
    return FixtureBundle("case08","validation",seed,payload,{"stations":3,"replications":20},{"time":"min"},"discrete_event_simulation")


def case08_industrial_fixture(seed:int=1008)->FixtureBundle:
    g=_rng(seed);S=12
    payload={"mean_processing":g.uniform(2.5,9,S).round(2),"cv_processing":g.uniform(.12,.45,S).round(3),"mtbf":g.uniform(90,420,S).round(2),"mttr":g.uniform(5,35,S).round(2),"buffer_capacity":g.integers(4,25,S-1),"horizon":60*24*30.,"warmup":60*24*3.,"candidate_wip_caps":np.arange(8,81,4),"replications":50}
    return FixtureBundle("case08","industrial",seed,payload,{"stations":S,"replications":50},{"time":"min"},"simulation_optimization_crn")


def case09_validation_fixture(seed:int=109)->FixtureBundle:
    payload={"processing":np.array([3,2,4,2,3]),"power":np.array([5.,7.,4.,6.,5.5]),"due":np.array([5,7,10,12,13],float),"weight":np.array([2,1,3,2,2],float),"tariff":np.array([.12,.11,.10,.32,.35,.30,.16,.14,.13,.12,.11,.10,.09,.10,.12,.15]),"blackout":np.array([8])}
    return FixtureBundle("case09","validation",seed,payload,{"jobs":5,"periods":16,"machines":1},{"power":"kW","tariff":"currency/kWh"},"time_indexed_milp")


def case09_industrial_fixture(seed:int=1009)->FixtureBundle:
    g=_rng(seed);J,M,T=120,4,168; p=g.integers(1,9,(J,M)); eligible=(g.random((J,M))<.75).astype(int)
    for j in range(J):
        if not eligible[j].any():eligible[j,g.integers(M)]=1
    p=np.where(eligible,p,999); power=g.uniform(3,28,(J,M)).round(2); due=np.sort(g.uniform(12,T-4,J)).round(1); w=g.integers(1,6,J).astype(float)
    hour=np.arange(T)%24; tariff=np.where((hour>=17)&(hour<=21),.34,np.where((hour>=8)&(hour<=16),.18,.09)); blackout={m:np.array(sorted(g.choice(T,6,replace=False))) for m in range(M)}
    payload={"processing":p,"eligible":eligible,"power":power,"due":due,"weight":w,"tariff":tariff,"blackout":blackout}
    return FixtureBundle("case09","industrial",seed,payload,{"jobs":J,"periods":T,"machines":M},{"power":"kW","tariff":"currency/kWh"},"rolling_horizon_milp_or_cp_sat")


def case10_validation_fixture(seed:int=110)->FixtureBundle:
    payload={"item_lengths":np.array([180,260,310]),"demand":np.array([8,6,5]),"stock_lengths":np.array([1000,620,540]),"stock_cost":np.array([1.,.26,.22]),"availability":np.array([-1,2,2]),"kerf":4}
    return FixtureBundle("case10","validation",seed,payload,{"item_types":3,"stock_types":3},{"length":"mm"},"exact_pattern_milp")


def case10_industrial_fixture(seed:int=1010)->FixtureBundle:
    g=_rng(seed);I,S=30,6; items=np.sort(g.integers(80,780,I)); stock=np.array([6000,7500,9000,10500,12000,13500]); demand=g.integers(20,180,I); costs=np.round(stock/stock.max()*1.2,3); availability=np.array([-1,-1,50,35,25,20])
    payload={"item_lengths":items,"demand":demand,"stock_lengths":stock,"stock_cost":costs,"availability":availability,"kerf":4}
    return FixtureBundle("case10","industrial",seed,payload,{"item_types":I,"stock_types":S},{"length":"mm"},"column_generation_or_restricted_pattern_milp")

VALIDATION_BUILDERS=[case01_validation_fixture,case02_validation_fixture,case03_validation_fixture,case04_validation_fixture,case05_validation_fixture,case06_validation_fixture,case07_validation_fixture,case08_validation_fixture,case09_validation_fixture,case10_validation_fixture]
INDUSTRIAL_BUILDERS=[case01_industrial_fixture,case02_industrial_fixture,case03_industrial_fixture,case04_industrial_fixture,case05_industrial_fixture,case06_industrial_fixture,case07_industrial_fixture,case08_industrial_fixture,case09_industrial_fixture,case10_industrial_fixture]


def fixture_pair(case_number:int, seed_offset:int=0)->tuple[FixtureBundle,FixtureBundle]:
    if not 1<=case_number<=10: raise ValueError("case_number must be 1..10")
    return VALIDATION_BUILDERS[case_number-1](), INDUSTRIAL_BUILDERS[case_number-1](1000+case_number+seed_offset)


def catalog()->list[dict[str,Any]]:
    out=[]
    for i in range(1,11):
        s,l=fixture_pair(i)
        out.extend([{"case_id":x.case_id,"scale":x.scale,"seed":x.seed,"dimensions":x.dimensions,"solver_mode":x.solver_mode,"fingerprint":x.fingerprint()} for x in (s,l)])
    return out


def materialize(root:str|Path)->list[Path]:
    root=Path(root); paths=[]
    for i in range(1,11):
        for fx in fixture_pair(i):
            path=root/fx.case_id/f"{fx.scale}.json";path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(fx.to_dict(),indent=2));paths.append(path)
    (root/"manifest.json").write_text(json.dumps(catalog(),indent=2));return paths


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--materialize",type=str);args=ap.parse_args()
    if args.materialize:
        print(f"materialized {len(materialize(args.materialize))} fixture files")
    else:
        for row in catalog():print(row)

if __name__=="__main__":main()
