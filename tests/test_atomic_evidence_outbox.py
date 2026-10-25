import sqlite3
import httpx
import pytest
from lab.atomic_evidence_outbox import save_and_enqueue
from lab.sqlite_evidence import verify
from lab.telemetry_outbox import drain,connect

E={"event_id":"e1","case_id":"c1","kind":"review","trace_id":"a"*32,"commit_sha":"sha","artifact_digest":"digest"}
def test_atomic_save_and_rollback(tmp_path):
    db=tmp_path/"evidence.db"
    save_and_enqueue(db,E)
    assert verify(db)["valid"]
    with connect(db) as c:
        assert c.execute("SELECT COUNT(*) FROM telemetry_outbox").fetchone()[0]==2
    with pytest.raises(sqlite3.IntegrityError):
        save_and_enqueue(db,E)
    with connect(db) as c:
        assert c.execute("SELECT COUNT(*) FROM evidence_events").fetchone()[0]==1
        assert c.execute("SELECT COUNT(*) FROM telemetry_outbox").fetchone()[0]==2

def test_transient_error_then_success(tmp_path):
    db=tmp_path/"q.db"
    from lab.telemetry_outbox import enqueue
    p={"event_id":"e1","case_id":"c1","trace_id":"a"*32,"commit_sha":"sha","event_hash":"hash"}
    enqueue(db,"otel",p,"e1:otel")
    n=[0]
    def endpoint(request):
        n[0]+=1
        return httpx.Response(503 if n[0]==1 else 200)
    with httpx.Client(transport=httpx.MockTransport(endpoint)) as client:
        assert drain(db,{"otel_url":"https://example.org/v1/traces"},client,now=0)==1
        assert drain(db,{"otel_url":"https://example.org/v1/traces"},client,now=100)==1
    with connect(db) as c:
        assert c.execute("SELECT status FROM telemetry_outbox").fetchone()[0]=="sent"
