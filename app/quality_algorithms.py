"""Deterministic, offline-capable quality algorithms. No LLM verdict can grant Golden approval."""
import hashlib
import json
import math
from dataclasses import dataclass
from typing import Mapping

def canonical_digest(value: object) -> str:
    """SHA-256 of stable JSON; caller must persist raw evidence independently."""
    encoded=json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

def verify_evidence(expected_sha256: str, evidence: object) -> dict:
    observed=canonical_digest(evidence)
    return {"verified":observed==expected_sha256,"expected":expected_sha256,"observed":observed}

def select_subset(items: list[dict], *, fraction: float=0.2, minimum: int=1, seed: str="axqeos") -> list[dict]:
    """Stable hash-ranked subset. Stratify by risk bucket to preserve critical samples."""
    if not 0<fraction<=1 or minimum<1:raise ValueError("invalid subset policy")
    if not items:return []
    groups:dict[str,list[dict]]={}
    for item in items:
        if "id" not in item:raise ValueError("sample id required")
        group=str(item.get("risk_bucket","default"))
        groups.setdefault(group,[]).append(item)
    selected=[]
    for group,group_items in sorted(groups.items()):
        n=min(len(group_items),max(minimum,math.ceil(len(group_items)*fraction)))
        ranked=sorted(group_items,key=lambda x:(hashlib.sha256((seed+":"+str(x["id"])).encode()).hexdigest(),str(x["id"])))
        selected.extend(ranked[:n])
    return selected

def ablation_delta(baseline: Mapping[str,float], variant: Mapping[str,float], *, higher_is_better: bool=True) -> dict:
    """Paired metric difference; descriptive only, not causal proof."""
    keys=sorted(set(baseline)&set(variant))
    if not keys:raise ValueError("no paired metrics")
    diffs={}
    for key in keys:
        a,b=float(baseline[key]),float(variant[key])
        if not math.isfinite(a) or not math.isfinite(b):raise ValueError("nonfinite metric")
        diffs[key]=(b-a) if higher_is_better else (a-b)
    return {"paired_count":len(keys),"mean_improvement":sum(diffs.values())/len(diffs),"per_metric":diffs,"causal_claim":False}

def independent_review(verdicts: list[dict], *, minimum_reviewers: int=2, min_confidence: float=0.9) -> dict:
    """Reject correlated reviewer IDs and abstain on disagreement or uncertainty."""
    if minimum_reviewers<2:raise ValueError("independent review requires >=2 reviewers")
    ids=[v.get("reviewer_id") for v in verdicts]
    if any(not i for i in ids) or len(ids)!=len(set(ids)):
        return {"decision":"escalate","reason":"reviewer_identity_not_independent"}
    if len(verdicts)<minimum_reviewers:
        return {"decision":"escalate","reason":"insufficient_reviewers"}
    for v in verdicts:
        if v.get("verdict") not in ("pass","fail") or not 0<=float(v.get("confidence",-1))<=1:
            return {"decision":"escalate","reason":"invalid_or_abstaining_review"}
        if float(v["confidence"])<min_confidence:
            return {"decision":"escalate","reason":"low_confidence"}
    outcomes={v["verdict"] for v in verdicts}
    if len(outcomes)!=1:return {"decision":"escalate","reason":"reviewer_disagreement"}
    return {"decision":outcomes.pop(),"reason":"independent_consensus","golden_approved":False}
