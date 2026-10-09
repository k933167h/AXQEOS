import pytest
from app.integration_algorithms import canonical_fingerprint,choose_tier,retry_delay,redact_evidence

def test_fingerprint_stable_order_and_distinct():
    a=canonical_fingerprint("case","run",{"b":2,"a":1})
    assert a==canonical_fingerprint("case","run",{"a":1,"b":2})
    assert a!=canonical_fingerprint("case","other",{"a":1,"b":2})

def test_critical_not_downgraded_by_budget():
    assert choose_tier(0.95,0.99,budget=0)[0]=="T3"

def test_missing_confidence_escalates():
    assert choose_tier(0.2,None)[0]=="T2"

def test_high_confidence_is_only_candidate():
    assert choose_tier(0.1,0.99,complexity=0.1)[1]=="deterministic_candidate_only"

def test_invalid_inputs_rejected():
    with pytest.raises(ValueError):choose_tier(1.2,0.5)
    with pytest.raises(ValueError):choose_tier(0.5,-0.1)
    with pytest.raises(ValueError):retry_delay(0)

def test_retry_bounded_and_reproducible():
    assert retry_delay(100,seed=1)<=3600
    assert retry_delay(4,seed=123)==retry_delay(4,seed=123)

def test_redact_credentials():
    s=redact_evidence("Authorization: Bearer abc.def password=supersecret")
    assert "abc.def" not in s and "supersecret" not in s
