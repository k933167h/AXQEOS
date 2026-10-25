# Leased Outbox Worker — experimental

Use lab.leased_outbox_worker.work_once(db, settings) on a persistent SQLite DB. Claiming uses BEGIN IMMEDIATE and a bounded lease; lost workers can be reclaimed after lease expiry. After five unsuccessful sends the event is marked dead and discoverable by dead_letters(db). No automatic dead-letter replay or operational alert is provided.

**Warnings:** A lease can expire while an HTTP call is still active, so deliveries remain at-least-once. The lease owner is not a full fencing token and external receivers must support idempotency. SQLite does not provide distributed locking across machines with independent DB copies. Legacy telemetry_outbox.drain bypasses the lease scheme and must not run concurrently with this worker. Use only this worker for pilot sends.

The test suite covers exclusive claims, rejected stale-worker completion, expiry reclaim and dead-letter transitions. CI and live Langfuse/OTel integration are not yet confirmed. Configure credentials only through secrets, require network restrictions, and do not deploy to production before security review.
