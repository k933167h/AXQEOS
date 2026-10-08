import os,uuid,json
from fastapi import APIRouter,HTTPException,Header
from pydantic import BaseModel,Field
from . import store,judges
router=APIRouter(prefix="/api/v1")
class ReporterResult(BaseModel):
 external_run_id:str=Field(min_length=1)
 test_id:str
 goal:str=""
 risk:float=Field(ge=0,le=1)
 assertion_passed:bool|None=None
 evidence_uri:str|None=None
 evidence_summary:str=""
class Approval(BaseModel):
 reviewer:str=Field(min_length=2)
 decision:str
 note:str=""
@router.post("/reporter")
async def reporter(item:ReporterResult,x_ax_reporter_token:str|None=Header(default=None)):
 secret=os.getenv("AX_REPORTER_TOKEN")
 if not secret or x_ax_reporter_token!=secret:raise HTTPException(401,"reporter authentication required")
 existing=store.get_run(item.external_run_id)
 if existing:return {"run_id":existing["id"],"outcome":existing["outcome"],"idempotent":True}
 tier,outcome,reason="T0","pass","deterministic_pass"
 if item.assertion_passed is False:tier,outcome,reason="T0","fail","deterministic_fail"
 elif item.assertion_passed is None:tier,outcome,reason="T3","review","assertion_missing"
 if outcome=="pass" and item.risk>=0.85:tier,outcome,reason="T3","review","critical_risk"
 elif outcome=="pass" and item.evidence_summary:
  tier,outcome,judgement=await judges.evaluate(item.evidence_summary,item.risk)
  reason=str(judgement.get("reason","judge_result"))[:500]
 rid=str(uuid.uuid4())
 store.put_run(rid,item.external_run_id,item.model_dump(),tier,outcome,reason)
 if outcome=="fail":
  for dest in ("plane","kiwi","langfuse"):store.queue(rid,dest)
 elif outcome=="review":store.queue(rid,"langfuse")
 return {"run_id":rid,"tier":tier,"outcome":outcome,"reason":reason}
@router.get("/runs/{run_id}/persistent")
def persistent_run(run_id:str):
 row=store.get_run(run_id)
 if not row:raise HTTPException(404,"not found")
 row["payload"]=json.loads(row["payload"])
 return row
@router.post("/runs/{run_id}/approval")
def approval(run_id:str,item:Approval,x_ax_sme_token:str|None=Header(default=None)):
 if not os.getenv("AX_SME_TOKEN") or x_ax_sme_token!=os.getenv("AX_SME_TOKEN"):raise HTTPException(403,"SME authorization required")
 row=store.get_run(run_id)
 if not row:raise HTTPException(404,"not found")
 if row["outcome"]!="review":raise HTTPException(409,"only review cases are approvable")
 if item.decision not in ("approve","reject"):raise HTTPException(422,"invalid decision")
 store.approve(row["id"],item.reviewer,item.decision,item.note)
 if item.decision=="reject":store.queue(row["id"],"plane")
 return {"run_id":row["id"],"decision":item.decision,"golden_status":"candidate_only"}
