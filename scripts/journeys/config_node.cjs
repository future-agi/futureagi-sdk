/* Installed-client credential probes; only ephemeral session-created fixture keys. */
const http = require('node:http');
const { randomBytes } = require('node:crypto');
function demand(value) { if (!value) throw new Error('Probe invariant failed'); }
function member(root, path) {
  const parts = path.split('.');
  for (const part of parts.slice(0, -1)) root = root[part];
  return root[parts.at(-1)].bind(root);
}
async function refused(action, classes) {
  try { await action(); } catch (error) { demand(classes.includes(error.constructor.name)); return; }
  throw new Error('Expected typed refusal');
}
async function run(check, skip, policy, sdk, load) {
  const session = randomBytes(18).toString('base64url');
  const api = 'personal-fixture-' + randomBytes(18).toString('base64url');
  const secret = randomBytes(24).toString('base64url');
  let minted = false;
  const requests = [];
  const server = http.createServer((req, res) => {
    req.resume();
    const reply = (status, payload) => {
      res.writeHead(status, { 'Content-Type': 'application/json' }); res.end(JSON.stringify(payload));
    };
    if (req.method === 'POST' && req.url === '/__fixture/session') return reply(200, { session });
    if (req.method === 'POST' && req.url === '/__fixture/personal-keys') {
      if (req.headers.authorization !== 'Bearer ' + session) return reply(403, {});
      minted = true; return reply(201, { api_key: api, secret_key: secret, type: 'user' });
    }
    requests.push({ path: req.url, headers: req.headers });
    if (req.url.startsWith('/accounts/keys/')) return reply(410, {});
    if (!minted || req.headers['x-api-key'] !== api || req.headers['x-secret-key'] !== secret) return reply(403, { detail: 'Personal credentials required' });
    if (req.url.startsWith('/accounts/user-info/')) return reply(200, { id: 'fixture-person', email: 'person@example.invalid' });
    return reply(200, { status: 'success', result: [], data: [], items: [], results: [], count: 0 });
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const url = `http://127.0.0.1:${server.address().port}`;
  try {
    const sessionBody = await (await fetch(url + '/__fixture/session', { method: 'POST' })).json();
    const pair = await (await fetch(url + '/__fixture/personal-keys', { method: 'POST', headers: { Authorization: 'Bearer ' + sessionBody.session } })).json();
    demand(pair.type === 'user');
    Object.assign(process.env, { FI_API_KEY: api, FI_SECRET_KEY: secret, FI_BASE_URL: url, FI_PLATFORM_BASE_URL: url + '/omega/api' });
    const client = new sdk.FutureAGIClient();
    async function request(path, args = []) {
      const before = requests.length;
      await member(client, path)(...args);
      demand(requests.length === before + 1);
      const headers = requests.at(-1).headers;
      demand(headers['x-api-key'] === api && headers['x-secret-key'] === secret && !headers.authorization);
    }
    await check('config.default-client', () => request('users.current'));
    await check('config.platform-origin-headers', () => request('_platform.call', ['platform.capabilities.get']));
    for (const call of policy.config_calls.ts) await check('config.namespace.' + call.path, () => request(call.path, call.args));
    const before = requests.length;
    await check('config.mixed-credentials', () => refused(() => new sdk.FutureAGIClient({ platformToken: 'fixture-selfhost-token' })._platform.call('platform.capabilities.get'), ['MixedCredentialsError']));
    await check('config.unsafe-origin', () => refused(() => new sdk.FutureAGIClient({ platformBaseUrl: 'https://untrusted.invalid/omega/api' })._platform.call('platform.capabilities.get'), ['HostNotAllowedError']));
    await check('config.no-mixed-key-sources', () => refused(() => new sdk.FutureAGIClient({ apiKey: api, baseUrl: url }).users.current(), ['CredentialsMissingError', 'MissingAuthError']));
    await check('config.negatives-no-request', () => demand(requests.length === before));
    await check('config.argument-precedence', async () => {
      Object.assign(process.env, { FI_API_KEY: 'conflicting-fixture-api', FI_SECRET_KEY: 'conflicting-fixture-secret' });
      try {
        const explicit = new sdk.FutureAGIClient({ apiKey: api, secretKey: secret, baseUrl: url });
        const before = requests.length;
        await explicit.users.current();
        demand(requests.length === before + 1);
        const headers = requests.at(-1).headers;
        demand(headers['x-api-key'] === api && headers['x-secret-key'] === secret);
      } finally { Object.assign(process.env, { FI_API_KEY: api, FI_SECRET_KEY: secret }); }
    });
    if (policy.states.gateway.ts === 'ON') {
      await check('config.fi-pair-not-gateway', async () => {
        const { AgentCC } = await load('@future-agi/sdk/gateway');
        for (const key of [api, secret]) await refused(() => new AgentCC({ apiKey: key, baseUrl: url }), ['AgentCCError']);
      });
    } else skip('config.fi-pair-not-gateway', 'Gateway data-plane namespace OFF; absence checked separately');
    if (policy.states.gateway_management.ts === 'ON') {
      await check('config.virtual-key-not-management', async () => {
        const before = requests.length;
        const c = new sdk.FutureAGIClient({ apiKey: 'sk-agentcc-fixture-only', secretKey: 'fixture-only', baseUrl: url });
        await refused(() => c.gateway.config.getActive(), ['ConfigurationError', 'AuthError', 'CredentialsMissingError', 'AuthenticationError']);
        demand(requests.length === before);
      });
    } else skip('config.virtual-key-not-management', 'Gateway management namespace OFF; absence checked separately');
    await check('config.no-retired-key-route', () => demand(!requests.some(r => r.path.startsWith('/accounts/keys/'))));
  } finally {
    server.closeAllConnections();
    await new Promise(resolve => server.close(resolve));
  }
}
module.exports = { run, demand };
