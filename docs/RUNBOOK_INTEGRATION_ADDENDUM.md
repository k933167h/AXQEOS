# Runbook update: Integration test procedure
## Purpose
Validate Reporter -> persistence -> T0/T1/T2/T3 -> outbound outbox without disclosing API credentials.
## Local contract test
Install requirements.txt and run `python -m pytest -q tests/test_integration_contract.py`. Tests use httpx.MockTransport and SQLite temporary directories; **they do not connect to actual TesterArmy, JEV, Kiwi, Langfuse or OTel**.
## CI evidence
Read the PR's GitHub Actions `tests` job for assertion counts. Security `dependency-audit` is separate.
## Real sandbox verification
Configure GitHub Environment `integration` with protected secrets. Do not run against production without service-specific adapters, trace instrumentation, approvals, and privacy review.
## Incident handling
Judge unavailable -> review; upstream delivery failure -> retry/outbox; repeated failure -> dead letter. A delivery attempt is not an accepted remote record until a remote ID and expected status are verified.
## Architecture status
This change adds mocked integration contract tests only. No changes to the v4.9 tier architecture. Direct vendor integrations and actual browser execution remain pending.
