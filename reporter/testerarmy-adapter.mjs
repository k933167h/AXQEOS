import { randomUUID } from 'node:crypto';
import { report } from './reporter.mjs';

/**
 * Report an E2E outcome without assuming undocumented TesterArmy lifecycle hooks.
 * Use in a test's finally block. Inject transport for deterministic unit tests.
 */
export async function reportTesterArmyOutcome({
  testId, goal, risk = 0.5, assertionPassed, evidenceUri = null,
  evidenceSummary = '', externalRunId = `testerarmy-${randomUUID()}`,
  transport = report
}) {
  if (typeof testId !== 'string' || !testId.trim()) throw new TypeError('testId required');
  if (assertionPassed !== true && assertionPassed !== false && assertionPassed !== null)
    throw new TypeError('assertionPassed must be true, false, or null');
  if (!Number.isFinite(risk) || risk < 0 || risk > 1) throw new RangeError('risk must be 0..1');
  return transport({
    external_run_id: externalRunId, test_id: testId, goal, risk,
    assertion_passed: assertionPassed, evidence_uri: evidenceUri,
    evidence_summary: evidenceSummary
  });
}

/** Preserve the original test error if reporting also fails. */
export async function runWithReporting(run, options) {
  let outcome = null;
  let originalError;
  try {
    await run();
    outcome = true;
  } catch (error) {
    originalError = error;
    outcome = false;
  }
  try {
    await reportTesterArmyOutcome({ ...options, assertionPassed: outcome });
  } catch (reportError) {
    if (originalError) {
      originalError.reportingError = reportError;
      throw originalError;
    }
    throw reportError;
  }
  if (originalError) throw originalError;
}
