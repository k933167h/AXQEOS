"""Deterministic seeded reviewer for verifying harness wiring only; NOT AI accuracy."""
import json
import sys
from pathlib import Path

request = json.loads(Path(sys.argv[1]).read_text())
role = request["role"]
root = Path.cwd()
fixture = root / "lab" / "fixtures" / "seeded_defects.py"
source = fixture.read_text(encoding="utf-8")
findings = []
if role == "correctness" and "return amount + discount" in source:
    findings.append({"title":"Seeded discount arithmetic bug", "file":"lab/fixtures/seeded_defects.py",
                     "line":4,"severity":"high","reproducer_id":"D001",
                     "defect_id":"D001"})
if role == "security" and "return not is_admin" in source:
    findings.append({"title":"Seeded authorization inversion", "file":"lab/fixtures/seeded_defects.py",
                     "line":8,"severity":"critical","reproducer_id":"D002",
                     "defect_id":"D002"})
Path(sys.argv[2]).write_text(json.dumps({"findings":findings}),encoding="utf-8")
