# SQLite Evidence Storage — Phase 8

This pilot module persists event envelopes with SQLite WAL and a transactional, hash-linked sequence. Required IDs: event_id, case_id, kind, trace_id, commit_sha, artifact_digest. Optional span_id and metadata. Use stable trace IDs from OTel and external observation URLs or digests as metadata only; do not record code, credentials, or hidden ground truth.

`python -m lab.sqlite_evidence append --db /secure/evidence.sqlite3 --input local_event.json`
`python -m lab.sqlite_evidence verify --db /secure/evidence.sqlite3`

Example: `{"event_id":"EVT-1","case_id":"CASE-1","kind":"review","trace_id":"otel-trace-id","span_id":"span-id","commit_sha":"immutable-sha","artifact_digest":"sha256:abcd","metadata":{"external_system":"langfuse","observation_id":"id","gate":"hold"}}`

The persisted hash chain can detect edits to rows when verified, but it **is not immutable**: a privileged writer can rewrite the entire chain, or delete the database. Backups, retention, filesystem ACLs, signatures, encryption, concurrency/load validation, external trace export and WORM storage are necessary before regulated production use. There is no live Langfuse / OTel API call in this version.

Do not confuse persistent storage tests with proven external integration or measured engineering productivity.
