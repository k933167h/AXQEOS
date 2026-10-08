"""Local HTTP contract checks: real HTTP code paths with mocked upstreams; not production connectivity."""
import asyncio
import json
import pytest
import httpx
from app import judges,worker

def run(coro): return asyncio.run(coro)

def test_jev_and_llm_judge_escalation(monkeypatch):
    calls=[]
    def handler(request):
        calls.append((request.url.path, json.loads(request.content)["model"]))
        verdict={"verdict":"pass","confidence":0.45 if len(calls)==1 else 0.97,"reason":"evaluated"}
        return httpx.Response(200,json={"choices":[{"message":{"content":json.dumps(verdict)}}]})
    original=httpx.AsyncClient
    monkeypatch.setattr(httpx,"AsyncClient",lambda **kw: original(transport=httpx.MockTransport(handler),**kw))
    for k,v in {"JEV_MODEL":"jev","JEV_BASE_URL":"https://judge.test/v1","JEV_API_KEY":"mock","LLM_JUDGE_MODEL":"strong","LLM_JUDGE_BASE_URL":"https://judge.test/v1","LLM_JUDGE_API_KEY":"mock"}.items():monkeypatch.setenv(k,v)
    tier,outcome,details=run(judges.evaluate("evidence",0.4))
    assert (tier,outcome)==("T2","pass")
    assert [model for _,model in calls]==["jev","strong"]

def test_judge_unconfigured_fails_closed(monkeypatch):
    for k in ("JEV_MODEL","JEV_BASE_URL","JEV_API_KEY","LLM_JUDGE_MODEL","LLM_JUDGE_BASE_URL","LLM_JUDGE_API_KEY"):monkeypatch.delenv(k,raising=False)
    tier,outcome,_=run(judges.evaluate("untrusted evidence",0.5))
    assert outcome=="review"

def test_worker_outbound_contracts(monkeypatch,tmp_path):
    from app import store
    monkeypatch.setenv("AX_DB_PATH",str(tmp_path/"db.sqlite3"))
    store.init()
    store.put_run("r1","ext1",{"test_id":"t1","evidence_uri":"https://evidence.test/item"},"T0","fail","assertion_failed")
    for k,v in {"PLANE_ISSUE_URL":"https://plane.test/issues","PLANE_API_KEY":"mock","KIWI_RESULT_URL":"https://kiwi.test/results","KIWI_API_TOKEN":"mock","LANGFUSE_INGEST_URL":"https://langfuse.test/events","LANGFUSE_INGEST_TOKEN":"mock"}.items():monkeypatch.setenv(k,v)
    seen=[]
    def handler(request):
        seen.append((request.url.host,request.headers.get("idempotency-key"),json.loads(request.content)))
        return httpx.Response(201,json={"id":"remote-"+request.url.host})
    original=httpx.AsyncClient
    monkeypatch.setattr(httpx,"AsyncClient",lambda **kw: original(transport=httpx.MockTransport(handler),**kw))
    for destination in ("plane","kiwi","langfuse"):store.queue("r1",destination)
    run(worker.run_once())
    assert {host for host,_,_ in seen}=={"plane.test","kiwi.test","langfuse.test"}
    assert all(key.startswith("r1:") for _,key,_ in seen)
    with store.connect() as db:
        assert db.execute("SELECT count(*) FROM outbox WHERE state='delivered'").fetchone()[0]==3

def test_worker_retry_on_failure(monkeypatch,tmp_path):
    from app import store
    monkeypatch.setenv("AX_DB_PATH",str(tmp_path/"retry.sqlite3"))
    store.init()
    store.put_run("r2","ext2",{"test_id":"t2"},"T0","fail","assertion_failed")
    store.queue("r2","kiwi")
    monkeypatch.delenv("KIWI_RESULT_URL",raising=False)
    run(worker.run_once())
    with store.connect() as db:
        row=db.execute("SELECT state,attempts,last_error FROM outbox").fetchone()
        assert row["state"]=="pending" and row["attempts"]==1
        assert "not configured" in row["last_error"]
