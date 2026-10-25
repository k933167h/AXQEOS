# Blind AI reviewer evaluation — controlled rollout

This adds an **offline manifest / scoring separation**, not live model execution. The model sees only case_id, requirement_id, diff_ref and repository_snapshot. Do not put answers, fault injection markers or ground-truth descriptions in repository files, commit messages, prompt text, CLI history, issue descriptions, or the evaluation manifest.

1. Prepare isolated read-only repository snapshots without an answer key. The operator maintains the truth file in a separate private location with restricted access.
2. Run `python -m lab.blind_benchmark manifest --cases private_cases.json --output public_cases.json`. Inspect public_cases.json and snapshot history for leaks. Never send private_cases.json to an agent.
3. Execute authorized reviewer CLI in a no-secret sandbox on immutable commit SHA. Freeze raw model findings and record timestamp/model/provider/version, active human review minutes and actual billed cost. **Models' proposed defect IDs are not truth**.
4. Independent human adjudicators match claims to defect IDs and record `adjudicated_detected_ids` in predictions. Disagreements require a documented ruling; verified false positives remain in predictions.
5. Run `python -m lab.blind_benchmark grade --predictions adjudicated_predictions.json --truth private_truth.json --output scored_results.json`.
6. For paired human-time and cost comparison, use `python -m lab.pilot_experiment --input paired_pilot.json --output paired_metrics.json`. Gating/promotion still requires SME approval and statistical review.

Private truth schema: `[{"case_id":"C1","defect_ids":["D1"],"adjudicated":true}]`.
Post-adjudication predictions: `[{"case_id":"C1","adjudicated_detected_ids":["D1","FP1"]}]`.

**Caveats:** Public manifest generation does not scrub repository content or Git history. Real review must not reuse `lab/fixtures/seeded_defects.py` as hidden evaluation because it reveals defects. All output data are untrusted until independently adjudicated. No observed performance improvement is claimed. The current CLI adapter and gate still require real sandbox integration and vendor version validation.
