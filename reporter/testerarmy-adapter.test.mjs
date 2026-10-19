import test from 'node:test';
import assert from 'node:assert/strict';
import { reportTesterArmyOutcome, runWithReporting } from './testerarmy-adapter.mjs';

test('reports success with stable supplied run ID', async () => {
  let payload;
  await reportTesterArmyOutcome({
    testId: 'login', goal: 'Login succeeds', assertionPassed: true,
    externalRunId: 'run-1', transport: async x => { payload = x; }
  });
  assert.equal(payload.external_run_id, 'run-1');
  assert.equal(payload.assertion_passed, true);
});

test('rejects invalid risk', async () => {
  await assert.rejects(reportTesterArmyOutcome({
    testId: 'x', assertionPassed: false, risk: 2, transport: async () => {}
  }), RangeError);
});

test('retains test failure when reporting fails', async () => {
  const failure = new Error('assertion failed');
  await assert.rejects(runWithReporting(
    async () => { throw failure; },
    { testId: 'x', transport: async () => { throw new Error('network'); } }
  ), error => error === failure && error.reportingError.message === 'network');
});

test('fails closed if successful test cannot be reported', async () => {
  await assert.rejects(runWithReporting(async () => {}, {
    testId: 'x', transport: async () => { throw new Error('network'); }
  }), /network/);
});
