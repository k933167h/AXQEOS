import pytest
from app.judge_metrics import calibration_metrics,judge_cost,evaluation_economics

def test_perfect_calibration():
    r=calibration_metrics([{"confidence":1,"correct":True},{"confidence":0,"correct":False}])
    assert r["brier_score"]==0
    assert r["ece"]==0
    assert r["calibrated"] is False

def test_calibration_rejects_missing_labels():
    with pytest.raises(ValueError):calibration_metrics([])
    with pytest.raises(ValueError):calibration_metrics([{"confidence":1.2,"correct":True}])

def test_cost_from_real_usage_inputs():
    assert judge_cost(input_tokens=1_000_000,output_tokens=500_000,input_usd_per_million=1,output_usd_per_million=2)==2
    with pytest.raises(ValueError):judge_cost(input_tokens=-1,output_tokens=2,input_usd_per_million=1,output_usd_per_million=1)

def test_economics_denominators():
    r=evaluation_economics([{"usd":0.1,"correct":True,"critical":True,"false_accept":False},
                           {"usd":0.2,"correct":False,"critical":True,"false_accept":True}])
    assert r["cost_per_correct_evaluation_usd"]==pytest.approx(0.3)
    assert r["false_accept_rate"]==0.5
    assert r["critical_false_accept_rate"]==0.5
