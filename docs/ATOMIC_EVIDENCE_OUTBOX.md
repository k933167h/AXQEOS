# Atomic evidence + telemetry outbox (pilot)

`lab.atomic_evidence_outbox.save_and_enqueue(db, event)` writes one evidence event and exactly two outbox records (OTLP and Langfuse) inside the **same SQLite transaction**. Duplicate event IDs roll back atomically. `lab.telemetry_outbox.drain` retries failed transmissions. GitHub CI includes tests covering duplicate rollback and HTTP 503 then success.

**Boundary:** Outbox delivery remains *at least once*, not exactly once. This is a single-process pilot without worker leases, claim tokens, dead-letter handling, end-to-end validation with a running Langfuse server or OTel Collector, credential provisioning, trace continuity verification, or WORM backup. Network egress and secrets require a hardened deployment. Do not activate in production.

Verification commands: `python -m pytest -q tests/test_atomic_evidence_outbox.py`. Require CI green and security review before using beyond isolated tests. Existing legacy `sqlite_evidence.append` does not enqueue telemetry by itself; callers must explicitly use the atomic entry point.
