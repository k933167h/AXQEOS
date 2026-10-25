import sqlite3
import pytest
from lab.sqlite_evidence import append,verify

def event(id):
    return {"event_id":id,"case_id":"CASE-1","kind":"review","trace_id":"abc123",
      "span_id":"span1","commit_sha":"commit123","artifact_digest":"sha256:digest",
      "metadata":{"gate":"hold"}}

def test_persistent_chain_and_duplicate(tmp_path):
    db=tmp_path/"events.sqlite3"
    first=append(db,event("evt1"))
    second=append(db,event("evt2"))
    assert second["previous_hash"]==first["event_hash"]
    assert verify(db)["checked"]==2
    with pytest.raises(sqlite3.IntegrityError):
        append(db,event("evt2"))
    assert verify(db)["valid"]

def test_modified_record_detected(tmp_path):
    db=tmp_path/"events.sqlite3"
    append(db,event("evt1"))
    con=sqlite3.connect(db)
    con.execute("UPDATE evidence_events SET payload_json='{}' WHERE event_id='evt1'")
    con.commit();con.close()
    assert verify(db)["valid"] is False

def test_reject_raw_fields(tmp_path):
    value=event("e1");value["source_code"]="secret"
    with pytest.raises(ValueError):
        append(tmp_path/"db.sqlite3",value)
