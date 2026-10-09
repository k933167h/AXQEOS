import os,sqlite3,json,time
from contextlib import contextmanager
def path():return os.getenv("AX_DB_PATH","/data/axqeos.sqlite3")
@contextmanager
def connect():
 p=path();os.makedirs(os.path.dirname(os.path.abspath(p)),exist_ok=True)
 db=sqlite3.connect(p,timeout=20);db.row_factory=sqlite3.Row
 try:yield db;db.commit()
 finally:db.close()
def init():
 with connect() as db:
  db.executescript("""CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,external_id TEXT UNIQUE,payload TEXT NOT NULL,tier TEXT NOT NULL,outcome TEXT NOT NULL,reason TEXT NOT NULL,created REAL NOT NULL);
CREATE TABLE IF NOT EXISTS approvals(id INTEGER PRIMARY KEY AUTOINCREMENT,run_id TEXT NOT NULL,reviewer TEXT NOT NULL,decision TEXT NOT NULL,note TEXT,created REAL NOT NULL);
CREATE TABLE IF NOT EXISTS outbox(id INTEGER PRIMARY KEY AUTOINCREMENT,run_id TEXT NOT NULL,destination TEXT NOT NULL,state TEXT NOT NULL DEFAULT 'pending',attempts INTEGER NOT NULL DEFAULT 0,last_error TEXT,next_attempt REAL NOT NULL DEFAULT 0,remote_id TEXT,UNIQUE(run_id,destination));
CREATE TABLE IF NOT EXISTS golden(id INTEGER PRIMARY KEY AUTOINCREMENT,run_id TEXT NOT NULL UNIQUE,approved_by TEXT NOT NULL,created REAL NOT NULL);""")
def put_run(run_id,external_id,payload,tier,outcome,reason):
 with connect() as db:db.execute("INSERT INTO runs VALUES(?,?,?,?,?,?,?)",(run_id,external_id,json.dumps(payload),tier,outcome,reason,time.time()))
def get_run(run_id):
 with connect() as db:
  row=db.execute("SELECT * FROM runs WHERE id=? OR external_id=?",(run_id,run_id)).fetchone()
  return dict(row) if row else None
def approve(run_id,reviewer,decision,note):
 with connect() as db:db.execute("INSERT INTO approvals(run_id,reviewer,decision,note,created) VALUES(?,?,?,?,?)",(run_id,reviewer,decision,note,time.time()))
def queue(run_id,destination):
 with connect() as db:db.execute("INSERT OR IGNORE INTO outbox(run_id,destination) VALUES(?,?)",(run_id,destination))
def pending():
 with connect() as db:return [dict(r) for r in db.execute("SELECT * FROM outbox WHERE state='pending' AND next_attempt<=? ORDER BY id LIMIT 20",(time.time(),))]
def finish(job,remote_id):
 with connect() as db:db.execute("UPDATE outbox SET state='delivered',remote_id=?,last_error=NULL WHERE id=?",(remote_id,job["id"]))
def retry(job,error,delay=None):
 attempts=job["attempts"]+1
 with connect() as db:db.execute("UPDATE outbox SET attempts=?,last_error=?,state=?,next_attempt=? WHERE id=?",(attempts,str(error)[:300],"dead" if attempts>=6 else "pending",time.time()+(min(3600,2**attempts) if delay is None else delay),job["id"]))
def promote(run_id,reviewer):
 with connect() as db:
  r=db.execute("SELECT outcome FROM runs WHERE id=?",(run_id,)).fetchone()
  a=db.execute("SELECT decision,reviewer FROM approvals WHERE run_id=? ORDER BY id DESC LIMIT 1",(run_id,)).fetchone()
  if not r or not a or a["decision"]!="approve" or a["reviewer"]!=reviewer:raise ValueError("SME approval required")
  db.execute("INSERT OR IGNORE INTO golden(run_id,approved_by,created) VALUES(?,?,?)",(run_id,reviewer,time.time()))
