// Offline regressions shared by source, CJS and ESM runs. Synthetic values only.
const assert = require('node:assert/strict');
const ID = '01ARZ3NDEKTSV4RRFFQ69G5FAV';
const SECRET = 'synthetic-transport-credential';
const GUIDANCE = 'The gateway did not confirm whether the request was applied; check whether it was applied before sending it again.';
const REQUEST = { method: 'POST', path: '/v1/chat/completions', body: { model: 'example/model', messages: [] } };
const NAMES = ['authorization', 'proxy-authorization', 'cookie', 'set-cookie', 'x-api-key', 'api-key', 'x-goog-api-key', 'x-agentcc-config', 'x-auth-token', 'x-access-token', 'x-api-token', 'x-agentcc-api-key', 'x-agentcc-session-id', 'x-agentcc-session-name', 'x-agentcc-session-path'];
const suppliedHeaders = () => Object.fromEntries(NAMES.filter(n => n !== 'authorization').map(n => [n.toUpperCase(), SECRET]));
const headersFor = (status, dispatch, type) => ({ status, headers: { 'content-type': type, 'x-agentcc-request-id': ID, ...(dispatch === null ? {} : { 'x-agentcc-dispatched': dispatch }) } });
const options = (api, policy) => ({ apiKey: SECRET, sessionId: SECRET, baseUrl: 'https://gateway.test', maxRetries: 2, ...(policy ? { retryPolicy: new api.RetryPolicy({ connectionErrorRetries: Infinity, timeoutRetries: Infinity, internalServerErrorRetries: 2 }) } : {}) });

// Include non-enumerable Error.cause and symbol keys, not only JSON.stringify.
function inspect(value, seen = new Set()) {
  if (!value || (typeof value !== 'object' && typeof value !== 'function')) return String(value);
  if (seen.has(value)) return '';
  seen.add(value);
  if (value instanceof Headers) return JSON.stringify([...value]);
  return Reflect.ownKeys(value).map(k => String(k) + inspect(value[k], seen)).join(' ');
}
function assertScrubbed(init) {
  for (const [name, value] of Object.entries(init.headers)) {
    if (NAMES.includes(name.toLowerCase())) assert.equal(value, '[REDACTED]', `retained ${name}`);
  }
  assert.equal(init.headers.Accept, 'application/json');
}
function assertGuidance(error, dispatch) {
  const unknown = dispatch === null || dispatch === 'False';
  assert.equal(error.message.split(GUIDANCE).length - 1, unknown ? 1 : 0);
  assert.equal(error.remedy ?? null, unknown ? GUIDANCE : null);
}
async function consume(api, client, method) {
  if (method.startsWith('stream-')) {
    for await (const _chunk of new api.Stream(await client.requestStream(REQUEST))) { /* consume */ }
  } else await client[method](REQUEST);
}
async function caught(action) {
  try { await action(); } catch (error) { return error; }
  assert.fail('Expected a terminal failure');
}

