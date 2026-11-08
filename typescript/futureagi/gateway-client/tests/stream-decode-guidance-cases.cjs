// Offline source and dual-build regressions; all payloads and credentials are synthetic.
const assert = require('node:assert/strict');
const ID = '01ARZ3NDEKTSV4RRFFQ69G5FAV';
const REQUEST = { method: 'POST', path: '/v1/chat/completions', body: { model: 'example/model', messages: [] } };
const GUIDANCE = 'The gateway did not confirm whether the request was applied; check whether it was applied before sending it again.';
const CHUNK = { id: 'synthetic', object: 'chat.completion.chunk', created: 0, model: 'example/model', choices: [{ index: 0, delta: { content: 'partial' }, finish_reason: null }] };
const FIXTURES = [
  { name: 'malformed JSON', type: 'application/json', text: '{broken}', message: 'Failed to parse JSON answer: {broken}' },
  { name: 'non-object JSON', type: 'application/json', text: '42', message: 'Failed to parse JSON answer: 42' },
  { name: 'malformed SSE', type: 'text/event-stream', text: 'data: {broken}\n\n', message: 'Failed to parse SSE data: {broken}' },
  { name: 'array JSON', type: 'application/json', text: '[]', message: 'Failed to parse JSON answer: []' },
  { name: 'non-object SSE', type: 'text/event-stream', text: 'data: null\n\n', message: 'Failed to parse SSE data: null' },
];

function setup(api, status, dispatch, type, text, policy = true) {
  let calls = 0;
  const retries = [];
  class Observer extends api.CallbackHandler {
    onRetry(_request, error) { retries.push(error); }
  }
  const headers = { 'content-type': type, 'x-agentcc-request-id': ID, 'x-agentcc-client-request-id': 'correlation' };
  if (dispatch !== null) headers['x-agentcc-dispatched'] = dispatch;
  const response = new Response(text, { status, headers });
  const client = new api.AgentCC({
    apiKey: 'synthetic-key', baseUrl: 'https://gateway.test', maxRetries: 3,
    ...(policy ? { retryPolicy: new api.RetryPolicy({ connectionErrorRetries: 5, timeoutRetries: 5 }) } : {}),
    callbacks: [new Observer()], fetch: async () => { calls++; return response; },
  });
  return { client, response, assertTerminal() { assert.equal(calls, 1); assert.equal(retries.length, 0); } };
}

function checkEvidence(api, error, response, dispatch) {
  assert.ok(error instanceof api.StreamError);
  assert.equal(error.name, 'StreamError');
  assert.equal(error.gatewayEvidence, api.getGatewayEvidence(response));
  assert.ok(Object.isFrozen(error.gatewayEvidence));
  assert.deepEqual(error.gatewayEvidence, {
    dispatched: dispatch === 'true' ? true : dispatch === 'false' ? false : 'unknown',
    gatewayRequestId: ID, clientRequestId: 'correlation',
  });
  assert.equal(error.cause, undefined);
}

async function checkDecode(api, fixture, status, dispatch, policy = true, partial = false) {
  const text = (partial ? `data: ${JSON.stringify(CHUNK)}\n\n` : '') + fixture.text;
  const run = setup(api, status, dispatch, fixture.type, text, policy);
  const raw = await run.client.requestStream(REQUEST);
  const stream = new api.Stream(raw);
  // Error reconstruction must use the captured owner, not mutable headers.
  raw.headers.set('x-agentcc-dispatched', dispatch === 'true' ? 'false' : 'true');
  raw.headers.set('x-agentcc-request-id', 'mutated');
  const chunks = [];
  let error;
  try { for await (const chunk of stream) chunks.push(chunk); } catch (caught) { error = caught; }
  checkEvidence(api, error, raw, dispatch);
  run.assertTerminal();
  assert.equal(chunks.length, partial ? 1 : 0);
  if (partial) assert.equal(chunks[0].choices[0].delta.content, 'partial');
  for (const field of ['type', 'code', 'param', 'body']) assert.equal(error[field], null);
  const unknown = dispatch === null || dispatch === 'False';
  assert.equal(error.message, fixture.message + (unknown ? `. ${GUIDANCE}` : ''));
  assert.equal(error.remedy, unknown ? GUIDANCE : null);
}

function registerCases(api, test) {
  for (const fixture of FIXTURES) for (const status of [200, 246]) for (const dispatch of [null, 'False', 'true', 'false']) {
    test(`${fixture.name}: ${status} dispatch ${dispatch}`, () => checkDecode(api, fixture, status, dispatch));
  }
  for (const status of [200, 246]) for (const dispatch of [null, 'False']) for (const policy of [false, true]) {
    test(`partial SSE: ${status} dispatch ${dispatch} policy ${policy}`, () => checkDecode(api, FIXTURES[2], status, dispatch, policy, true));
  }
  // Gateway frames retain precedence even when their message resembles an SDK failure,
  // or when a non-object error value has no body/type/code fields to distinguish it.
  for (const type of ['application/json', 'text/event-stream']) for (const status of [200, 246]) for (const dispatch of [null, 'False']) {
    for (const body of [{ message: 'Failed to parse SSE data: {broken}', type: 'gateway_timeout', code: 'managed_billing_unavailable', param: 'model' }, 'Failed to parse JSON answer: 42', 42]) {
      test(`gateway frame: ${type} ${status} dispatch ${dispatch} error ${typeof body}`, async () => {
        const payload = JSON.stringify({ error: body });
        const run = setup(api, status, dispatch, type, type === 'application/json' ? payload : `data: ${payload}\n\n`);
        const raw = await run.client.requestStream(REQUEST);
        await assert.rejects(async () => { for await (const _chunk of new api.Stream(raw)) { /* consume */ } }, error => {
          checkEvidence(api, error, raw, dispatch);
          assert.equal(error.message, typeof body === 'object' ? body.message : typeof body === 'string' ? body : 'Stream error: 42');
          assert.equal(error.remedy, null);
          assert.deepEqual(error.body, typeof body === 'number' ? null : body);
          for (const field of ['type', 'code', 'param']) assert.equal(error[field], typeof body === 'object' ? body[field] : null);
          return true;
        });
        run.assertTerminal();
      });
    }
  }
  for (const method of ['requestRaw', 'requestStream']) for (const fixture of [FIXTURES[0], FIXTURES[2]]) {
    test(`${method}: caller owns ${fixture.name} decoding`, async () => {
      const run = setup(api, 200, null, fixture.type, fixture.text);
      const raw = await run.client[method](REQUEST);
      assert.equal(await raw.text(), fixture.text);
      run.assertTerminal();
    });
  }
}
module.exports = { registerCases };
