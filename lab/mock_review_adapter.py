"""Deterministic CI-only reviewer adapter; does NOT invoke an AI model."""
import json
import sys
from pathlib import Path

request = json.loads(Path(sys.argv[1]).read_text())
role = request["role"]
scenario = request.get("scenario", "clean")
findings = []
if scenario == "critical" and role == "correctness":
    findings = [{"title": "seeded critical issue", "file": "lab/multi_agent_gate.py",
                 "line": 1, "severity": "critical", "reproducer_id": "seeded_issue"}]
if scenario == "unverified" and role == "security":
    findings = [{"title": "unverified issue", "file": "lab/multi_agent_gate.py",
                 "line": 1, "severity": "medium", "reproducer_id": "unknown"}]
Path(sys.argv[2]).write_text(json.dumps({"findings": findings}))
