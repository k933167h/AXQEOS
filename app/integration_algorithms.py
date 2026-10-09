"""Vendor-independent deterministic algorithms. No external network access."""
import hashlib
import json
import random
import re

def canonical_fingerprint(test_id, external_run_id, evidence):
    """Stable deduplication key across workers and restarts."""
    if not test_id or not external_run_id:
        raise ValueError("test_id and external_run_id required")
    blob=json.dumps({"test_id":test_id,"external_run_id":external_run_id,"evidence":evidence},sort_keys=True,ensure_ascii=False,separators=(",",":"),default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()

def choose_tier(risk, confidence, complexity=0.5, budget=1.0, critical=0.85):
    """Fail closed; cost pressure must never downgrade a critical test."""
    for name,value in {"risk":risk,"complexity":complexity,"budget":budget}.items():
        if not isinstance(value,(int,float)) or not 0<=value<=1:
            raise ValueError(name+" outside [0,1]")
    if confidence is not None and (not isinstance(confidence,(int,float)) or not 0<=confidence<=1):
        raise ValueError("confidence outside [0,1]")
    if risk>=critical:
        return "T3","critical_risk"
    if confidence is None:
        return "T2","missing_confidence"
    if risk>=0.65 or complexity>=0.85 or confidence<0.75:
        return "T2","high_risk_or_uncertainty"
    if confidence>=0.95 and risk<=0.2 and complexity<=0.4:
        return "T0","deterministic_candidate_only"
    return "T1","economical_judge"

def retry_delay(attempt, base=2, cap=3600, jitter=0.2, seed=None):
    """Bounded exponential backoff; seed enables deterministic tests."""
    if not isinstance(attempt,int) or attempt<1:raise ValueError("attempt must be positive integer")
    if base<=0 or cap<=0 or not 0<=jitter<=1:raise ValueError("invalid retry policy")
    nominal=min(cap,base**min(attempt,32))
    rng=random.Random(seed) if seed is not None else random.SystemRandom()
    return max(0.0,min(cap,nominal*(1-jitter+rng.random()*jitter)))

def redact_evidence(value):
    """Best-effort redaction; never substitute for a full DLP/privacy review."""
    text=str(value)
    text=re.sub(r"(?i)(bearer\s+)[a-z0-9._~+/=-]+",r"\1[REDACTED]",text)
    text=re.sub(r"(?i)(api[_-]?key|token|password)(\s*[:=]\s*)[^\s,;]+",r"\1\2[REDACTED]",text)
    return text
