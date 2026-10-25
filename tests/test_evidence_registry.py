import json
import pytest
from lab.evidence_registry import record, decision

def fixture(arm, found, minutes):
    return {"case_id":"C1","arm":arm,"ground_truth_ids":["D1"],"detected_ids":found,
            "human_minutes":minutes,"agent_cost_usd":0.2,"reviewer":"R1","adjudicated":True}

def test_chain_and_tamper_detection(tmp_path):
    p=tmp_path/"evidence.jsonl"
    first=record(p,{"case_id":"C1","kind":"review","verdict":"hold"})
    second=record(p,{"case_id":"C1","kind":"adjudication","verdict":"confirmed"})
    assert second["previous_sha256"] == first["sha256"]
    lines=p.read_text().splitlines()
    lines[0]=lines[0].replace("hold","pass")
    p.write_text("\n".join(lines)+"\n")
    with pytest.raises(ValueError,match="modified"):
        record(p,{"case_id":"C1","kind":"gate"})

def test_gate_holds_without_real_approval():
    rows=[fixture("baseline",[],20),fixture("pilot",["D1"],10)]
    result=decision(rows,{"ci_passed":True})
    assert result["decision"]=="hold"
    assert "insufficient_paired_cases" in result["reasons"]
    assert "missing_sme_approved" in result["reasons"]
    assert result["automatically_promoted"] is False
