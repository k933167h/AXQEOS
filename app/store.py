import os, sqlite3, json, time
from contextlib import contextmanager
DB=os.getenv("AX_DB_PATH","/data/axq e os.sqlite3").replace(" ","")
def init():
 os.makedirs(os.path.dirname(os.path.abspath(DB)),exist_ok=True)
 with connect() as db:
  db.executescript("""CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,external_id TEXT UNIQUE,payload TEXT NOT NULL,tier TEXT NOT NULL,outcome TEXT NOT NULL,reason TEXT NOT NULL,created REAL NOT NULL);
CREATE TABLE IF NOT EXISTS approvals(id INTEGER PRIMARY KEY AUTOINCREMENT,run_id TEXT NOT NULL,reviewer TEXT NOT NULL,decision TEXT NOT NULL,note TEXT,created REAL NOT NULL);
CREATE TABLE IF NOT EXISTS outbox(id INTEGER PRIMARY KEY AUTOINCREMENT,run_id TEXT NOT NULL,destination TEXT NOT NULL,state TEXT NOT NULL DEFAULT 'pending',attempts INTEGER NOT NULL DEFAULT 0,last_error TEXT,UNIQUE(run_id,destination));""")
@contextmanager
def connect():
 db=sqlite3.connect(DB,timeout=20)
 db.row_factory=sqlite3.Row
 try:
  yield db
  db.commit()
 finally: db.close()
def put_run(run_id,external_id,payload,tier,outcome,reason):
 with connect() as db:
  db.execute("INSERT INTO runs VALUES(?,?,?,?,?,?,?)",(run_id,external_id,json.dumps(payload),tier,outcome,reason,time.time()))
def get_run(run_id):
 with connect() as db:
  row=db.execute("SELECT * FROM runs WHERE id=? OR external_id=?",(run_id,run_id)).fetchone()
  return dict(row) if row else None
def approve(run_id,reviewer,decision,note):
 with connect() as db:
  db.execute("INSERT INTO approvals(run_id,reviewer,decision,note,created) VALUES(?,?,?,?,?)",(run_id,reviewer,decision,note,time.time()))
def queue(run_id,destination):
 with connect() as db:
  db.execute("INSERT OR IGNORE INTO outbox(run_id,destination) VALUES(?,?)",(run_id,destination))
