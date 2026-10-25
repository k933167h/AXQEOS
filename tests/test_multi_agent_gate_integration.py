"""Integration smoke exercises three independent subprocess review adapters."""
import sys
from pathlib import Path
from lab.multi_agent_gate import run

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "lab" / "mock_review_adapter.py"


def cfg(scenario):
    return {
        "context": {"requirement_id": "PILOT-1", "diff_ref": "immutable-test-commit",
                    "scenario": scenario},
        "reviewers": {role: [sys.executable, str(ADAPTER), "{input}", "{output}"]
                      for role in ("correctness", "security", "architecture")},
        "trusted_reproducers": {"seeded_issue": [sys.executable, "-c", "print('reproduced')"]},
        "required_tests": [[sys.executable, "-c", "assert True"]],
    }


def test_parallel_reviews_clean_pass():
    result = run(cfg("clean"), ROOT)
    assert result["gate"] == "pass"
    assert {x["role"] for x in result["reviews"]} == {"correctness", "security", "architecture"}


def test_verified_critical_blocks_gate():
    result = run(cfg("critical"), ROOT)
    assert result["gate"] == "hold"
    assert result["findings"][0]["verified"]
    assert result["reasons"]["blocking_findings"] == 1


def test_unverified_medium_blocks_gate():
    result = run(cfg("unverified"), ROOT)
    assert result["gate"] == "hold"
    assert result["reasons"]["unverified_findings"] == 1


def test_reviewer_cannot_inject_command():
    config = cfg("critical")
    config["trusted_reproducers"] = {}
    result = run(config, ROOT)
    assert result["gate"] == "hold"
    assert result["findings"][0]["verified"] is False
