# Observability HTTP Contract Smoke

The existing `tests/test_observability_contract.py` checks the full local path: atomic SQLite evidence persistence → leased worker → HTTP request serialization → mocked OTLP and Langfuse receivers. It asserts the shared trace ID, evidence event ID and hash and that both outbox entries become `sent`. Its second test returns HTTP 503 from the Langfuse mock and asserts the evidence remains valid and only that destination is left pending for retry.

Run: `python -m pytest -q tests/test_observability_contract.py`. GitHub Actions now includes this test.

**Boundary:** These are mocked HTTP receivers, not real Langfuse/Collector services. A mock 200 response cannot establish compatibility with installed service versions, backend ingestion acknowledgement, real data retention, duplicate suppression, authentication configuration, or network security. All live credentials belong in GitHub Secrets or external secret management. No measured AI performance improvement is claimed.
