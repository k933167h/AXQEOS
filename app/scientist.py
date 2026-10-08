"""Human-gated, evidence-linked quality hypothesis/experiment/review workflow."""
import json, time, uuid
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from . import store
from .extended import require
import os

router = APIRouter(prefix="/api/v1/scientist", tags=["ScientistTwo-inspired quality loop"])

class Hypothesis(BaseModel):
    source_run_id: str = Field(min_length=1)
    statement: str = Field(min_length=10)
    proposed_test: str = Field(min_length=5)

class Experiment(BaseModel):
    hypothesis_id: str
    test_run_id: str
    evidence_uri: str = Field(min_length=1)
    notes: str = ""

class Review(BaseModel):
    hypothesis_id: str
    experiment_id: str
    reviewer: str = Field(min_length=2)
    decision: str
    note: str = ""

def initialize():
    with store.connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS quality_hypotheses(
            id TEXT PRIMARY KEY,source_run_id TEXT NOT NULL,statement TEXT NOT NULL,
            proposed_test TEXT NOT NULL,state TEXT NOT NULL,created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS quality_experiments(
            id TEXT PRIMARY KEY,hypothesis_id TEXT NOT NULL,test_run_id TEXT NOT NULL,
            evidence_uri TEXT NOT NULL,notes TEXT NOT NULL,created REAL NOT NULL,
            FOREIGN KEY(hypothesis_id) REFERENCES quality_hypotheses(id));
        CREATE TABLE IF NOT EXISTS quality_reviews(
            id TEXT PRIMARY KEY,hypothesis_id TEXT NOT NULL,experiment_id TEXT NOT NULL,
            reviewer TEXT NOT NULL,decision TEXT NOT NULL,note TEXT NOT NULL,created REAL NOT NULL);
        """)

def auth(token):
    require(token, os.getenv("AX_SME_TOKEN"))

@router.post("/hypotheses")
def hypothesis(item: Hypothesis, x_ax_sme_token: str | None = Header(default=None)):
    auth(x_ax_sme_token)
    if not store.get_run(item.source_run_id):
        raise HTTPException(404,"source run not found")
    initialize()
    hid=str(uuid.uuid4())
    with store.connect() as db:
        db.execute("INSERT INTO quality_hypotheses VALUES(?,?,?,?,?,?)",
                   (hid,item.source_run_id,item.statement,item.proposed_test,"proposed",time.time()))
    return {"hypothesis_id":hid,"state":"proposed","automated_execution":False}

@router.post("/experiments")
def experiment(item: Experiment, x_ax_sme_token: str | None = Header(default=None)):
    auth(x_ax_sme_token)
    initialize()
    if not store.get_run(item.test_run_id):
        raise HTTPException(404,"test run not found")
    with store.connect() as db:
        h=db.execute("SELECT * FROM quality_hypotheses WHERE id=?",(item.hypothesis_id,)).fetchone()
        if not h: raise HTTPException(404,"hypothesis not found")
        if h["state"]=="accepted":raise HTTPException(409,"accepted hypothesis is immutable")
        eid=str(uuid.uuid4())
        db.execute("INSERT INTO quality_experiments VALUES(?,?,?,?,?,?)",
                   (eid,item.hypothesis_id,item.test_run_id,item.evidence_uri,item.notes,time.time()))
        db.execute("UPDATE quality_hypotheses SET state='experimented' WHERE id=?",(item.hypothesis_id,))
    return {"experiment_id":eid,"state":"experimented"}

@router.post("/reviews")
def review(item: Review, x_ax_sme_token: str | None = Header(default=None)):
    auth(x_ax_sme_token)
    if item.decision not in ("accept","reject","revise"):
        raise HTTPException(422,"decision must be accept, reject or revise")
    initialize()
    with store.connect() as db:
        exp=db.execute("SELECT * FROM quality_experiments WHERE id=? AND hypothesis_id=?",
                       (item.experiment_id,item.hypothesis_id)).fetchone()
        if not exp: raise HTTPException(404,"experiment not found")
        h=db.execute("SELECT state FROM quality_hypotheses WHERE id=?",(item.hypothesis_id,)).fetchone()
        if not h or h["state"]=="accepted":raise HTTPException(409,"review not permitted")
        rid=str(uuid.uuid4())
        db.execute("INSERT INTO quality_reviews VALUES(?,?,?,?,?,?,?)",
                   (rid,item.hypothesis_id,item.experiment_id,item.reviewer,item.decision,item.note,time.time()))
        state={"accept":"accepted","reject":"rejected","revise":"needs_revision"}[item.decision]
        db.execute("UPDATE quality_hypotheses SET state=? WHERE id=?",(state,item.hypothesis_id))
    return {"review_id":rid,"state":state,"golden_promoted":False}

@router.get("/hypotheses/{hypothesis_id}")
def get_hypothesis(hypothesis_id: str, x_ax_sme_token: str | None = Header(default=None)):
    auth(x_ax_sme_token)
    initialize()
    with store.connect() as db:
        h=db.execute("SELECT * FROM quality_hypotheses WHERE id=?",(hypothesis_id,)).fetchone()
        if not h:raise HTTPException(404,"hypothesis not found")
        experiments=[dict(x) for x in db.execute("SELECT * FROM quality_experiments WHERE hypothesis_id=? ORDER BY created",(hypothesis_id,))]
        reviews=[dict(x) for x in db.execute("SELECT * FROM quality_reviews WHERE hypothesis_id=? ORDER BY created",(hypothesis_id,))]
    return {"hypothesis":dict(h),"experiments":experiments,"reviews":reviews}
