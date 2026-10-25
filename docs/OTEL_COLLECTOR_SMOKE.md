# Phase 12 — real OTel Collector smoke (isolated)

This experiment starts an actual OpenTelemetry Collector 0.123.0 Docker image, sends an OTLP/HTTP JSON span over loopback, then checks the Collector debug exporter logs for a synthetic Trace ID and span name.

Files:
- `docker-compose.otel-smoke.yml`
- `lab/collector_live_smoke.py`
- `.github/workflows/otel-collector-smoke.yml`

Local use:
```bash
docker compose -f docker-compose.otel-smoke.yml up -d
python lab/collector_live_smoke.py
docker compose -f docker-compose.otel-smoke.yml logs otel-collector
docker compose -f docker-compose.otel-smoke.yml down -v
```

The workflow is dispatched manually or when its listed paths change in a PR. This is a **real collector container**, but it only uses a synthetic trace and its debug exporter. It does not establish production TLS, authentication, real Langfuse compatibility, durable collector retention or correlation with a live AX QE OS agent run. All CI findings remain pending until actual GitHub Actions logs are reviewed. The production outbox transport still requires HTTPS, and this smoke deliberately does not modify or bypass that requirement.
