import pytest
from lab.pilot_experiment import report

def item(arm, detected, minutes, cost=1):
    return {"case_id":"case-01","arm":arm, "ground_truth_ids":["D1","D2"],
            "detected_ids":detected,"human_minutes":minutes,
            "agent_cost_usd":cost,"reviewer":"tester","adjudicated":True}

def test_paired_metrics_distinguish_fp_from_tp():
    result=report([item("baseline",["D1"],30),item("pilot",["D1","D2","FAKE"],15)])
    assert result["baseline"]["recall"] == .5
    assert result["pilot"]["recall"] == 1.
    assert result["pilot"]["false_positives"] == 1
    assert result["comparison"]["human_minutes_reduction"] == .5
    assert result["comparison"]["decision"] == "insufficient_data"

def test_unpaired_rejected():
    x=item("baseline",[],5)
    y=item("pilot",[],5)
    y["case_id"]="other"
    with pytest.raises(ValueError,match="paired"):
        report([x,y])

def test_unadjudicated_rejected():
    x=item("baseline",[],5)
    y=item("pilot",[],5)
    y["adjudicated"]=False
    with pytest.raises(ValueError,match="unadjudicated"):
        report([x,y])
