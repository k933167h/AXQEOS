import pytest
from app.evaluation_service import evaluate_run

@pytest.mark.asyncio
async def test_unconfigured_judge_escalates():
    result=await evaluate_run(risk=0.7,assertion_passed=True,confidence=0.5,evidence_summary="actual evidence")
    assert result["tier"]=="T3"
    assert result["outcome"]=="review"

@pytest.mark.asyncio
async def test_missing_evidence_never_passes():
    result=await evaluate_run(risk=0.7,assertion_passed=True,confidence=0.5)
    assert result["tier"]=="T3" and result["reason"]=="judge_evidence_missing"

@pytest.mark.asyncio
async def test_t0_deterministic_fail_without_judge():
    result=await evaluate_run(risk=0.2,assertion_passed=False,confidence=0.99)
    assert result["tier"]=="T0" and result["outcome"]=="fail"
    assert result["judge_executed"] is False

@pytest.mark.asyncio
async def test_prevent_tier_downgrade(monkeypatch):
    from app import evaluation_service
    async def fake(evidence,risk):
        return "T1","pass",{"reason":"mock"}
    monkeypatch.setattr(evaluation_service.judges,"evaluate",fake)
    result=await evaluate_run(risk=0.7,assertion_passed=True,confidence=0.5,evidence_summary="sample")
    assert result["tier"]=="T3" and result["reason"]=="judge_tier_downgrade_blocked"
