import tempfile
from app import store

def test_persistence_and_promotion(monkeypatch):
    with tempfile.TemporaryDirectory() as directory:
        monkeypatch.setenv("AX_DB_PATH", directory + "/test.sqlite3")
        store.init()
        store.put_run("run-1", "external-1", {"test_id": "t"}, "T3", "review", "needs SME")
        assert store.get_run("external-1")["id"] == "run-1"
        store.queue("run-1", "kiwi")
        assert len(store.pending()) == 1
        store.approve("run-1", "reviewer-1", "approve", "reviewed")
        store.promote("run-1", "reviewer-1")
        with store.connect() as db:
            assert db.execute("SELECT count(*) FROM golden").fetchone()[0] == 1

def test_reject_cannot_promote(monkeypatch):
    with tempfile.TemporaryDirectory() as directory:
        monkeypatch.setenv("AX_DB_PATH", directory + "/test.sqlite3")
        store.init()
        store.put_run("run-2", "external-2", {}, "T3", "review", "needs SME")
        store.approve("run-2", "reviewer-1", "reject", "not verified")
        try:
            store.promote("run-2", "reviewer-1")
            assert False, "Rejected runs must not be promoted"
        except ValueError:
            pass
