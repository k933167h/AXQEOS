# AX QE OS v4.9 — Local Integration Lab Runbook
## Scope
Runs a real FastAPI server, SQLite, outbox worker, Prometheus, Grafana, an OTel Collector and simulated upstream HTTP endpoints. JEV, LLM Judge, Plane, Kiwi and Langfuse responses are **simulated**. No real TesterArmy browser automation or vendor deployment is included.
## Quick start
1. Install Docker Engine and Docker Compose.
2. Copy .env.lab.example to .env.lab and replace placeholder tokens.
3. Run: `docker compose --env-file .env.lab -f docker-compose.yml -f docker-compose.lab.yml up --build -d`
4. Run: `docker compose --env-file .env.lab -f docker-compose.yml -f docker-compose.lab.yml --profile smoke run --rm smoke`
5. Inspect: `docker compose --env-file .env.lab -f docker-compose.yml -f docker-compose.lab.yml logs --tail=100 api worker mock-services otel-collector`
6. Stop: `docker compose --env-file .env.lab -f docker-compose.yml -f docker-compose.lab.yml down`.
## Validation gates
The smoke run must print PASS with scope LOCAL_SIMULATION_ONLY. This verifies a real HTTP round-trip through Reporter and judge mock, not model accuracy. To verify worker delivery, submit a failing reporter run and check SQLite outbox delivery state and mock service logs. To verify OTel, first instrument application spans: collector readiness alone does not establish end-to-end traces.
## Real product integration
TesterArmy: install the actual supported SDK and execute a browser against a controlled app. JEV/LLM: configure real sandbox inference endpoints and review calibration dataset. Kiwi: implement direct JSON-RPC integration and confirm remote test result ID. Langfuse: implement direct ingestion and verify trace ID. OTel: instrument FastAPI, httpx and worker and confirm correlated trace export. These remain unverified.
## Security
This repository is public. Never commit production API keys, secrets, PHI, real evidence or .env.lab. Use GitHub Environments and a Secret Manager for actual external endpoints.
## Operations
Maintain docs/ARCHITECTURE_OVERVIEW.md and docs/RUNBOOK.md alongside implementation changes. Never mark mock test as real-service validation.
