import httpx
from lab.leased_outbox_worker import claim,settle,work_once,dead_letters
from lab.telemetry_outbox import enqueue,connect

PAYLOAD={"event_id":"E","trace_id":"a"*32,"case_id":"C","commit_sha":"sha","event_hash":"digest"}
def test_exclusive_claim(tmp_path):
    db=tmp_path/"queue.db"
    enqueue(db,"otel",PAYLOAD,event_id="E:otel")
    owner,items=claim(db,owner="worker-A",now=100)
    assert len(items)==1
    other,again=claim(db,owner="worker-B",now=100)
    assert not again
    assert not settle(db,"worker-B","E:otel",0,True,now=100)
    assert settle(db,"worker-A","E:otel",0,True,now=100)

def test_retry_dead_letter(tmp_path):
    db=tmp_path/"queue.db"
    enqueue(db,"otel",PAYLOAD,event_id="E:otel")
    def failure(request):return httpx.Response(503)
    with httpx.Client(transport=httpx.MockTransport(failure)) as c:
        for n in range(5):
            result=work_once(db,{"otel_url":"https://example.org/v1/traces"},client=c,now=100000+n*4000)
            assert result["claimed"]==1
    assert dead_letters(db)[0]["attempts"]==5
    with connect(db) as c:
        assert c.execute("SELECT status FROM telemetry_outbox").fetchone()[0]=="dead"

def test_lease_expiry_reclaim(tmp_path):
    db=tmp_path/"queue.db"
    enqueue(db,"otel",PAYLOAD,event_id="E:otel")
    _,a=claim(db,owner="old",now=100,lease_seconds=10)
    _,b=claim(db,owner="new",now=111,lease_seconds=10)
    assert len(a)==len(b)==1
    assert not settle(db,"old","E:otel",0,True,now=111)
