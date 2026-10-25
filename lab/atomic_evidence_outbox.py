"""Atomic evidence + telemetry enqueue in the same SQLite transaction."""
import hashlib
import json
import sqlite3
from datetime import datetime,timezone
from pathlib import Path
from .sqlite_evidence import connect, canonical
from .telemetry_outbox import connect as outbox_connect

def save_and_enqueue(db: Path, event: dict):
    required=("event_id","case_id","kind","trace_id","commit_sha","artifact_digest")
    if any(not isinstance(event.get(k),str) or not event[k] for k in required):
        raise ValueError("missing evidence fields")
    if set(event)-set(required)-{"span_id","metadata"}:
        raise ValueError("unrecognized evidence fields")
    if not isinstance(event.get("metadata",{}),dict):
        raise ValueError("invalid metadata")
    # Outbox migration initializes table before the atomic transaction.
    con=outbox_connect(db)
    try:
        con.execute("CREATE TABLE IF NOT EXISTS evidence_events (seq INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT UNIQUE NOT NULL,timestamp_utc TEXT NOT NULL,case_id TEXT NOT NULL,kind TEXT NOT NULL,trace_id TEXT NOT NULL,span_id TEXT,commit_sha TEXT NOT NULL,artifact_digest TEXT NOT NULL,previous_hash TEXT NOT NULL,event_hash TEXT NOT NULL,payload_json TEXT NOT NULL)")
        con.execute("BEGIN IMMEDIATE")
        prev=con.execute("SELECT event_hash FROM evidence_events ORDER BY seq DESC LIMIT 1").fetchone()
        previous=prev[0] if prev else "0"*64
        at=datetime.now(timezone.utc).isoformat()
        raw=canonical(event)
        digest=hashlib.sha256((previous+"|"+at+"|"+raw).encode()).hexdigest()
        con.execute("INSERT INTO evidence_events(event_id,timestamp_utc,case_id,kind,trace_id,span_id,commit_sha,artifact_digest,previous_hash,event_hash,payload_json) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (event["event_id"],at,event["case_id"],event["kind"],event["trace_id"],event.get("span_id"),event["commit_sha"],event["artifact_digest"],previous,digest,raw))
        payload={key:event[key] for key in ("event_id","case_id","trace_id","commit_sha")}
        payload["event_hash"]=digest
        for dest in ("otel","langfuse"):
            con.execute("INSERT INTO telemetry_outbox(id,destination,payload) VALUES(?,?,?)",
                        (event["event_id"]+":"+dest,dest,json.dumps(payload,sort_keys=True)))
        con.execute("COMMIT")
        return {"event_id":event["event_id"],"event_hash":digest,"destinations":2}
    except Exception:
        con.execute("ROLLBACK")
        raise
    finally:
        con.close()
