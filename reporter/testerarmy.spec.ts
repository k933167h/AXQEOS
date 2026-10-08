// Example TesterArmy integration: explicit after-test reporting without relying on undocumented hooks.
// Run this with your installed e2e CLI after configuring the app and credentials.
import { test, expect } from 'e2e';
test('AXQEOS reporter integration', async ({ app, agent, screen }) => {
  const external_run_id = 'testerarmy-' + crypto.randomUUID();
  let assertion_passed: boolean | null = null;
  try {
    await app.open('/');
    await agent.act('Inspect the homepage and locate its primary heading');
    await expect(screen.getByRole('heading').first()).toBeVisible();
    assertion_passed = true;
  } catch (error) {
    assertion_passed = false;
    throw error;
  } finally {
    const result = await fetch(process.env.AXQEOS_URL + '/api/v1/reporter', {
      method: 'POST',
      headers: {'Content-Type':'application/json','X-AX-Reporter-Token':process.env.AX_REPORTER_TOKEN || ''},
      body: JSON.stringify({external_run_id,test_id:'homepage-heading',goal:'primary heading visible',risk:0.2,assertion_passed})
    });
    if (!result.ok) throw new Error('AXQEOS report failed: ' + result.status);
  }
});
