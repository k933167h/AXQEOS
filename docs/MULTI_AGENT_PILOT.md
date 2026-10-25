# Multi-Agent Review → Evidence Verification → Quality Gate (Pilot)

This is an **opt-in pilot** independent of the existing API and T0–T3 judge. It does not call any LLM by itself, nor assert real performance improvements.

## Contract

Run three independent reviewer adapters (correctness, security, architecture), each receiving `{input}` as JSON and writing `{output}` as JSON. All reviewer responses must use `{"findings":[...]}`. Findings may contain `title`, `file`, `line`, `severity`, and a reproducible **argv** `reproducer` command. Review findings without a passing reproduction remain unverified, never silently accepted as false. Any high/critical finding holds the gate, even if unverified. The gate also holds if a reviewer fails or mandatory regression tests are missing/fail. The gate result is NOT a deployment authorization; human approval remains pending.

**Security:** Reviewers and reproduction commands can execute code. Only use **trusted** adapters and test commands in an isolated CI environment with least privilege and no production secrets. Do not accept reviewer-provided arbitrary commands from untrusted models in production. Before production, use an allowlisted verification runner and container isolation. Don't expose secrets or untrusted repository contents to external providers without authorization.

## Execution

Use `python -m lab.multi_agent_gate run --repo . --config path/to/review_config.json --output /tmp/ax-pilot-gate.json`.

Example config:

```json
{
  "context": {"requirement_id": "REQ-123", "diff_ref": "immutable-commit-sha"},
  "reviewers": {
    "correctness": ["python", "trusted_review_adapter.py", "{input}", "{output}"],
    "security": ["python", "trusted_review_adapter.py", "{input}", "{output}"],
    "architecture": ["python", "trusted_review_adapter.py", "{input}", "{output}"]
  },
  "required_tests": [["python", "-m", "pytest", "-q", "tests"]],
  "timeout_seconds": 120
}
```

Example reviewer output: `{"findings":[{"title":"Regression","file":"app/main.py","line":1,"severity":"high","reproducer":["python","trusted_repro.py"]}]}`. Exit code 0 from the trusted reproducer means the reported failure condition was confirmed, **not** that a regression test passed.

## Measuring actual outcomes

Record independent ground-truth defects and human active-review time per case. A case is one paired, difficulty-matched work item; measure baseline and pilot with the same rubric. Record false positives separately. Human minutes must come from actual human timers, not agent processing time. Do not claim results without sufficient labeled cases.

```
python -m lab.multi_agent_gate metrics --config pilot_measurements.json --output /tmp/ax-pilot-metrics.json
```

Sample records (illustrative, NOT measured):
```json
[
 {"arm":"baseline","adjudicated_defect_ids":["D1","D2"],"detected_defect_ids":["D1"],"human_review_minutes":20},
 {"arm":"pilot","adjudicated_defect_ids":["D1","D2"],"detected_defect_ids":["D1","D2"],"human_review_minutes":10}
]
```

## Expansion gates (not activated)

- **G1:** After sufficient paired cases, improve detection rate without unacceptable false-positive growth; demonstrate lower active human review minutes, controlled cost and no security regressions. Require SME review of statistically uncertain results.
- **G2:** Parallel root-cause investigation with read-only independent agents and source-grounded plans.
- **G3:** Harness² evolution: version prompts/tools, benchmark on held-out Golden Dataset, reject regressions, require approval before promoting harness.
- **G4:** LLMWiki Gherkin: link Feature/Scenario IDs, Requirement ID, verification traces, test runs and evidence records.

Current repository status: **pilot implementation, not production-proven**. Nothing here claims external model execution or observed defect-detection/time improvements.
