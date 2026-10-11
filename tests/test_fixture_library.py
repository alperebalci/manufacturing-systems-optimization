import json
import numpy as np
from pathlib import Path
from manufacturing_optimization import fixture_library as f


def test_catalog_has_two_fixtures_per_case():
    rows=f.catalog()
    assert len(rows)==20
    for i in range(1,11):
        case=f"case{i:02d}"
        scales={r["scale"] for r in rows if r["case_id"]==case}
        assert scales=={"validation","industrial"}


def test_deterministic_and_industrial_is_larger():
    for i in range(1,11):
        small,large=f.fixture_pair(i)
        small2,large2=f.fixture_pair(i)
        assert small.fingerprint()==small2.fingerprint()
        assert large.fingerprint()==large2.fingerprint()
        assert sum(large.dimensions.values())>sum(small.dimensions.values())
        assert small.source==large.source=="synthetic"


def test_probability_contracts():
    small,large=f.fixture_pair(5)
    for fx in (small,large):
        P=np.asarray(fx.payload["transition"])
        assert np.all(P>=0)
        assert np.allclose(P.sum(axis=2),1.0)


def test_eligibility_contracts():
    for case in (3,7,9):
        _,fx=f.fixture_pair(case)
        e=np.asarray(fx.payload["eligible"])
        assert np.all(e.sum(axis=1)>=1)


def test_storage_and_skill_contracts():
    _,milk=f.fixture_pair(2)
    assert np.all(milk.payload["storage_capacity"]>=milk.payload["safety_stock"])
    _,workers=f.fixture_pair(4)
    assert np.all(np.asarray(workers.payload["skill"]).sum(axis=0)>=4)


def test_materialize_round_trip(tmp_path: Path):
    paths=f.materialize(tmp_path)
    assert len(paths)==20
    manifest=json.loads((tmp_path/"manifest.json").read_text())
    assert len(manifest)==20
    sample=json.loads((tmp_path/"case01"/"industrial.json").read_text())
    assert sample["dimensions"]=={"jobs":500,"machines":20}
    assert len(sample["fingerprint"])==64
