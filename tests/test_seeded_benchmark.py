"""End-to-end harness validation with *synthetic* seeded bugs."""
import sys
from pathlib import Path
from lab.multi_agent_gate import run

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "lab" / "fixtures" / "seeded_defects.py"
ADAPTER = ROOT / "lab" / "seeded_review_adapter.py"
ORACLE = ROOT / "lab" / "seeded_oracle.py"


def test_seeded_detections_reproduce_and_hold():
    config = {
        "context":{"requirement_id":"SYNTHETIC-001","diff_ref":"local-seed-v1"},
        "reviewers": {
            role:[sys.executable,str(ADAPTER),"{input}","{output}"]
            for role in ("correctness","security","architecture")
        },
        "trusted_reproducers":{
            defect:[sys.executable,str(ORACLE),defect,str(FIXTURE)]
            for defect in ("D001","D002")
        },
        "required_tests":[[sys.executable,"-c","assert True"]],
    }
    result = run(config, ROOT)
    assert result["gate"] == "hold"
    findings = {f["defect_id"]: f for f in result["findings"]}
    assert set(findings) == {"D001","D002"}
    assert all(f["verified"] is True for f in findings.values())
    assert result["reasons"]["blocking_findings"] == 2


def test_oracle_fails_for_fixed_source(tmp_path):
    fixed = tmp_path/"fixed.py"
    fixed.write_text("return amount - discount\nreturn is_admin\n",encoding="utf-8")
    from lab.seeded_oracle import check
    assert check("D001", fixed) != 0
    assert check("D002", fixed) != 0
