import os,uuid,json,time,yaml
from pathlib import Path
from fastapi import FastAPI,HTTPException,Header
from fastapi.responses import Response
from pydantic import BaseModel,Field
from prometheus_client import Counter,generate_latest,CONTENT_TYPE_LATEST
from . import store
from .orchestrator import decide
from .evaluation_service import evaluate_run
from .judge_ledger import record_calls, summary as judge_summary
from .extended import router, require
from .scientist import router as scientist_router
from .quality_api import router as quality_router
app=FastAPI(title="AX QE OS",version="4.9.0")
store.init()
app.include_router(router)
app.include_router(scientist_router)
app.include_router(quality_router)
RUNS=Counter("ax_e2e_runs_total","Runs",["tier","outcome"])
class Run(BaseModel):
 test_id:str
 goal:str=""
 risk:float=Field(ge=0,le=1)
 assertion_passed:bool|None=None
 confidence:float|None=Field(default=None,ge=0,le=1)
 external_run_id:str|None=None
 evidence_uri:str|None=None
 evidence:dict|None=None
 expected_sha256:str|None=None
 estimated_judge_cost_usd:float=Field(default=0,ge=0)
 evidence_summary:str=""
def route(r):
 p=yaml.safe_load(Path("config/routing.yaml").read_text())["routing"]
 d=decide(risk=r.risk,assertion_passed=r.assertion_passed,confidence=r.confidence,
          evidence=r.evidence,expected_sha256=r.expected_sha256,
          estimated_judge_cost_usd=r.estimated_judge_cost_usd,
          max_judge_cost_usd=p["max_judge_usd_per_run"],
          critical_risk=p["critical_risk"],strong_judge_risk=p["strong_judge_risk"],
          confidence_accept=p["confidence_accept"],confidence_escalate=p["confidence_escalate"])
 return d.tier,d.outcome,d.reason
@app.get("/health")
def health():return {"status":"ok","version":"4.9.0"}
@app.post("/api/v1/e2e/runs")
async def ingest(r:Run):
 p=yaml.safe_load(Path("config/routing.yaml").read_text())["routing"]
 result=await evaluate_run(risk=r.risk,assertion_passed=r.assertion_passed,confidence=r.confidence,evidence_summary=r.evidence_summary,evidence=r.evidence,expected_sha256=r.expected_sha256,estimated_judge_cost_usd=r.estimated_judge_cost_usd,policy=p)
 tier,outcome,reason=result["tier"],result["outcome"],result["reason"]
 rid=str(uuid.uuid4())
 store.put_run(rid,r.external_run_id,r.model_dump(),tier,outcome,reason)
 record_calls(rid,result.get("judge_calls",[]))
 RUNS.labels(tier,outcome).inc()
 if outcome=="fail":
  for dest in ("plane","kiwi","langfuse"):store.queue(rid,dest)
 return {"run_id":rid,"tier":tier,"outcome":outcome,"reason":reason,"judge_executed":result["judge_executed"],"estimated_judge_cost_usd":result["estimated_judge_cost_usd"],"golden_status":"candidate"}
@app.get("/api/v1/e2e/runs/{run_id}")
def get_run(run_id:str):
 row=store.get_run(run_id)
 if not row:raise HTTPException(404,"not found")
 row["payload"]=json.loads(row["payload"])
 return row
@app.get("/metrics")
def metrics():return Response(generate_latest(),media_type=CONTENT_TYPE_LATEST)

@app.get("/api/v1/e2e/runs/{run_id}/judge-telemetry")
def judge_telemetry(run_id:str,x_ax_sme_token:str|None=Header(default=None)):
 require(x_ax_sme_token,os.getenv('AX_SME_TOKEN'))
 if not store.get_run(run_id):raise HTTPException(404,"not found")
 return judge_summary(run_id)
