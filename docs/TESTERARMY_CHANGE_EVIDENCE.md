# TesterArmy Reporter v1 — Change evidence

## Architecture Overview addendum
TesterArmy test -> explicit runWithReporting wrapper -> normalized payload -> existing authenticated /api/v1/reporter -> SQLite persistence -> T0–T3 routing.

No undocumented upstream hook is assumed. The wrapper preserves original test failures and surfaces reporting failures. Reporter idempotency is provided by the existing API's external_run_id handling.

## Evidence checklist
- Source reviewed: reporter/reporter.mjs, reporter/testerarmy.spec.ts, app/orchestrator.py, docs/STATUS.md and docs/RUNBOOK.md on main.
- New source: reporter/testerarmy-adapter.mjs.
- New deterministic tests: reporter/testerarmy-adapter.test.mjs.
- Operational runbook: docs/TESTERARMY_ADAPTER.md.
- Local tests: NOT RUN through GitHub connector.
- CI status: NOT YET VERIFIED.
- Actual TesterArmy browser and mobile execution: NOT VERIFIED.
- External integrations: NOT VERIFIED.

## Release gate
Do not merge before Node contract tests and existing Python tests pass, documentation review, and confirmation of GitHub Actions results.
