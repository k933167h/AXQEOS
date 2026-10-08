# v4.9 Integration validation matrix
| Component | Contract/mock coverage | Real service status |
| --- | --- | --- |
| TesterArmy | Reporter sample exists; no SDK contract test | NOT VERIFIED |
| JEV economical judge | HTTP chat completion response, low-confidence escalation | NOT VERIFIED |
| Strong LLM judge | HTTP chat completion and verdict | NOT VERIFIED |
| Kiwi TC | Generic adapter URL POST with auth/idempotency | Direct Kiwi JSON-RPC NOT IMPLEMENTED |
| Langfuse | Generic adapter URL POST with auth/idempotency | Direct Langfuse ingestion NOT IMPLEMENTED |
| Plane | Generic issue POST with auth/idempotency | Actual tenant NOT VERIFIED |
| OpenTelemetry | Semantic convention YAML only | Span export NOT IMPLEMENTED |
| Persistence | SQLite + SME approval + outbox tests | Production database NOT VERIFIED |
The mocked integration tests verify application HTTP request shapes and fail/retry logic only. They do not prove the upstream services' contracts or credential validity.
## Gate to real end-to-end validation
1. Pin the TesterArmy/e2e package and exact supported test completion hook.
2. Provision sandbox API credentials in GitHub integration environment (never commit them).
3. Implement direct Kiwi JSON-RPC and Langfuse event ingestion against vendor API documentation.
4. Instrument reporter, judge and worker spans; verify collector receives correlated trace IDs.
5. Run a sandbox E2E workflow and attach redacted remote IDs, trace IDs, test counts and logs.
6. Update Architecture Overview, Runbook and STATUS.md before production signoff.
