# CI validation — AX QE OS v4.9
## Scope
The required tests job runs compileall, pytest and docker compose config validation. It uses no production secrets. A separate dependency-audit job reports known vulnerabilities but is explicitly non-gating until dependency remediation; a green tests job does not mean vulnerability-free.
## Why this change
Isolate dependency security findings from functional CI, ensure tests use temporary isolated SQLite database via monkeypatch, and retain an optional integration secret-presence check. The integration job is NOT an actual external E2E test.
## How to verify
Open GitHub Actions > AXQEOS CI > latest pull_request run. Inspect tests job steps and dependency-audit job independently. Do not merge if tests fails. If audit reports vulnerabilities, create a remediation issue and fix them before production approval.
## Evidence
No successful GitHub Actions run has been observed at authoring time. Add run URL, SHA, test counts, failures and remediation here after actual run.
## Runbook update
Architecture Overview unchanged: TesterArmy -> Reporter -> T0/T1/T2/T3 -> Outbox -> Plane/Kiwi/Langfuse. CI changes are validation-only. Production approval still blocked on external integrations and real E2E.
