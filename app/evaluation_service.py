"""Shared T0-T3 execution path; model failures escalate rather than pass."""
import httpx
from . import judges
from .orchestrator import decide

async def evaluate_run(*, risk:float, assertion_passed:bool|None, confidence:float|None,
                       evidence_summary:str="", evidence:dict|None=None,
                       expected_sha256:str|None=None,
                       estimated_judge_cost_usd:float=0.0,
                       policy:dict|None=None)->dict:
    p=policy or {}
    d=decide(
        risk=risk,assertion_passed=assertion_passed,confidence=confidence,
        evidence=evidence,expected_sha256=expected_sha256,
        estimated_judge_cost_usd=estimated_judge_cost_usd,
        max_judge_cost_usd=p.get("max_judge_usd_per_run",0.20),
        critical_risk=p.get("critical_risk",0.85),
        strong_judge_risk=p.get("strong_judge_risk",0.65),
        confidence_accept=p.get("confidence_accept",0.90),
        confidence_escalate=p.get("confidence_escalate",0.65))
    result={"tier":d.tier,"outcome":d.outcome,"reason":d.reason,
            "estimated_judge_cost_usd":d.estimated_cost_usd,
            "judge_executed":False,"judge_calls":[]}
    if not d.judge_allowed:return result
    if not evidence_summary.strip():
        return {**result,"tier":"T3","outcome":"review","reason":"judge_evidence_missing"}
    try:
        tier,outcome,judgement=await judges.evaluate(evidence_summary,risk)
        if tier not in ("T1","T2","T3") or outcome not in ("pass","fail","review"):
            raise ValueError("invalid judge result")
        # The routing policy may require T2. A T1 decision cannot override it.
        if d.tier=="T2" and tier=="T1":
            return {**result,"tier":"T3","outcome":"review","reason":"judge_tier_downgrade_blocked","judge_executed":True,"judge_calls":judgement.get("_calls",[])}
        # Missing model credentials yield a review verdict, never a pass.
        return {**result,"tier":tier,"outcome":outcome,
                "reason":str(judgement.get("reason","judge_result"))[:500],
                "judge_executed":True,"judge_calls":judgement.get("_calls",[])}
    except (httpx.HTTPError,ValueError,KeyError,TypeError,IndexError,TimeoutError):
        return {**result,"tier":"T3","outcome":"review",
                "reason":"judge_unavailable_or_invalid","judge_executed":False}
