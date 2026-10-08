import os,tempfile
def test_persistence_and_promotion():
 from app import store
 with tempfile.TemporaryDirectory() as d:
  os.environ["AX_DB_PATH"]=d+"/test.sqlite3"
  store.init()
  store.put_run("run-1","external-1",{"test_id":"t"},"T3","review","needs SME")
  assert store.get_run("external-1")["id"]=="run-1"
  store.queue("run-1","kiwi")
  assert len(store.pending())==1
  store.approve("run-1","reviewer-1","approve","reviewed")
  store.promote("run-1","reviewer-1")
  with store.connect() as db:
   assert db.execute("SELECT count(*) FROM golden").fetchone()[0]==1
