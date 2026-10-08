"""API integration checks with isolated SQLite and mocked external judge."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import store

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("AX_DB_PATH", str(tmp_path / "ax.sqlite3"))
    monkeypatch.setenv("AX_REPORTER_TOKEN", "reporter-test-secret")
    monkeypatch.setenv("AX_SME_TOKEN", "sme-test-secret")
    store.init()
    return TestClient(app)

def test_reporter_auth_idempotency_and_outbox(client):
    payload = {"external_run_id":"army-001","test_id":"homepage","risk":0.2,"assertion_passed":False}
    assert client.post("/api/v1/reporter", json=payload).status_code == 403
    headers={"X-AX-Reporter-Token":"reporter-test-secret"}
    first=client.post("/api/v1/reporter",json=payload,headers=headers)
    assert first.status_code == 200
    assert first.json()["outcome"] == "fail"
    again=client.post("/api/v1/reporter",json=payload,headers=headers)
    assert again.json()["idempotent"] is True
    assert again.json()["run_id"] == first.json()["run_id"]
    with store.connect() as db:
        assert db.execute("SELECT count(*) FROM runs").fetchone()[0] == 1
        assert {r[0] for r in db.execute("SELECT destination FROM outbox")} == {"plane","kiwi","langfuse"}

def test_sme_approval_and_golden_gate(client):
    headers={"X-AX-Reporter-Token":"reporter-test-secret"}
    r=client.post("/api/v1/reporter",json={"external_run_id":"army-002","test_id":"critical","risk":0.95,"assertion_passed":True},headers=headers)
    assert r.status_code == 200 and r.json()["tier"] == "T3"
    rid=r.json()["run_id"]
    url=f"/api/v1/runs/{rid}/golden/promote"
    auth={"X-AX-SME-Token":"sme-test-secret"}
    assert client.post(url,params={"reviewer":"expert"},headers=auth).status_code == 409
    assert client.post(f"/api/v1/runs/{rid}/approval",json={"reviewer":"expert","decision":"approve"},headers=auth).status_code == 200
    assert client.post(url,params={"reviewer":"expert"},headers=auth).status_code == 200
    with store.connect() as db:
        assert db.execute("SELECT count(*) FROM golden").fetchone()[0] == 1
