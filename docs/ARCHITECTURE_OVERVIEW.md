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
