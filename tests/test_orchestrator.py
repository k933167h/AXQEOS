from app.orchestrator import decide
from app.quality_algorithms import canonical_digest

def test_t0_and_missing_assertion():
    assert decide(risk=0.2,assertion_passed=False,confidence=1).outcome=="fail"
    assert decide(risk=0.2,assertion_passed=None,confidence=1).tier=="T3"
    assert decide(risk=0.2,assertion_passed=True,confidence=0.99).tier=="T0"

def test_adaptive_judge_and_budget():
    assert decide(risk=0.2,assertion_passed=True,confidence=0.7).tier=="T1"
    assert decide(risk=0.7,assertion_passed=True,confidence=0.99).tier=="T2"
    assert decide(risk=0.7,assertion_passed=True,confidence=0.99,estimated_judge_cost_usd=0.3).reason=="judge_budget_exceeded"
    assert decide(risk=0.9,assertion_passed=True,confidence=1).tier=="T3"

def test_evidence_integrity_fail_closed():
    evidence={"status":"ok"}
    good=canonical_digest(evidence)
    assert decide(risk=0.1,assertion_passed=True,confidence=0.99,evidence=evidence,expected_sha256=good).outcome=="pass"
    assert decide(risk=0.1,assertion_passed=True,confidence=0.99,evidence={"status":"changed"},expected_sha256=good).reason=="evidence_integrity_failed"
