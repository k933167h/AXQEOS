# AX QE OS — Paired defect-detection pilot

## Status
Experiment analysis code is implemented, **no production measurements have been collected**. Never present example rows as actual outcomes.

## Method
Use the same independently adjudicated bug set in baseline (existing review) and pilot (multi-agent review); compare items of equivalent size/difficulty and randomize order to reduce learning effects. Define a defect ID and location before seeing model findings. Two human adjudicators should resolve disputed labels. Capture actual active human minutes with a stopwatch; agent wall-clock time is a separate observation. Record API cost from provider billing separately and protect source code.

Create a local private `pilot.json` array; NEVER commit customer repository contents or reviewer identities without approval.

Example (synthetic input, not evidence):
```json
[
  {"case_id":"C-001","arm":"baseline","ground_truth_ids":["D1","D2"],"detected_ids":["D1"],"human_minutes":20,"agent_cost_usd":0,"reviewer":"R01","adjudicated":true},
  {"case_id":"C-001","arm":"pilot","ground_truth_ids":["D1","D2"],"detected_ids":["D1","D2"],"human_minutes":12,"agent_cost_usd":0.45,"reviewer":"R01","adjudicated":true}
]
```

Run: `python -m lab.pilot_experiment --input pilot.json --output pilot_report.json`.

Metrics: recall TP/(TP+FN), precision TP/(TP+FP), average actual human active review minutes, and provider cost. For fewer than 20 paired items, decision stays `insufficient_data`. At or above 20, code still does not auto-pass: requires SME adjudication and a statistical review; consider confidence intervals, false-positive burden, task stratification and reviewer-order effects. The 20-item threshold is a screening threshold, not a statistical power guarantee.

## Promotion conditions
No promotion without passing automated tests, validated sandbox isolation, tested live provider adapters, no significant critical defect escape, acceptable false-positive load, and documented human signoff. Subsequent parallel investigation → Harness² → LLMWiki Gherkin stages remain disabled until evidence-based approval.
