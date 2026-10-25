"""Transactional SQLite evidence persistence with trace correlation.

Pilot local durable store; not a replacement for production audit/WORM storage.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS evidence_events (
 seq INTEGER PRIMARY KEY AUTOINCREMENT,
 event_id TEXT NOT NULL UNIQUE,
 timestamp_utc TEXT NOT NULL,
 case_id TEXT NOT NULL,
 kind TEXT NOT NULL,
 trace_id TEXT NOT NULL,
 span_id TEXT,
 commit_sha TEXT NOT NULL,
 artifact_digest TEXT NOT NULL,
 previous_hash TEXT NOT NULL,
 event_hash TEXT NOT NULL,
 payload_json TEXT NOT NULL
);
"""

def connect(database: Path):
    database.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(database), timeout=15, isolation_level=None)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=15000")
    con.execute(SCHEMA)
    return con

def append(database: Path, event: dict):
    keys = ("event_id","case_id","kind","trace_id","commit_sha","artifact_digest")
    if any(not isinstance(event.get(k), str) or not event[k] for k in keys):
        raise ValueError("invalid evidence identifiers")
    if not isinstance(event.get("metadata", {}), dict):
        raise ValueError("metadata must be an object")
    # Do not persist raw code, credentials, or hidden ground truth.
    allowed = set(keys) | {"span_id", "metadata"}
    if set(event) - allowed:
        raise ValueError("unsupported fields: metadata only")
    con = connect(database)
    try:
        con.execute("BEGIN IMMEDIATE")
        prev = con.execute("SELECT event_hash FROM evidence_events ORDER BY seq DESC LIMIT 1").fetchone()
        previous = prev[0] if prev else "0"*64
        timestamp = datetime.now(timezone.utc).isoformat()
        payload = canonical(event)
        digest = hashlib.sha256((previous + "|" + timestamp + "|" + payload).encode()).hexdigest()
        con.execute("""INSERT INTO evidence_events
        (event_id,timestamp_utc,case_id,kind,trace_id,span_id,commit_sha,artifact_digest,
         previous_hash,event_hash,payload_json) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
         (event["event_id"],timestamp,event["case_id"],event["kind"],event["trace_id"],
          event.get("span_id"),event["commit_sha"],event["artifact_digest"],previous,digest,payload))
        con.execute("COMMIT")
        return {"event_id":event["event_id"],"event_hash":digest,"previous_hash":previous}
    except Exception:
        con.execute("ROLLBACK")
        raise
    finally:
        con.close()

def verify(database: Path):
    con=connect(database)
    previous="0"*64
    checked=0
    try:
        for timestamp,payload,prev,digest in con.execute(
            "SELECT timestamp_utc,payload_json,previous_hash,event_hash FROM evidence_events ORDER BY seq"):
            expected=hashlib.sha256((previous+"|"+timestamp+"|"+payload).encode()).hexdigest()
            if prev!=previous or expected!=digest:
                return {"valid":False,"checked":checked}
            previous=digest
            checked+=1
        return {"valid":True,"checked":checked,"head_hash":previous}
    finally:
        con.close()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("mode",choices=("append","verify"))
    parser.add_argument("--db",required=True)
    parser.add_argument("--input")
    args=parser.parse_args()
    db=Path(args.db)
    if args.mode=="append":
        if not args.input:parser.error("--input required")
        print(canonical(append(db,json.loads(Path(args.input).read_text(encoding="utf-8")))))
    else:
        value=verify(db)
        print(canonical(value))
        if not value["valid"]:raise SystemExit(2)

if __name__=="__main__":
    main()
