// Shared source and built-package regressions; all transport values are synthetic.
const assert = require('node:assert/strict');
const ID = '01ARZ3NDEKTSV4RRFFQ69G5FAV';
const REQUEST = { method: 'POST', path: '/v1/chat/completions', body: { model: 'example/model', messages: [] } };
const PATHS = ['request', 'requestWithResponse', 'requestRaw', 'requestStream'];
const SECRET = 'synthetic-sensitive-marker';
const coded = (code, extra = {}) => Object.assign(new Error('transport failure'), { code, ...extra });
const wrapped = (cause) => Object.assign(new TypeError('fetch failed'), { cause });
const failures = [
  ['timeout', () => new DOMException('timed out', 'TimeoutError'), 'APITimeoutError'],
  ['abort', () => new DOMException('aborted', 'AbortError'), 'APIConnectionError'],
  ['fetch abort', () => new TypeError('request aborted'), 'APITimeoutError'],
  ...['ECONNRESET', 'UND_ERR_SOCKET', 'UND_ERR_HEADERS_TIMEOUT', 'UND_ERR_BODY_TIMEOUT', 'ETIMEDOUT', 'EPIPE', 'UNKNOWN'].map(code => [code, () => wrapped(coded(code)), 'APIConnectionError']),
  ['unclassified', () => new TypeError('fetch failed'), 'APIConnectionError'],
  ['pre-send wording is not evidence', () => new Error('ENOTFOUND connection refused connect timeout'), 'APIConnectionError'],
  ['mixed aggregate', () => wrapped(new AggregateError([coded('ECONNREFUSED'), coded('ECONNRESET')])), 'APIConnectionError'],
  ['coded mixed aggregate', () => wrapped(Object.assign(new AggregateError([coded('ECONNREFUSED'), coded('ECONNRESET')]), { code: 'ECONNREFUSED' })), 'APIConnectionError'],
  ['reset overrides nested DNS', () => coded('ECONNRESET', { cause: coded('ENOTFOUND') }), 'APIConnectionError'],
  ['cyclic cause', () => { const e = new Error('cycle'); e.cause = e; return e; }, 'APIConnectionError'],
];
const preSend = [
  ...['ENOTFOUND', 'EAI_AGAIN', 'ECONNREFUSED', 'UND_ERR_CONNECT_TIMEOUT', 'UND_ERR_POOL_TIMEOUT', 'UND_ERR_QUEUE_TIMEOUT'].map(code => [code, () => wrapped(coded(code))]),
  ['connect syscall timeout', () => wrapped(coded('ETIMEDOUT', { syscall: 'connect' }))],
  ['all pre-send aggregate', () => wrapped(new AggregateError([coded('ECONNREFUSED'), coded('ENOTFOUND')]))],
];
function inspect(value, seen = new Set()) {
  if (value === null || value === undefined) return '';
  if (typeof value !== 'object') return String(value);
  if (seen.has(value)) return ''; seen.add(value);
  if (value instanceof Headers) return JSON.stringify([...value]);
  return Object.getOwnPropertyNames(value).map(key => key + inspect(value[key], seen)).join(' ');
}
function registerCases(api, test) {
  const settings = [
    ['flat', { maxRetries: 1 }],
    ['policy', { maxRetries: 1, retryPolicy: new api.RetryPolicy({ timeoutRetries: 5, connectionErrorRetries: 5, serviceUnavailableRetries: 1, rateLimitRetries: 5, internalServerErrorRetries: 5, badGatewayRetries: 5, gatewayTimeoutRetries: 5 }) }],
  ];
  function setup(fetch, options) {
    const events = [];
    class Observer extends api.CallbackHandler {
      onRequestStart(request) { events.push(['start', request]); }
      onError(request, error) { events.push(['error', request, error]); }
      onRetry(request, error) { events.push(['retry', request, error]); }
    }
    const client = new api.AgentCC({ apiKey: SECRET, sessionId: SECRET, baseUrl: 'https://gateway.test', callbacks: [new Observer()], ...options, fetch });
    return { client, events };
  }
  async function timed(fn) {
    const original = globalThis.setTimeout;
    const sleeps = [];
    globalThis.setTimeout = (callback, ms, ...args) => {
      sleeps.push(ms);
      if (sleeps.length > 32) throw new Error('Retry observation exceeded bounded test budget');
      queueMicrotask(() => callback(...args)); return { unref() { return this; } };
    };
    try { await fn(sleeps); } finally { globalThis.setTimeout = original; }
  }
  async function failure(promise) {
    try { await promise; } catch (error) { return error; }
    assert.fail('Expected a terminal error');
  }
  for (const path of PATHS) {
    for (const [name, options] of [['SDK defaults', {}], ['unbounded policy', { retryPolicy: new api.RetryPolicy({ timeoutRetries: Infinity, connectionErrorRetries: Infinity, serviceUnavailableRetries: Infinity }) }]]) {
      test(`${path}: ${name} cannot override unknown transport dispatch`, () => timed(async sleeps => {
        let calls = 0;
        const { client } = setup(async () => { calls++; throw new TypeError('fetch failed'); }, options);
        const error = await failure(client[path](REQUEST));
        assert.ok(error instanceof api.APIConnectionError);
        assert.equal(calls, 1); assert.equal(sleeps.length, 0);
      }));
    }
    for (const kind of ['transport', 'status']) {
      test(`${path}: ${kind} errors and callbacks omit sensitive request headers`, () => timed(async () => {
        const sensitive = { AuThOrIzAtIoN: 'Bearer ' + SECRET, 'x-agentcc-config': SECRET, 'x-agentcc-session-id': SECRET };
        const { client, events } = setup(async () => {
          if (kind === 'transport') throw wrapped(coded('ECONNRESET'));
          return new Response('{}', { status: 503, headers: { ...sensitive, 'x-agentcc-request-id': ID } });
        }, { maxRetries: 0 });
        const error = await failure(client[path]({ ...REQUEST, headers: sensitive }));
        assert.ok(!inspect([error, events]).includes(SECRET));
        assert.ok(!inspect([error, events]).toLowerCase().includes('authorization'));
        assert.equal(sensitive.AuThOrIzAtIoN, 'Bearer ' + SECRET);
      }));
    }
  }
  for (const path of PATHS) for (const [setting, options] of settings) {
    test(`${path} ${setting}: unreadable 503 keeps status-driven retry`, () => timed(async sleeps => {
      let calls = 0;
      const { client, events } = setup(async () => {
        calls++;
        const response = new Response('{}', { status: 503, headers: { 'x-agentcc-request-id': ID, 'x-agentcc-dispatched': 'false' } });
        response.json = () => { throw new Error('unreadable JSON'); };
        response.text = async () => { throw new Error('unreadable text'); };
        return response;
      }, options);
      const error = await failure(client[path](REQUEST));
      assert.ok(error instanceof api.ServiceUnavailableError);
      assert.equal(calls, 2); assert.equal(sleeps.length, 1);
      assert.deepEqual(error.gatewayEvidence, { dispatched: false, gatewayRequestId: ID, clientRequestId: null });
      assert.equal(events.filter(e => e[0] === 'retry').length, 1);
    }));
    for (const [name, make, expected] of failures) {
      test(`${path} ${setting}: ${name} is unknown and terminal`, () => timed(async sleeps => {
        let calls = 0;
        const { client, events } = setup(async (_url, init) => {
          calls++;
          const original = make();
          // Transport exceptions can retain the SDK-composed authorization and session headers.
          original.request = init;
          original.message += ' ' + SECRET;
          throw original;
        }, options);
        const error = await failure(client[path](REQUEST));
        assert.equal(error.name, expected); assert.ok(error instanceof api.APIConnectionError);
        assert.equal(calls, 1); assert.equal(sleeps.length, 0);
        assert.deepEqual(error.gatewayEvidence, { dispatched: 'unknown', gatewayRequestId: null, clientRequestId: null });
        assert.ok(Object.isFrozen(error.gatewayEvidence));
        assert.match(error.message, /check whether.*applied.*before/i);
        assert.equal(error.cause, undefined);
        assert.equal(events.filter(e => e[0] === 'retry').length, 0);
        assert.equal(events.find(e => e[0] === 'error')[2], error);
        assert.ok(!inspect([error, events]).includes(SECRET));
        assert.ok(!inspect([error, events]).toLowerCase().includes('authorization'));
      }));
    }
    for (const [name, make] of preSend) {
      test(`${path} ${setting}: ${name} remains retryable before send`, () => timed(async sleeps => {
        let calls = 0;
        const { client } = setup(async () => { calls++; throw make(); }, options);
        const error = await failure(client[path](REQUEST));
        assert.ok(error instanceof api.APIConnectionError);
        const attempts = setting === 'policy' ? 6 : 2;
        assert.equal(calls, attempts); assert.equal(sleeps.length, attempts - 1);
        assert.deepEqual(error.gatewayEvidence, { dispatched: false, gatewayRequestId: null, clientRequestId: null });
      }));
    }
    for (const dispatch of [null, 'False', 'false, false', 'unknown']) {
      for (const code of [undefined, 'future_code']) {
        test(`${path} ${setting}: unknown gateway dispatch ${dispatch} code ${code}`, () => timed(async sleeps => {
          let calls = 0;
          const { client } = setup(async () => {
            calls++;
            const headers = new Headers({ 'x-agentcc-request-id': ID, 'x-agentcc-client-request-id': 'correlation' });
            if (dispatch !== null) headers.set('x-agentcc-dispatched', dispatch);
            return new Response(JSON.stringify({ error: { code } }), { status: 503, headers });
          }, options);
          const error = await failure(client[path](REQUEST));
          assert.ok(error instanceof api.ServiceUnavailableError);
          assert.equal(calls, 1); assert.equal(sleeps.length, 0);
          assert.deepEqual(error.gatewayEvidence, { dispatched: 'unknown', gatewayRequestId: ID, clientRequestId: 'correlation' });
          assert.match(error.remedy, /check whether.*applied.*before/i);
        }));
      }
    }
    test(`${path} ${setting}: explicit contract row keeps precedence over unknown dispatch`, () => timed(async sleeps => {
      let calls = 0;
      const { client } = setup(async () => {
        calls++;
        return new Response(JSON.stringify({ error: { code: 'managed_billing_unavailable' } }), { status: 503, headers: { 'x-agentcc-request-id': ID } });
      }, options);
      const error = await failure(client[path](REQUEST));
      assert.ok(error instanceof api.ServiceUnavailableError);
      assert.equal(calls, 2); assert.equal(sleeps.length, 1);
      assert.equal(error.gatewayEvidence.dispatched, 'unknown');
    }));
  }
}
module.exports = { registerCases };
