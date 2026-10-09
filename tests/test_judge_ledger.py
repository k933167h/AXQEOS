import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import store
from app.judge_ledger import record_calls,summary

def test_usage_ledger_distinguishes_unknown_cost(tmp_path,monkeypatch):
    monkeypatch.setenv("AX_DB_PATH",str(tmp_path/"usage.sqlite3"))
    monkeypatch.setenv("AX_SME_TOKEN","sme-test")
    store.init()
    store.put_run("run-1","ext-1",{"test_id":"case"},"T2","review","judge")
    record_calls("run-1",[
      {"model":"model-a","tier":"T1","verdict":"review","confidence":0.7,"latency_ms":100,
       "usage":{"prompt_tokens":1000000,"completion_tokens":500000},"status":"ok"},
      {"model":"model-b","tier":"T2","verdict":"review","confidence":0.8,"latency_ms":120,
       "usage":{},"status":"ok"}],
      pricing={"model-a":{"input_usd_per_million":1,"output_usd_per_million":2}})
    report=summary("run-1")
    assert report["known_cost_usd"]==2
    assert report["unpriced_calls"]==1
    assert report["cost_complete"] is False
    client=TestClient(app)
    url="/api/v1/e2e/runs/run-1/judge-telemetry"
    assert client.get(url).status_code==403
    assert client.get(url,headers={"X-AX-SME-Token":"sme-test"}).json()["unpriced_calls"]==1
