import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import store

@pytest.fixture
def api(tmp_path,monkeypatch):
    monkeypatch.setenv("AX_DB_PATH",str(tmp_path/"quality.sqlite3"))
    monkeypatch.setenv("AX_SME_TOKEN","test-sme")
    store.init()
    store.put_run("run-1","external-1",{"test_id":"example"},"T3","review","needs SME")
    return TestClient(app),{"X-AX-SME-Token":"test-sme"}

def test_evidence_requires_reference_and_records_audit(api):
    client,headers=api
    payload={"run_id":"run-1","evidence":{"test":"ok"}}
    assert client.post("/api/v1/quality/evidence/verify",json=payload).status_code==403
    first=client.post("/api/v1/quality/evidence/verify",json=payload,headers=headers)
    assert first.status_code==200,first.text
    assert first.json()["verified"] is False
    payload["expected_sha256"]=first.json()["sha256"]
    verified=client.post("/api/v1/quality/evidence/verify",json=payload,headers=headers)
    assert verified.status_code==200 and verified.json()["verified"] is True
    payload["evidence"]["test"]="tampered"
    assert client.post("/api/v1/quality/evidence/verify",json=payload,headers=headers).json()["verified"] is False
    assert len(client.get("/api/v1/quality/audits/run-1",headers=headers).json()["audits"])==3

def test_subset_ablation_and_review(api):
    client,headers=api
    subset=client.post("/api/v1/quality/subset",headers=headers,json={"samples":[{"id":"1","risk_bucket":"high"},{"id":"2","risk_bucket":"low"}]})
    assert subset.status_code==200 and subset.json()["count"]==2
    ablation=client.post("/api/v1/quality/ablation",headers=headers,json={"baseline":{"a":0.6},"variant":{"a":0.8}})
    assert ablation.status_code==200 and ablation.json()["causal_claim"] is False
    review=client.post("/api/v1/quality/reviews/consensus",headers=headers,json={"run_id":"run-1","verdicts":[{"reviewer_id":"a","verdict":"pass","confidence":0.98},{"reviewer_id":"b","verdict":"pass","confidence":0.99}]})
    assert review.status_code==200 and review.json()["decision"]=="pass"
    assert review.json()["golden_approved"] is False
    with store.connect() as db:
        assert db.execute("SELECT count(*) FROM golden").fetchone()[0]==0
