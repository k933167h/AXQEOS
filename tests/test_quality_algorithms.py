import pytest
from app.quality_algorithms import canonical_digest,verify_evidence,select_subset,ablation_delta,independent_review

def test_evidence_tamper_detection():
    original={"run":"1","score":0.9}
    digest=canonical_digest(original)
    assert verify_evidence(digest,{"score":0.9,"run":"1"})["verified"]
    assert not verify_evidence(digest,{"score":0.8,"run":"1"})["verified"]

def test_subset_deterministic_stratified():
    items=[{"id":str(i),"risk_bucket":"critical" if i<3 else "normal"} for i in range(20)]
    a=select_subset(items,fraction=0.2,seed="fixed")
    assert a==select_subset(list(reversed(items)),fraction=0.2,seed="fixed")
    assert {x["risk_bucket"] for x in a}=={"critical","normal"}
    assert len(a)==5

def test_ablation_is_descriptive_not_causal():
    result=ablation_delta({"a":0.7,"b":0.8},{"a":0.8,"b":0.9})
    assert result["mean_improvement"]==pytest.approx(0.1)
    assert result["causal_claim"] is False

def test_review_disagreement_and_duplicate_identity_escalate():
    a={"reviewer_id":"judge-a","verdict":"pass","confidence":0.98}
    b={"reviewer_id":"judge-b","verdict":"fail","confidence":0.99}
    assert independent_review([a,b])["decision"]=="escalate"
    assert independent_review([a,a])["decision"]=="escalate"
    b["verdict"]="pass"
    assert independent_review([a,b])["decision"]=="pass"
    assert independent_review([a,b])["golden_approved"] is False
