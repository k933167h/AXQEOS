import os,uuid,json,time,yaml
from pathlib import Path
from fastapi import FastAPI,HTTPException
from fastapi.responses import Response
from pydantic import BaseModel,Field
from prometheus_client import Counter,generate_latest,CONTENT_TYPE_LATEST
from . import store
from .extended import router
app=FastAPI(title="AX QE OS",version="4.9.0")
store.init()
app.include_router(router)
RUNS=Counter("ax_e2e_runs_total","Runs",["tier","outcome"])
class Run(BaseModel):
 test_id:str
 goal:str=""
 risk:float=Field(ge=0,le=1)
 assertion_passed:bool|None=None
 confidence:float|None=Field(default=None,ge=0,le=1)
 external_run_id:str|None=None
 evidence_uri:str|None=None
def route(r):
 p=yaml.safe_load(Path("config/routing.yaml").read_text())["routing"]
 if r.assertion_passed is False:return "T0","fail","assertion_failed"
 if r.assertion_passed is None:return "T3","review","assertion_missing"
 if r.risk>=p["critical_risk"]:return "T3","review","critical_risk"
 if r.confidence is None:return "T2","review","confidence_missing"
 if r.risk>=p["strong_judge_risk"] or r.confidence<p["confidence_escalate"]:return "T2","review","strong_judge_required"
 if r.confidence<p["confidence_accept"]:return "T1","review","economical_judge_required"
 return "T0","pass","deterministic_pass"
@app.get("/health")
def health():return {"status":"ok","version":"4.9.0"}
@app.post("/api/v1/e2e/runs")
def ingest(r:Run):
 tier,outcome,reason=route(r)
 rid=str(uuid.uuid4())
 store.put_run(rid,r.external_run_id,r.model_dump(),tier,outcome,reason)
 RUNS.labels(tier,outcome).inc()
 if outcome=="fail":
  for dest in ("plane","kiwi","langfuse"):store.queue(rid,dest)
 return {"run_id":rid,"tier":tier,"outcome":outcome,"reason":reason,"golden_status":"candidate"}
@app.get("/api/v1/e2e/runs/{run_id}")
def get_run(run_id:str):
 row=store.get_run(run_id)
 if not row:raise HTTPException(404,"not found")
 row["payload"]=json.loads(row["payload"])
 return row
@app.get("/metrics")
def metrics():return Response(generate_latest(),media_type=CONTENT_TYPE_LATEST)
