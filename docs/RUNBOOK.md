# AX QE OS v4.9 Runbook — 2026-10-09
## 1. Scope and verified status
Source is committed. No successful end-to-end run has yet been demonstrated. CI outcome must be checked in GitHub Actions. The system is NOT approved for production.
## 2. Architecture Overview
TesterArmy e2e -> Reporter -> FastAPI -> SQLite -> T0 deterministic / T1 economical judge / T2 strong judge / T3 SME -> transactional-intent outbox -> Plane / Kiwi / Langfuse -> Grafana. OTel Collector configuration exists, but tracing is not yet instrumented. Golden promotion requires explicit SME approval.
## 3. Installation
Install Docker Compose. Copy .env.example to .env and replace placeholder values. Never paste real secrets into GitHub files or issue comments. Run docker compose config -q, then docker compose up --build -d. Inspect docker compose logs api worker. Check curl http://localhost:8080/health.
## 4. Secrets and access
GitHub Settings > Secrets and variables > Actions > New repository secret. Add AX_REPORTER_TOKEN, AX_SME_TOKEN, JEV_API_KEY, LLM_JUDGE_API_KEY, PLANE_API_KEY, KIWI_API_TOKEN, LANGFUSE_INGEST_TOKEN. Add non-secret endpoints and model identifiers as repository variables. For production prefer GitHub Environments with reviewer approval and an external Secret Manager via short-lived OIDC credentials. Never use a production key in PR CI. The connected GitHub API cannot create secrets automatically.
## 5. TesterArmy scenario
Run the sample reporter/testerarmy.spec.ts only after configuring a reachable test app and matching installed e2e SDK. The test sends the run outcome in finally. Verify the run ID in /api/v1/runs/{id}/persistent. The sample is not a validated SDK plugin.
## 6. Judge scenario
Configure JEV and strong judge endpoints. Missing judge configuration returns review. Validate pass, fail, low-confidence, model timeout, invalid JSON and critical-risk routing against a SME-reviewed dataset. Do not claim a genuine JEV model is integrated until its endpoint is verified.
## 7. Operations
Inspect /metrics and Grafana. The worker retries failed outbound requests up to six attempts. A queued record is not evidence of successful delivery. Inspect outbox states and remote IDs in SQLite. Confirm the real Plane, Kiwi and Langfuse API contracts.
## 8. Incident response
If secrets leak, revoke and rotate them; audit Actions and remote provider logs. For dead-letter outbox records, correct endpoint/credentials and implement controlled replay after checking idempotency. For false pass, suspend automation and escalate to SME.
## 9. Audit evidence
Preserve run_id, test_id, assertion outcome, Judge tier/verdict, reviewer, approval decision, Golden promotion, outbox delivery IDs, build SHA, workflow run URL and timestamp. Redact personal data and tokens.
## 10. Change management
For every change: code -> automated tests -> evidence -> Architecture Overview -> Runbook -> PR review. Keep docs/STATUS.md accurate. Never assert test success without a successful CI or execution log.
