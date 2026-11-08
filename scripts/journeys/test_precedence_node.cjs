/* Exercise the actual assertion, not a copy, with incorrect credential resolvers. */
const assert = require('node:assert/strict');
const { run } = require('./config_node.cjs');
async function outcome(ignored) {
  class Client {
    constructor(options = {}) {
      const api = ignored.includes('api') ? process.env.FI_API_KEY : options.apiKey ?? process.env.FI_API_KEY;
      const secret = ignored.includes('secret') ? process.env.FI_SECRET_KEY : options.secretKey ?? process.env.FI_SECRET_KEY;
      const url = options.baseUrl ?? process.env.FI_BASE_URL;
      this.users = { current: async () => {
        const response = await fetch(url + '/accounts/user-info/', { headers: { 'X-Api-Key': api, 'X-Secret-Key': secret } });
        await response.text(); // Deliberately ignore status to test both header assertions.
      } };
    }
  }
  let state;
  await run(async (name, action) => {
    if (name !== 'config.argument-precedence') return;
    try { await action(); state = 'PASS'; } catch { state = 'FAIL'; }
  }, () => {}, { config_calls: { ts: [] }, states: { gateway: { ts: 'OFF' }, gateway_management: { ts: 'OFF' } } }, { FutureAGIClient: Client });
  return state;
}
(async () => {
  assert.equal(await outcome([]), 'PASS');
  for (const ignored of [['api'], ['secret'], ['api', 'secret']]) {
    assert.equal(await outcome(ignored), 'FAIL', `Environment snapshot must fail: ${ignored}`);
  }
  console.log('Correct resolver passed; all three environment-snapshot mutants failed');
})().catch(error => { console.error(error); process.exitCode = 1; });
