import pytest
from lab.blind_benchmark import public_manifest, grade

PUBLIC={"case_id":"C1","requirement_id":"REQ1","diff_ref":"sha1","repository_snapshot":"snapshot1","defect_ids":["SECRET"]}
def test_public_manifest_does_not_expose_labels():
    output=public_manifest([PUBLIC])
    assert "defect_ids" not in output[0]
    assert "SECRET" not in str(output)

def test_private_scoring():
    predictions=[{"case_id":"C1","adjudicated_detected_ids":["D1","FAKE"]}]
    truth=[{"case_id":"C1","defect_ids":["D1","D2"],"adjudicated":True}]
    out=grade(predictions,truth)
    assert (out["tp"],out["fp"],out["fn"])==(1,1,1)
    assert out["recall"]==.5 and out["precision"]==.5

def test_mismatched_cases_fail_closed():
    with pytest.raises(ValueError):
        grade([{"case_id":"C2","adjudicated_detected_ids":[]}],
              [{"case_id":"C1","defect_ids":[],"adjudicated":True}])

def test_no_unadjudicated_truth():
    with pytest.raises(ValueError):
        grade([{"case_id":"C1","adjudicated_detected_ids":[]}],
              [{"case_id":"C1","defect_ids":[],"adjudicated":False}])
