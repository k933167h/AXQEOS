"""Authenticated APIs for deterministic quality analysis; results never promote Golden."""
import json
import os
import time
import uuid
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from . import store
from .extended import require
from .quality_algorithms import canonical_digest, verify_evidence, select_subset, ablation_delta, independent_review

router=APIRouter(prefix="/api/v1/quality",tags=["Quality algorithms"])

class EvidenceInput(BaseModel):
    run_id: str
    evidence: dict
    expected_sha256: str | None = None

class SubsetInput(BaseModel):
    samples: list[dict]
    fraction: float = Field(default=0.2,gt=0,le=1)
    minimum: int = Field(default=1,ge=1)
    seed: str = "axqeos"

class AblationInput(BaseModel):
    baseline: dict[str,float]
    variant: dict[str,float]
    higher_is_better: bool = True

class ReviewInput(BaseModel):
    run_id: str
    verdicts: list[dict]
    minimum_reviewers: int = Field(default=2,ge=2)
    min_confidence: float = Field(default=0.9,ge=0,le=1)

def auth(token):
    require(token,os.getenv("AX_SME_TOKEN"))

def init():
    with store.connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS quality_audits(
        id TEXT PRIMARY KEY,run_id TEXT NOT NULL,kind TEXT NOT NULL,
        result TEXT NOT NULL,created REAL NOT NULL)""")

def record(run_id,kind,result):
    init()
    audit_id=str(uuid.uuid4())
    with store.connect() as db:
        db.execute("INSERT INTO quality_audits VALUES(?,?,?,?,?)",
                   (audit_id,run_id,kind,json.dumps(result,sort_keys=True),time.time()))
    return audit_id

@router.post("/evidence/verify")
def evidence(item:EvidenceInput,x_ax_sme_token:str|None=Header(default=None)):
    auth(x_ax_sme_token)
    if not store.get_run(item.run_id):raise HTTPException(404,"run not found")
    if item.expected_sha256 is None:
        result={"sha256":canonical_digest(item.evidence),"verified":False,"reason":"no_trusted_reference"}
    else:
        result=verify_evidence(item.expected_sha256,item.evidence)
    return {"audit_id":record(item.run_id,"evidence",result),**result}

@router.post("/subset")
def subset(item:SubsetInput,x_ax_sme_token:str|None=Header(default=None)):
    auth(x_ax_sme_token)
    try: selected=select_subset(item.samples,fraction=item.fraction,minimum=item.minimum,seed=item.seed)
    except ValueError as exc:raise HTTPException(422,str(exc))
    return {"selected":selected,"count":len(selected),"total":len(item.samples)}

@router.post("/ablation")
def ablation(item:AblationInput,x_ax_sme_token:str|None=Header(default=None)):
    auth(x_ax_sme_token)
    try:return ablation_delta(item.baseline,item.variant,higher_is_better=item.higher_is_better)
    except ValueError as exc:raise HTTPException(422,str(exc))

@router.post("/reviews/consensus")
def consensus(item:ReviewInput,x_ax_sme_token:str|None=Header(default=None)):
    auth(x_ax_sme_token)
    if not store.get_run(item.run_id):raise HTTPException(404,"run not found")
    result=independent_review(item.verdicts,minimum_reviewers=item.minimum_reviewers,min_confidence=item.min_confidence)
    return {"audit_id":record(item.run_id,"independent_review",result),**result,"golden_approved":False}

@router.get("/audits/{run_id}")
def audits(run_id:str,x_ax_sme_token:str|None=Header(default=None)):
    auth(x_ax_sme_token)
    init()
    with store.connect() as db:
        rows=[dict(r) for r in db.execute("SELECT * FROM quality_audits WHERE run_id=? ORDER BY created",(run_id,))]
    for row in rows:row["result"]=json.loads(row["result"])
    return {"run_id":run_id,"audits":rows}
