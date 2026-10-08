# AX QE OS v4.9 integration contract
## Reporter
Invoke reporter/report() in the test runner's supported completion hook. The hook name/API depends on the installed TesterArmy version; this is a generic adapter, not a verified TesterArmy plugin. Use a unique external_run_id for retry-safe submissions.
## Judges
JEV_BASE_URL, JEV_API_KEY, JEV_MODEL and LLM_JUDGE_BASE_URL, LLM_JUDGE_API_KEY, LLM_JUDGE_MODEL point to OpenAI-compatible chat completion endpoints. Calls are real HTTP requests when configured; without credentials the outcome is review, not pass. An actual JEV implementation must expose that API or have a custom adapter.
## Persistence
SQLite uses AX_DB_PATH, defaults to /data/axqeos.sqlite3. Mount /data as a persistent Docker volume. For multi-worker deployment replace SQLite with PostgreSQL and implement transactional outbox delivery.
## Human approval
AX_SME_TOKEN authorizes POST /api/v1/runs/{id}/approval. Approvals are auditable records, not automatic Golden Dataset promotion. Golden promotion requires separate SME-curated dataset workflow.
## External adapters
The outbox records destinations for Plane/Kiwi/Langfuse; delivery worker, API mappings, retry/backoff and credential management remain to be implemented. Do not claim delivery from a queued record.
## Security
Never commit tokens. Avoid uploading PII/PHI into evidence_summary. Set API access controls and TLS before production use.
