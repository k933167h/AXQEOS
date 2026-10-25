"""Local contract test: atomic store -> leased worker -> mocked OTLP/Langfuse."""
import json
import httpx
from lab.atomic_evidence_outbox import save_and_enqueue
from lab.leased_outbox_worker import work_once
from lab.sqlite_evidence import verify
from lab.telemetry_outbox import connect

EVENT={"event_id":"E2E-C001","case_id":"CASE-C001","kind":"review",
       "trace_id":"0123456789abcdef0123456789abcdef",
       "commit_sha":"immutable-commit","artifact_digest":"sha256:approved"}

def test_end_to_end_transport_contract(tmp_path):
    db=tmp_path/"pilot.sqlite3"
    stored=save_and_enqueue(db,EVENT)
    receipts=[]
    def receiver(request):
        payload=json.loads(request.content)
        if request.url.path=="/v1/traces":
            spans=payload["resourceSpans"][0]["scopeSpans"][0]["spans"]
            assert spans[0]["traceId"]==EVENT["trace_id"]
            attrs={a["key"]:a["value"]["stringValue"] for a in spans[0]["attributes"]}
            assert attrs["event_hash"]==stored["event_hash"]
            assert attrs["event_id"]==EVENT["event_id"]
            receipts.append(("otel",attrs))
        elif request.url.path=="/api/public/ingestion":
            item=payload["batch"][0]
            assert item["body"]["traceId"]==EVENT["trace_id"]
            assert item["body"]["metadata"]["event_hash"]==stored["event_hash"]
            assert item["body"]["metadata"]["event_id"]==EVENT["event_id"]
            assert request.headers.get("authorization","").startswith("Basic ")
            receipts.append(("langfuse",item["body"]["metadata"]))
        else:
            raise AssertionError("unexpected receiver endpoint")
        return httpx.Response(200,json={})
    settings={"otel_url":"https://mock.example/v1/traces",
              "langfuse_url":"https://mock.example",
              "langfuse_public_key":"test-public","langfuse_secret_key":"test-secret"}
    with httpx.Client(transport=httpx.MockTransport(receiver)) as client:
        result=work_once(db,settings,client=client,now=100)
    assert result["claimed"]==2
    assert result["sent"]==2
    assert {name for name,_ in receipts}=={"otel","langfuse"}
    assert verify(db)["valid"]
    with connect(db) as dbcon:
        assert dbcon.execute("SELECT COUNT(*) FROM telemetry_outbox WHERE status='sent'").fetchone()[0]==2

def test_partial_transport_failure_preserves_evidence(tmp_path):
    db=tmp_path/"pilot.sqlite3"
    save_and_enqueue(db,EVENT)
    def receiver(request):
        return httpx.Response(503 if request.url.path=="/api/public/ingestion" else 200)
    settings={"otel_url":"https://mock.example/v1/traces",
              "langfuse_url":"https://mock.example",
              "langfuse_public_key":"public","langfuse_secret_key":"secret"}
    with httpx.Client(transport=httpx.MockTransport(receiver)) as client:
        result=work_once(db,settings,client=client,now=100)
    assert result["sent"]==1
    assert result["retried"]==1
    assert verify(db)["valid"]
    with connect(db) as dbcon:
        statuses={row[0]:row[1] for row in dbcon.execute("SELECT destination,status FROM telemetry_outbox")}
    assert statuses=={"otel":"sent","langfuse":"pending"}
