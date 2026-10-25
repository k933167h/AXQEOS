"""Lease-safe outbox worker for SQLite pilot; no live services configured by default."""
import json
import time
import uuid
from pathlib import Path
import httpx
from .telemetry_outbox import connect, send

def migrate(db):
    con=connect(db)
    try:
        cols={r[1] for r in con.execute("PRAGMA table_info(telemetry_outbox)")}
        for name,typ in (("lease_owner","TEXT"),("lease_until","REAL NOT NULL DEFAULT 0")):
            if name not in cols:
                con.execute("ALTER TABLE telemetry_outbox ADD COLUMN "+name+" "+typ)
        return con
    except Exception:
        con.close()
        raise

def claim(db,owner=None,now=None,limit=10,lease_seconds=90):
    owner=owner or str(uuid.uuid4())
    now=time.time() if now is None else now
    con=migrate(db)
    try:
        con.execute("BEGIN IMMEDIATE")
        rows=con.execute("""SELECT id,destination,payload,attempts FROM telemetry_outbox
          WHERE ((status='pending' AND next_attempt<=?)
          OR (status='leased' AND lease_until<=?)) ORDER BY rowid LIMIT ?""",
          (now,now,limit)).fetchall()
        for eid,_,_,_ in rows:
            con.execute("""UPDATE telemetry_outbox SET status='leased',
              lease_owner=?,lease_until=? WHERE id=?""",(owner,now+lease_seconds,eid))
        con.execute("COMMIT")
        return owner,rows
    except Exception:
        con.execute("ROLLBACK")
        raise
    finally:
        con.close()

def settle(db,owner,eid,attempts,ok,now=None,max_attempts=5,error=""):
    now=time.time() if now is None else now
    con=migrate(db)
    try:
        con.execute("BEGIN IMMEDIATE")
        if ok:
            cur=con.execute("""UPDATE telemetry_outbox SET status='sent',attempts=attempts+1,
              lease_owner=NULL,lease_until=0,last_error=NULL
              WHERE id=? AND lease_owner=? AND status='leased'""",(eid,owner))
        else:
            retries=attempts+1
            state="dead" if retries>=max_attempts else "pending"
            delay=min(3600,2**min(retries,11))
            cur=con.execute("""UPDATE telemetry_outbox SET status=?,attempts=?,
              next_attempt=?,lease_owner=NULL,lease_until=0,last_error=?
              WHERE id=? AND lease_owner=? AND status='leased'""",
              (state,retries,now+delay,error[:200],eid,owner))
        con.execute("COMMIT")
        return cur.rowcount == 1
    except Exception:
        con.execute("ROLLBACK")
        raise
    finally:
        con.close()

def work_once(db,settings,client=None,now=None,limit=10):
    own=client is None
    if own: client=httpx.Client()
    try:
        owner,rows=claim(db,now=now,limit=limit)
        counters={"claimed":len(rows),"sent":0,"retried":0,"dead":0}
        for eid,dest,payload,attempts in rows:
            try:
                send(dest,json.loads(payload),settings,client)
                if settle(db,owner,eid,attempts,True,now=now):
                    counters["sent"]+=1
            except (httpx.HTTPError,ValueError,KeyError,TypeError) as exc:
                if settle(db,owner,eid,attempts,False,now=now,error=str(exc)):
                    counters["dead" if attempts+1>=5 else "retried"]+=1
        return counters
    finally:
        if own:client.close()

def dead_letters(db):
    con=migrate(db)
    try:
        return [dict(id=r[0],destination=r[1],attempts=r[2],last_error=r[3])
                for r in con.execute("""SELECT id,destination,attempts,last_error
                FROM telemetry_outbox WHERE status='dead' ORDER BY rowid""")]
    finally:
        con.close()
