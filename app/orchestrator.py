"""Conservative orchestrator: existing T0 fail-closed precedence and configured thresholds remain authoritative."""
from .integration_algorithms import choose_tier

def route_assertion(assertion_passed,risk,confidence,policy,complexity=0.5,budget=1.0):
    if assertion_passed is False:
        return "T0","fail","assertion_failed"
    if assertion_passed is None:
        return "T3","review","assertion_missing"
    if risk>=policy["critical_risk"]:
        return "T3","review","critical_risk"
    if confidence is None:
        return "T2","review","confidence_missing"
    if risk>=policy["strong_judge_risk"] or confidence<policy["confidence_escalate"]:
        return "T2","review","strong_judge_required"
    if confidence<policy["confidence_accept"]:
        return "T1","review","economical_judge_required"
    # Existing T0 acceptance requires explicit assertion + confidence threshold.
    # Complexity can only escalate; it must never silently downgrade existing tiers.
    proposed,why=choose_tier(risk,confidence,complexity,budget,policy["critical_risk"])
    if proposed=="T2":
        return "T2","review","complexity_escalation" if complexity>=0.85 else "algorithm_escalation"
    if proposed=="T1":
        return "T1","review","algorithm_economical_judge"
    return "T0","pass","deterministic_pass"