function registerCases(api, test, routeStream) {
  for (const method of ['request', 'requestWithResponse', 'stream-json', 'stream-sse']) {
    for (const status of [200, 246]) for (const dispatch of [null, 'False', 'false', 'true']) for (const policy of [false, true]) for (const binding of ['unbound', 'evidence', 'public-option']) {
      test(`R1 retained init: ${method} ${status} ${dispatch} policy=${policy} ${binding}`, async () => {
        let response, original, init, calls = 0, pulls = 0;
        const callbacks = [], retries = [];
        const callerHeaders = suppliedHeaders();
        class Observer extends api.CallbackHandler {
          onError(request, error) { callbacks.push({ request, error }); }
          onRetry(request, error) { retries.push({ request, error }); }
        }
        const type = method === 'stream-sse' ? 'text/event-stream' : 'application/json';
        const client = new api.AgentCC({ ...options(api, policy), defaultHeaders: callerHeaders, callbacks: [new Observer()], fetch: async (_url, sent) => {
          calls++; init = sent;
          assert.equal(sent.headers.Authorization, `Bearer ${SECRET}`);
          const body = new ReadableStream({ pull(controller) {
            if (pulls++ === 0) {
              controller.enqueue(new TextEncoder().encode(type === 'application/json' ? '{' : 'data: {"choices":[{"index":0,"delta":{"content":"partial"},"finish_reason":null}]}\n\n'));
              return;
            }
            original = new api.StreamError('synthetic normalized reader abort', binding === 'unbound' ? {} : {
              gatewayEvidence: api.getGatewayEvidence(response), bodyReadFailure: binding === 'public-option',
            });
            Object.defineProperty(original, 'cause', { value: { request: init }, enumerable: false });
            controller.error(original);
          } });
          response = new Response(body, headersFor(status, dispatch, type));
          return response;
        } });
        const error = await caught(() => consume(api, client, method));
        assert.equal(calls, 1); assert.equal(retries.length, 0);
        assert.ok(error instanceof (method.startsWith('stream-') ? api.StreamError : api.ResponseBodyError));
        assert.equal(error.gatewayEvidence, api.getGatewayEvidence(response));
        assert.ok(Object.isFrozen(error.gatewayEvidence));
        assert.equal(inspect(error).includes(SECRET), false, 'SDK error must not retain credentials');
        assert.equal(inspect(callbacks).includes(SECRET), false, 'onError arguments must not retain credentials');
        assertScrubbed(init);
        assert.notEqual(error, original, 'Public class/evidence/options cannot establish trusted origin');
        if (method.startsWith('stream-')) assert.equal(error.cause, original, 'Retain the normalized reader cause only after transport scrubbing');
        else { assert.equal(callbacks.length, 1); assert.equal(callbacks[0].error, error); }
        assertGuidance(error, dispatch);
        assert.deepEqual(callerHeaders, suppliedHeaders(), 'Do not scrub caller-owned options');
      });
    }
  }
  for (const method of ['request', 'requestWithResponse', 'requestRaw', 'requestStream']) for (const policy of [false, true]) for (const failure of ['503', 'connect']) {
    test(`R2 retry sends real credentials: ${method} policy=${policy} ${failure}`, async () => {
      const sent = [], observed = [], callbacks = [];
      const callerHeaders = suppliedHeaders();
      class Observer extends api.CallbackHandler {
        onError(request, error) { callbacks.push({ request, error }); }
        onRetry(request, error) { callbacks.push({ request, error }); assertScrubbed(sent[0]); }
      }
      const client = new api.AgentCC({ ...options(api, policy), defaultHeaders: callerHeaders, callbacks: [new Observer()], fetch: async (_url, init) => {
        sent.push(init); observed.push({ ...init.headers });
        if (sent.length === 1) {
          if (failure === 'connect') throw Object.assign(new Error('synthetic refused'), { code: 'ECONNREFUSED', request: init });
          return new Response('{"message":"synthetic unavailable"}', { status: 503, headers: { 'x-agentcc-dispatched': 'false', 'retry-after': '0.001' } });
        }
        return new Response('{}');
      } });
      await client[method](REQUEST);
      assert.equal(sent.length, 2);
      assert.notEqual(sent[0], sent[1]); assert.notEqual(sent[0].headers, sent[1].headers);
      for (const headers of observed) {
        assert.equal(headers.Authorization, `Bearer ${SECRET}`);
        for (const name of Object.keys(callerHeaders)) assert.equal(headers[name], SECRET);
        assert.equal(headers['x-agentcc-session-id'], SECRET);
      }
      sent.forEach(assertScrubbed);
      assert.deepEqual(callerHeaders, suppliedHeaders());
      assert.equal(inspect(callbacks).includes(SECRET), false);
    });
  }
  for (const kind of ['null', 'reader']) for (const type of ['application/json', 'text/event-stream']) for (const status of [200, 246]) for (const dispatch of [null, 'False', 'false', 'true']) for (const policy of [false, true]) {
    test(`R3 guidance: ${kind} ${type} ${status} ${dispatch} policy=${policy}`, async () => {
      let calls = 0;
      const original = new api.StreamError('synthetic reader failure');
      const client = new api.AgentCC({ ...options(api, policy), fetch: async () => {
        calls++;
        return new Response(kind === 'null' ? null : new ReadableStream({ start(controller) { controller.error(original); } }), headersFor(status, dispatch, type));
      } });
      const error = await caught(() => consume(api, client, type === 'application/json' ? 'stream-json' : 'stream-sse'));
      assert.equal(calls, 1);
      assertGuidance(error, dispatch);
      assert.ok(error instanceof api.StreamError);
      assert.equal(error.gatewayEvidence.gatewayRequestId, ID);
      if (kind === 'null') assert.equal(error.message, 'Response body is null' + (dispatch === null || dispatch === 'False' ? `. ${GUIDANCE}` : ''));
    });
  }
  for (const type of ['application/json', 'text/event-stream']) for (const dispatch of [null, 'False', 'false', 'true']) {
    test(`R3 gateway frame precedence: ${type} ${dispatch}`, async () => {
      const message = 'Response body is null';
      const json = JSON.stringify({ error: { message, code: 'managed_billing_unavailable' } });
      const client = new api.AgentCC({ ...options(api, true), fetch: async () => new Response(type === 'application/json' ? json : `data: ${json}\n\n`, headersFor(200, dispatch, type)) });
      const error = await caught(() => consume(api, client, type === 'application/json' ? 'stream-json' : 'stream-sse'));
      assert.equal(error.message, message); assert.equal(error.remedy, null); assert.equal(error.cause, undefined);
      assert.equal(error.code, 'managed_billing_unavailable');
    });
  }
  for (const method of ['requestRaw', 'requestStream']) {
    test(`R3 caller owns raw reader: ${method}`, async () => {
      const original = new api.StreamError('synthetic caller reader');
      const client = new api.AgentCC({ ...options(api, true), fetch: async () => new Response(new ReadableStream({ start(c) { c.error(original); } }), headersFor(200, null, 'application/json')) });
      const response = await client[method](REQUEST);
      await assert.rejects(response.text(), error => error === original);
    });
  }
  for (const type of ['application/json', 'text/event-stream']) {
    test(`standalone reader has no scrub guarantee: ${type}`, async () => {
      const callerInit = { headers: { Authorization: `Bearer ${SECRET}` } };
      const original = new api.StreamError('synthetic caller reader');
      original.cause = { request: callerInit };
      const response = new Response(new ReadableStream({ start(c) { c.error(original); } }), headersFor(200, null, type));
      const error = await caught(async () => { for await (const _chunk of new api.Stream(response)) { /* consume */ } });
      assert.equal(inspect(error).includes(SECRET), false);
      assert.equal(error.cause, undefined, 'Do not retain a caller-owned unsanitized cause');
      assert.equal(callerInit.headers.Authorization, `Bearer ${SECRET}`);
      assertGuidance(error, null);
    });
    test(`route transport scrubs its own header copy: ${type}`, async () => {
      const callerHeaders = { Authorization: `Bearer ${SECRET}`, ...suppliedHeaders() };
      let init, original;
      const stream = await routeStream({ headers: callerHeaders, fetch: async (_url, sent) => {
        init = sent;
        assert.equal(init.headers.Authorization, `Bearer ${SECRET}`);
        original = new api.StreamError('synthetic route reader');
        original.cause = { request: init };
        return new Response(new ReadableStream({ start(c) { c.error(original); } }), headersFor(200, null, type));
      } }, {});
      const error = await caught(async () => { for await (const _chunk of stream) { /* consume */ } });
      assert.equal(inspect(error).includes(SECRET), false);
      assert.equal(error.cause, original);
      for (const [name, value] of Object.entries(init.headers)) {
        if (NAMES.includes(name.toLowerCase())) assert.equal(value, '[REDACTED]');
      }
      assert.equal(callerHeaders.Authorization, `Bearer ${SECRET}`);
      assert.deepEqual(Object.fromEntries(Object.entries(callerHeaders).filter(([n]) => n !== 'Authorization')), suppliedHeaders());
      assertGuidance(error, null);
    });
  }
  test('credential header names are shared by status and callback sinks', async () => {
    const callbacks = [];
    class Observer extends api.CallbackHandler {
      onRequestStart(request) { callbacks.push(request); }
      onError(request, error) { callbacks.push({ request, error }); }
    }
    const client = new api.AgentCC({ ...options(api, false), callbacks: [new Observer()], fetch: async () => new Response('{}', { status: 400, headers: suppliedHeaders() }) });
    const error = await caught(() => client.request({ ...REQUEST, headers: suppliedHeaders() }));
    assert.equal(inspect(error).includes(SECRET), false);
    assert.equal(inspect(callbacks).includes(SECRET), false);
  });
}
module.exports = { registerCases };
