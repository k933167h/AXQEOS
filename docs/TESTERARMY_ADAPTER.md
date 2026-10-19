# TesterArmy Adapter v1 — implementation and validation

## Architecture
TesterArmy test body -> `runWithReporting` -> `reportTesterArmyOutcome` -> existing `reporter.mjs` -> authenticated AX QE OS Reporter API -> persistence -> Judge.

This integration deliberately does **not** assume a TesterArmy onTestEnd/afterEach hook. Use the wrapper in an explicit test body. This adapter does not install or execute the upstream browser engine.

## Runbook
1. Install Node.js 20+ and configure the existing AX QE OS API and `AX_REPORTER_TOKEN` using a local secrets manager.
2. Run `node --test reporter/testerarmy-adapter.test.mjs`.
3. Start AX QE OS according to `docs/RUNBOOK.md`, then set `AXQEOS_URL` and `AX_REPORTER_TOKEN`.
4. Install and initialize TesterArmy from its pinned official release in a separate test project. Verify the installed SDK's `test`, `app`, `agent`, and `screen` interfaces.
5. Invoke `runWithReporting(async () => { /* test steps */ }, {testId:'smoke',goal:'homepage visible'})` from a TesterArmy test body.
6. Verify the returned persistent run using the AX QE OS API and confirm the assertion and Judge results.

## Acceptance checks
- Explicit true/false/null outcomes and risk bounds.
- Unique default external run ID, or caller-supplied stable ID for retries.
- Original assertion error remains primary if result delivery also fails.
- Reporting failure after a passing test fails the test.
- Do not transmit credentials, screenshots, or sensitive data in evidence summaries.
- No production readiness claim until real browser run, CI, replay behavior and endpoint validation succeed.

## Current limitations
No upstream browser execution, actual SDK integration test, outbox replay, mobile device test or OpenTelemetry SDK span export has been demonstrated. Transport errors are not automatically retried by this adapter.
