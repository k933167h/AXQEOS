# AX QE OS Architecture Overview — v4.9 baseline

Source of truth: https://github.com/k933167h/AXQEOS

## Current implementation (verified by source inspection; external E2E pending)
TesterArmy sample -> POST /api/v1/reporter (token) -> deterministic assertion gate -> optional JEV/T2 model evaluation -> SQLite runs -> Outbox -> Plane/Kiwi/Langfuse adapter endpoints.
Critical or uncertain evaluations -> T3 review -> SME token-protected approval -> explicit Golden promotion.

The generic /api/v1/e2e/runs endpoint uses a separate deterministic routing function and does not invoke the model judge. Do not claim both endpoints have equivalent semantics.

## Trust boundaries
- Test evidence is untrusted; model verdicts are advisory.
- Missing model configuration must not be interpreted as a pass.
- Golden promotion requires an explicit SME decision; approval identity currently relies on a shared token and reviewer string and requires stronger identity controls before production.
- External endpoints and actual TesterArmy execution are not verified by repository-level tests.

## Planned ScientistTwo-inspired extension (NOT implemented)
Production failure -> Hypothesis Generator -> subset-first Experiment -> Ablation/Regression -> Independent Review -> SME Gate -> Versioned Golden -> Continuous Quality Monitoring.

No autonomous changes to production, Golden, or quality policies without authorized review.

## CI evidence gate
GitHub Actions runs pytest for the Reporter/SME workflow and archives JUnit XML plus console output as an Actions artifact. Passing this gate validates isolated API behavior, not actual TesterArmy browsers, remote judge services, or third-party integrations.

## Experimental quality loop (development branch, prototype)
Authenticated quality hypothesis records are linked to existing run IDs; experiments must reference a persisted test run and evidence URI; an SME-token-protected review records accept/reject/revise. This is a **manual orchestration prototype**, not an autonomous hypothesis generator, independent AI reviewer, ablation runner, or real TesterArmy executor. Accepted hypotheses never auto-promote Golden. The model judge failure path returns T3 review rather than HTTP 500 for recognized transport/parse failures.

## Native fallback algorithms (development branch)
app/quality_algorithms.py provides canonical SHA-256 evidence digests, stable risk-stratified subset selection, paired descriptive ablation deltas, and conservative multi-reviewer consensus. All are deterministic and usable without an external AI service. These are reusable primitives, **not yet wired into the production evaluation orchestrator**. Review IDs alone do not establish actual organizational or model independence. Evidence digests detect changes only against a trusted stored reference; they do not establish provenance. Ablation deltas are not causal estimates.

## Native algorithm API integration (development branch)
Authenticated /api/v1/quality endpoints expose evidence verification, subset selection, ablation delta, reviewer consensus, and persistent audit retrieval. Evidence and review audits are linked to run IDs in SQLite. Subset and ablation calls are currently stateless; the evaluation orchestrator does not automatically invoke them. Evidence verification accepts a caller-supplied reference digest and therefore does not independently establish trusted provenance. Reviewer IDs are self-declared; identity/model independence is not independently attested. No API here promotes Golden.

## Adaptive Orchestrator v1 integration
The generic POST /api/v1/e2e/runs path now invokes app/orchestrator.py for deterministic T0, risk/confidence T1/T2 referral, critical T3, budget cap and optional evidence digest verification. Estimated judge cost is an input estimate, not metered actual spend. T1/T2 are routing recommendations on this generic endpoint: actual judge HTTP execution remains in the separate Reporter path. This is not yet a unified executable cascade. Golden promotion remains a separate SME action.

## Unified evaluation service (development)
Both generic E2E ingestion and authenticated Reporter call app/evaluation_service.py. T0 deterministic gates precede model evaluation. T1/T2 model calls are attempted only with evidence text and allowed routing budget; absent model configuration returns review, not pass. Risk policy prevents a T1 verdict from overriding a required T2 path. Model transport/format failures fail closed to T3. The Reporter currently uses a heuristic confidence (0.7 with summary, 0.99 without); this is **not calibrated model confidence** and must be replaced. The judge evaluator may invoke both T1 and T2; estimated cost is not actual metered cost. External execution remains unverified.

## Judge Calibration and Economics primitives
app/judge_metrics.py computes Brier score and ECE from independently labeled confidence/correctness pairs, token-price cost from supplied actual usage, and Judge Cost / Cost per Correct Evaluation / False Accept / Critical False Accept rates. These functions do not fetch provider prices or create labels, and they are not yet wired to live judge telemetry. Do not interpret the presence of these calculations as proof of calibration. Reserve disjoint calibration and holdout datasets before enabling production thresholds.

## Judge telemetry ledger (development branch)
Model response usage (prompt/completion tokens), elapsed call time, model name and verdict flow through the shared evaluator to append-only SQLite judge_calls rows. An authenticated per-run endpoint reports recorded calls, known priced cost and number of unpriced calls. Provider pricing is not automatically configured; unpriced calls are explicitly marked unknown, not zero. Network errors currently may omit attempted-call telemetry; telemetry persistence is not atomic with run insertion. Do not claim complete billing or P95 monitoring. Calibration remains offline.
