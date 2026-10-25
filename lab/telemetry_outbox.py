"""Durable pilot outbox for approved observability event metadata.

Transport contracts: OTLP HTTP JSON spans and Langfuse ingestion events.
Never put secret/model inputs, source, or hidden truth in payloads.
"""
import json
import sqlite3
import time
import uuid
from pathlib import Path
import httpx

def connect(db):
    db=Path(db)
    db.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(str(db),timeout=15,isolation_level=None)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("""CREATE TABLE IF NOT EXISTS telemetry_outbox(
      id TEXT PRIMARY KEY, destination TEXT NOT NULL, payload TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'pending', attempts INTEGER NOT NULL DEFAULT 0,
      next_attempt REAL NOT NULL DEFAULT 0, last_error TEXT)""")
    return c

def enqueue(db,destination,payload,event_id=None):
    if destination not in ("otel","langfuse"):raise ValueError("unknown destination")
    required={"event_id","trace_id","case_id","commit_sha","event_hash"}
    if not isinstance(payload,dict) or not required <= set(payload):
        raise ValueError("event metadata incomplete")
    if set(payload)-required:
        raise ValueError("unexpected telemetry fields")
    eid=event_id or str(uuid.uuid4())
    with connect(db) as c:
        c.execute("INSERT OR IGNORE INTO telemetry_outbox(id,destination,payload) VALUES(?,?,?)",
                  (eid,destination,json.dumps(payload,sort_keys=True)))
    return eid

def send(destination,payload,settings,client):
    if destination=="otel":
        url=settings.get("otel_url")
        if not url or not url.startswith("https://"):raise ValueError("HTTPS OTLP endpoint required")
        # OTLP/HTTP JSON request body; no model/source content is transmitted.
        trace=payload["trace_id"]
        if len(trace)!=32 or any(ch not in "0123456789abcdef" for ch in trace.lower()):
            raise ValueError("trace_id must be 32 hex chars")
        body={"resourceSpans":[{"resource":{"attributes":[{"key":"service.name","value":{"stringValue":"axqeos-pilot"}}]},
         "scopeSpans":[{"scope":{"name":"axqeos.evidence"},"spans":[{
         "traceId":trace,"spanId":"0000000000000001","name":"evidence.recorded",
         "startTimeUnixNano":str(time.time_ns()),"endTimeUnixNano":str(time.time_ns()),
         "attributes":[{"key":k,"value":{"stringValue":str(v)}} for k,v in payload.items()]
         }]}]}]}
        response=client.post(url,json=body,timeout=10)
    else:
        url=settings.get("langfuse_url")
        public=settings.get("langfuse_public_key")
        secret=settings.get("langfuse_secret_key")
        if not url or not url.startswith("https://") or not public or not secret:
            raise ValueError("Langfuse HTTPS URL and credentials required")
        body={"batch":[{"id":payload["event_id"],"type":"event-create",
            "timestamp":__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            "body":{"id":payload["event_id"],"traceId":payload["trace_id"],
                    "name":"axqeos.evidence","metadata":payload}}]}
        response=client.post(url.rstrip("/")+"/api/public/ingestion",json=body,
                             auth=(public,secret),timeout=10)
    response.raise_for_status()

def drain(db,settings,client=None,now=None,limit=20):
    now=time.time() if now is None else now
    processed=0
    client=client or httpx.Client()
    own=not (client is not None and client is not False) # replaced below by caller semantics
    try:
        con=connect(db)
        try:
            items=con.execute("""SELECT id,destination,payload,attempts FROM telemetry_outbox
              WHERE status='pending' AND next_attempt<=? ORDER BY rowid LIMIT ?""",
              (now,limit)).fetchall()
            for eid,dest,raw,attempts in items:
                try:
                    send(dest,json.loads(raw),settings,client)
                    con.execute("UPDATE telemetry_outbox SET status='sent',attempts=attempts+1,last_error=NULL WHERE id=?",(eid,))
                except (httpx.HTTPError,ValueError,KeyError,TypeError) as exc:
                    delay=min(3600,2**min(attempts+1,11))
                    con.execute("""UPDATE telemetry_outbox SET attempts=attempts+1,
                     next_attempt=?,last_error=? WHERE id=?""",(now+delay,str(exc)[:200],eid))
                processed+=1
        finally:con.close()
    finally:
        if own:client.close()
    return processed
