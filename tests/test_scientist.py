import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import store

@pytest.fixture
def setup(tmp_path,monkeypatch):
    monkeypatch.setenv("AX_DB_PATH",str(tmp_path/"science.sqlite3"))
    monkeypatch.setenv("AX_SME_TOKEN","test-sme")
    store.init()
    store.put_run("source-1","external-source",{"test_id":"source"},"T0","fail","failed")
    store.put_run("test-1","external-test",{"test_id":"test"},"T0","pass","passed")
    return TestClient(app),{"X-AX-SME-Token":"test-sme"}

def test_hypothesis_experiment_review_and_no_auto_golden(setup):
    client,headers=setup
    h=client.post("/api/v1/scientist/hypotheses",headers=headers,json={
        "source_run_id":"source-1","statement":"Retry isolation may reduce intermittent failure",
        "proposed_test":"Replay under isolated network conditions"})
    assert h.status_code==200,h.text
    hid=h.json()["hypothesis_id"]
    e=client.post("/api/v1/scientist/experiments",headers=headers,json={
        "hypothesis_id":hid,"test_run_id":"test-1","evidence_uri":"artifact://replay-001"})
    assert e.status_code==200,e.text
    r=client.post("/api/v1/scientist/reviews",headers=headers,json={
        "hypothesis_id":hid,"experiment_id":e.json()["experiment_id"],"reviewer":"sme-1",
        "decision":"accept","note":"validated"})
    assert r.status_code==200,r.text
    assert r.json()["golden_promoted"] is False
    state=client.get("/api/v1/scientist/hypotheses/"+hid,headers=headers)
    assert state.json()["hypothesis"]["state"]=="accepted"
    assert len(state.json()["experiments"])==1
    assert len(state.json()["reviews"])==1
    with store.connect() as db:
        assert db.execute("SELECT count(*) FROM golden").fetchone()[0]==0

def test_scientist_auth_and_missing_source(setup):
    client,headers=setup
    payload={"source_run_id":"missing","statement":"A sufficiently descriptive hypothesis","proposed_test":"Execute replay"}
    assert client.post("/api/v1/scientist/hypotheses",json=payload).status_code==403
    assert client.post("/api/v1/scientist/hypotheses",headers=headers,json=payload).status_code==404
