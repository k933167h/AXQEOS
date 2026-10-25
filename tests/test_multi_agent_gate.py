import json
from pathlib import Path

from lab.multi_agent_gate import run, metrics


def test_gate_pass(tmp_path):
    (tmp_path / "target.py").write_text("x = 1\n")
    adapter = tmp_path / "adapter.py"
    adapter.write_text(
        "import json,sys\n"
        "request=json.load(open(sys.argv[1]))\n"
        "json.dump({'findings':[]},open(sys.argv[2],'w'))\n"
    )
    import sys
    config = {
        "context": {"requirement_id": "REQ-1", "diff_ref": "sha-test"},
        "reviewers": {role: [sys.executable, str(adapter), "{input}", "{output}"]
                      for role in ("correctness", "security", "architecture")},
        "required_tests": [[sys.executable, "-c", "assert 1 == 1"]],
    }
    result = run(config, tmp_path)
    assert result["gate"] == "pass"
    assert len(result["reviews"]) == 3
    assert result["human_approval"] == "pending"


def test_no_tests_fails_closed(tmp_path):
    adapter = tmp_path / "adapter.py"
    adapter.write_text("import json,sys\njson.dump({'findings':[]},open(sys.argv[2],'w'))\n")
    import sys
    result = run({
        "context": {"requirement_id": "R", "diff_ref": "sha"},
        "reviewers": {r: [sys.executable, str(adapter), "{input}", "{output}"]
                      for r in ("correctness", "security", "architecture")},
    }, tmp_path)
    assert result["gate"] == "hold"


def test_metrics_uses_truth_and_human_minutes():
    rows = [
        {"arm": "baseline", "adjudicated_defect_ids": ["a", "b"],
         "detected_defect_ids": ["a"], "human_review_minutes": 20},
        {"arm": "pilot", "adjudicated_defect_ids": ["a", "b"],
         "detected_defect_ids": ["a", "b"], "human_review_minutes": 10},
    ]
    result = metrics(rows)
    assert result["comparison"]["human_review_reduction_ratio"] == 0.5
    assert result["comparison"]["detection_rate_delta"] == 0.5
