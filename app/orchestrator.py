"""Fail-closed adaptive routing with explicit evidence and budget gates."""
from dataclasses import dataclass
from .quality_algorithms import verify_evidence

@dataclass(frozen=True)
class Decision:
    tier: str
    outcome: str
    reason: str
    judge_allowed: bool
    estimated_cost_usd: float

def decide(*, risk:float, assertion_passed:bool|None, confidence:float|None,
           evidence:dict|None=None, expected_sha256:str|None=None,
           estimated_judge_cost_usd:float=0.0, max_judge_cost_usd:float=0.20,
           critical_risk:float=0.85, strong_judge_risk:float=0.65,
           confidence_accept:float=0.90, confidence_escalate:float=0.65)->Decision:
    if not 0<=risk<=1:raise ValueError("risk must be between 0 and 1")
    if confidence is not None and not 0<=confidence<=1:raise ValueError("invalid confidence")
    if estimated_judge_cost_usd<0 or max_judge_cost_usd<0:raise ValueError("invalid budget")
    if expected_sha256 is not None:
        if evidence is None or not verify_evidence(expected_sha256,evidence)["verified"]:
            return Decision("T3","review","evidence_integrity_failed",False,0.0)
    if assertion_passed is False:
        return Decision("T0","fail","deterministic_assertion_failed",False,0.0)
    if assertion_passed is None:
        return Decision("T3","review","assertion_missing",False,0.0)
    if risk>=critical_risk:
        return Decision("T3","review","critical_risk",False,0.0)
    if confidence is None:
        tier,reason="T2","confidence_missing"
    elif risk>=strong_judge_risk or confidence<confidence_escalate:
        tier,reason="T2","strong_judge_required"
    elif confidence<confidence_accept:
        tier,reason="T1","economical_judge_required"
    else:
        return Decision("T0","pass","deterministic_pass",False,0.0)
    if estimated_judge_cost_usd>max_judge_cost_usd:
        return Decision("T3","review","judge_budget_exceeded",False,0.0)
    return Decision(tier,"review",reason,True,estimated_judge_cost_usd)
