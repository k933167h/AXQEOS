# Pilot Evidence Registry and manual promotion gate

This opt-in, local pilot prototype records evidence events in a hash-chained JSONL file. Each entry includes a UTC time, prior SHA256, and current SHA256. It detects casual historical modification during later appends; it is **NOT immutable audit storage** and can be rewritten by anyone with filesystem access. Do not use it as a regulated system of record.

`python -m lab.evidence_registry record --input event.json --registry /secure/pilot/events.jsonl`

Event shape example: `{"case_id":"C1","kind":"review","commit_sha":"...","trace_id":"...","artifact_digest":"..."}`. Store only metadata/digests and private links, never secrets, raw source code or protected defect labels. Use access-controlled durable DB/object storage, immutable retention, writer locking, event signatures and Langfuse/OTel linkage before production.

For pilot promotion, gather **real** independently adjudicated paired measurements and verified controls (CI, sandbox, live model CLI, statistical review, SME approval). Then:

`python -m lab.evidence_registry decision --input paired.json --controls controls.json --output decision.json`

All five controls must be explicitly true. At least 20 paired cases, positive recall delta and human-time reduction, and no aggregate increase in false-positive count are also required for **eligibility**, not deployment. Operator confirmation is always separate. Small samples or undocumented improvements result in HOLD. Real CI and model execution have not yet been verified.
