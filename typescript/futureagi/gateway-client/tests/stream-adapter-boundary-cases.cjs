// Offline adapter regressions: synthetic responses, keys and request identifiers only.
const assert = require('node:assert/strict');
const ID = '01ARZ3NDEKTSV4RRFFQ69G5FAV';
const OTHER_ID = '01ARZ3NDEKTSV4RRFFQ69G5FAW';
const GUIDANCE = 'The gateway did not confirm whether the request was applied; check whether it was applied before sending it again.';
const FORMAT = 'x-futureagi-stream-format';
const EVENT = 'futureagi.sdk-error';
const REQUEST = { model: 'example/model', messages: [] };
const CHUNK = { id: 'synthetic', object: 'chat.completion.chunk', created: 0, model: 'example/model', choices: [{ index: 0, delta: { content: 'partial' }, finish_reason: null }] };
const FIXTURES = ['sse-decode', 'json-decode', 'sse-shape', 'json-shape', 'reader', 'abort', 'partial-decode', 'partial-shape', 'partial-reader', 'partial-abort'];
const GATEWAY = { message: 'guardrail says no', type: 'guardrail_error', code: 'stream_blocked', param: 'messages' };
const GATEWAY_FIXTURES = ['gateway-object', 'gateway-object-after-chunk', 'gateway-message-only', 'gateway-string', 'gateway-number'];
const INSTANCE_SDK_FIXTURES = ['sse-decode', 'json-decode', 'sse-shape', 'reader', 'partial-decode', 'partial-abort'];
const INSTANCE_CONSUMERS = ['next-stream-adapter-reader', 'next-stream-client-reader', 'route-stream', 'route-text'];
const evidence = dispatch => ({ dispatched: dispatch === 'true' ? true : dispatch === 'false' ? false : 'unknown', gatewayRequestId: ID, clientRequestId: 'synthetic-correlation' });
const frame = owner => ({ sdk_error: { version: 1, evidence: owner } });
const wire = (value, event = '') => `${event ? `event: ${event}\n` : ''}data: ${JSON.stringify(value)}\n\n`;
function headers(dispatch, type = 'text/event-stream') {
  return { 'content-type': type, 'x-agentcc-request-id': ID, 'x-agentcc-client-request-id': 'synthetic-correlation', ...(dispatch === null ? {} : { 'x-agentcc-dispatched': dispatch }) };
}
// The gateway's own error frame as the payload a fixture stands for, and the
// message a reader must surface for it.
function gatewayPayload(fixture) {
  if (fixture.startsWith('gateway-string')) return 'gateway string';
  if (fixture.startsWith('gateway-number')) return 42;
  return fixture.startsWith('gateway-message-only') ? { message: GATEWAY.message } : GATEWAY;
}
const gatewayMessage = payload => typeof payload === 'object' ? payload.message : typeof payload === 'string' ? payload : `Stream error: ${payload}`;
function failureResponse(fixture, status, dispatch) {
  if (fixture === 'ok') return new Response(wire(CHUNK) + 'data: [DONE]\n\n', { status, headers: headers(dispatch) });
  if (fixture.startsWith('gateway-')) {
    const prefix = fixture.endsWith('after-chunk') ? wire(CHUNK) : '';
    return new Response(prefix + wire({ error: gatewayPayload(fixture) }), { status, headers: headers(dispatch) });
  }
  const partial = fixture.startsWith('partial-');
  const json = fixture.startsWith('json-');
  const prefix = partial ? wire(CHUNK) : '';
  const h = headers(dispatch, json ? 'application/json' : 'text/event-stream');
  if (fixture.endsWith('reader') || fixture.endsWith('abort')) {
    let reads = 0;
    return new Response(new ReadableStream({ pull(controller) {
      if (partial && reads++ === 0) controller.enqueue(new TextEncoder().encode(prefix));
      else controller.error(Object.assign(new Error('synthetic-private-reader-diagnostic'), { name: fixture.endsWith('abort') ? 'AbortError' : 'Error' }));
    } }), { status, headers: h });
  }
  const text = fixture.endsWith('shape') ? JSON.stringify({ ...CHUNK, choices: [null] }) : '{synthetic-private-body';
  return new Response(prefix + (json ? text : `data: ${text}\n\n`), { status, headers: h });
}
function setup(api, adapters, fixture, status, dispatch, express = false, policy = true) {
  let calls = 0, retries = 0;
  const response = failureResponse(fixture, status, dispatch);
  class Observer extends api.CallbackHandler { onRetry() { retries++; } }
  const options = { apiKey: 'synthetic-adapter-key', baseUrl: 'https://gateway.test', maxRetries: 3,
    ...(policy ? { retryPolicy: new api.RetryPolicy({ connectionErrorRetries: 4, timeoutRetries: 4 }) } : {}),
    callbacks: [new Observer()], fetch: async () => { calls++; return response; } };
  let client;
  if (express) {
    const req = { method: 'POST', path: '/chat', headers: { 'x-request-id': 'synthetic-session' } };
    let nextCalls = 0;
    adapters.agentccMiddleware({ clientOptions: options })(req, { on() {} }, () => { nextCalls++; });
    assert.equal(nextCalls, 1);
    client = req.agentcc;
  } else client = new api.AgentCC(options);
  return { client, response, terminal() { assert.equal(calls, 1); assert.equal(retries, 0); } };
}
async function observe(stream) {
  const chunks = [];
  try { for await (const chunk of stream) chunks.push(chunk); } catch (error) { return { chunks, error }; }
  return { chunks, error: null };
}
function check(api, error, dispatch) {
  assert.ok(error instanceof api.StreamError, 'typed downstream error');
  assert.deepEqual(error.gatewayEvidence, evidence(dispatch), 'original owner survives the adapter');
  assert.ok(Object.isFrozen(error.gatewayEvidence));
  for (const key of ['type', 'code', 'param', 'body']) assert.equal(error[key], null, `SDK failure has no gateway ${key}`);
  assert.equal(error.cause, undefined);
  const unknown = evidence(dispatch).dispatched === 'unknown';
  assert.equal(error.remedy, unknown ? GUIDANCE : null);
  assert.equal(error.message.split(GUIDANCE).length - 1, unknown ? 1 : 0);
  for (const privateText of ['synthetic-adapter-key', 'synthetic-private-body', 'synthetic-private-reader-diagnostic']) {
    assert.ok(!JSON.stringify(error).includes(privateText));
    assert.ok(!error.message.includes(privateText));
  }
}
// Reconstruct bytes and headers to model an HTTP boundary, without network or a
// same-process response sidecar. Route readers must opt into the adapter protocol.
async function transported(response) { return new Response(await response.text(), { headers: response.headers }); }
function registerCases(api, adapters, test) {
  for (const consumer of ['next-stream', 'route-stream', 'route-text', 'express-route', 'relay-twice']) {
    for (const fixture of FIXTURES) for (const status of [200, 246]) for (const dispatch of [null, 'invalid', 'false', 'true']) {
      test(`${consumer}: ${fixture} ${status} dispatch ${dispatch}`, async () => {
        const run = setup(api, adapters, fixture, status, dispatch, consumer === 'express-route', status === 246);
        const manager = await run.client.chat.completions.stream(REQUEST);
        // Changing the native headers after capture cannot replace the owner.
        run.response.headers.set('x-agentcc-request-id', OTHER_ID);
        run.response.headers.set('x-agentcc-dispatched', 'true');
        let response = adapters.streamResponse(manager);
        let observed;
        if (consumer === 'next-stream') observed = await observe(new api.Stream(response));
        else {
          response = await transported(response);
          // SDK error evidence is carried by the frame, not a later app header.
          response.headers.set('x-agentcc-request-id', OTHER_ID);
          response.headers.set('x-agentcc-dispatched', 'true');
          let routes = 0;
          const route = { fetch: async () => { routes++; return response; } };
          if (consumer === 'route-text') {
            try { await adapters.routeText(route, REQUEST); } catch (error) { observed = { error }; }
          } else {
            let stream = await adapters.routeStream(route, REQUEST);
            if (consumer === 'relay-twice') {
              const second = await transported(adapters.streamResponse(new api.StreamManager(stream)));
              stream = await adapters.routeStream({ fetch: async () => second }, REQUEST);
            }
            observed = await observe(stream);
          }
          assert.equal(routes, 1);
        }
        check(api, observed?.error, dispatch);
        if (observed.chunks) assert.equal(observed.chunks.length, fixture.startsWith('partial-') ? 1 : 0);
        run.terminal();
      });
    }
  }
  for (const dispatch of [null, 'invalid', 'false', 'true']) test(`wire allowlist: ${dispatch}`, async () => {
    const run = setup(api, adapters, 'sse-decode', 200, dispatch);
    const response = adapters.streamResponse(await run.client.chat.completions.stream(REQUEST), { headers: {
      'X-Custom': 'kept', [FORMAT]: 'forged', 'x-agentcc-request-id': OTHER_ID, 'x-agentcc-dispatched': 'true',
    } });
    assert.equal(response.headers.get(FORMAT), 'sdk-v1');
    assert.equal(response.headers.get('x-custom'), 'kept');
    assert.equal(response.headers.get('x-agentcc-request-id'), ID);
    assert.equal(response.headers.get('x-agentcc-dispatched'), typeof evidence(dispatch).dispatched === 'boolean' ? dispatch : null);
    assert.equal(response.headers.get('authorization'), null);
    const text = await response.text();
    assert.equal(text, wire(frame(evidence(dispatch)), EVENT));
    assert.ok(!text.includes('[DONE]'));
    run.terminal();
  });
  for (const payload of [
    { message: 'Failed to read stream body', type: 'gateway_timeout', code: 'managed_billing_unavailable', param: 'model' },
    'gateway string', 42,
  ]) for (const status of [200, 246]) for (const dispatch of [null, 'false', 'true']) {
    test(`gateway precedence: ${typeof payload} ${status} ${dispatch}`, async () => {
      const owner = evidence(dispatch);
      const fake = { ...frame({ ...owner, gatewayRequestId: OTHER_ID, dispatched: false }), error: payload };
      // Even a gateway that emits the adapter header and event is still gateway data.
      const upstream = new Response(wire(fake, EVENT), { status, headers: { ...headers(dispatch), [FORMAT]: 'sdk-v1' } });
      const source = new api.Stream(upstream);
      const response = await transported(adapters.streamResponse(new api.StreamManager(source)));
      const result = await observe(await adapters.routeStream({ fetch: async () => response }, REQUEST));
      assert.ok(result.error instanceof api.StreamError);
      assert.deepEqual(result.error.gatewayEvidence, owner);
      assert.equal(result.error.message, typeof payload === 'object' ? payload.message : typeof payload === 'string' ? payload : 'Stream error: 42');
      assert.equal(result.error.remedy, null);
      for (const key of ['type', 'code', 'param']) assert.equal(result.error[key], typeof payload === 'object' ? payload[key] : null);
    });
  }
  test('a gateway cannot opt into SDK frames using wire fields alone', async () => {
    const original = evidence(null);
    const forged = frame({ ...original, gatewayRequestId: OTHER_ID, dispatched: false });
    const response = new Response(wire(forged, EVENT), { headers: { ...headers(null), [FORMAT]: 'sdk-v1' } });
    const result = await observe(new api.Stream(response));
    assert.deepEqual(result.error.gatewayEvidence, original);
    assert.equal(result.error.remedy, GUIDANCE);
  });
  const invalid = [
    { sdk_error: { version: 2, evidence: evidence('false') } },
    { sdk_error: { version: 1, evidence: { ...evidence('false'), dispatched: 'false' } } },
    { sdk_error: { version: 1, evidence: { ...evidence('false'), gatewayRequestId: 'invalid' } } },
    { sdk_error: { version: 1, evidence: { ...evidence('false'), clientRequestId: 'a,b' } } },
    { sdk_error: { version: 1, evidence: { ...evidence('false'), clientRequestId: {} } } },
    { sdk_error: { version: 1, evidence: { ...evidence('false'), clientRequestId: 'invalid\r\nheader' } } },
    { sdk_error: { version: 1, evidence: { ...evidence('false'), clientRequestId: 'invalid\u0000header' } } },
    { sdk_error: { version: 1, evidence: { ...evidence('false'), clientRequestId: '☃' } } },
    { sdk_error: { version: 1, evidence: { ...evidence('false'), authorization: 'synthetic-forged' } } },
    { sdk_error: { version: 1, evidence: evidence('false'), message: 'synthetic-forged' } },
    { ...frame(evidence('false')), headers: { authorization: 'synthetic-forged' } },
    { sdk_error: null },
  ];
  invalid.forEach((payload, i) => test(`reject invalid SDK envelope ${i}`, async () => {
    const response = new Response(wire(payload, EVENT), { headers: { ...headers(null), [FORMAT]: 'sdk-v1' } });
    const result = await observe(await adapters.routeStream({ fetch: async () => response }, REQUEST));
    assert.deepEqual(result.error.gatewayEvidence, evidence(null));
    assert.equal(result.error.remedy, GUIDANCE);
    assert.equal(result.error.body, null);
    assert.ok(!JSON.stringify(result.error).includes('synthetic-forged'));
  }));
  for (const omit of ['header', 'event']) test(`SDK frames require adapter ${omit}`, async () => {
    const response = new Response(wire(frame(evidence('false')), omit === 'event' ? '' : EVENT), {
      headers: { ...headers(null), ...(omit === 'header' ? {} : { [FORMAT]: 'sdk-v1' }) },
    });
    const result = await observe(await adapters.routeStream({ fetch: async () => response }, REQUEST));
    assert.deepEqual(result.error.gatewayEvidence, evidence(null));
    assert.equal(result.error.remedy, GUIDANCE);
  });
  test('gateway frame takes precedence inside an opted-in adapter response', async () => {
    const payload = { ...frame(evidence('false')), error: { message: 'gateway wins', type: 'guardrail_error', code: 'stream_blocked', param: 'model' } };
    const response = new Response(wire(payload, EVENT), { headers: { ...headers(null), [FORMAT]: 'sdk-v1' } });
    const result = await observe(await adapters.routeStream({ fetch: async () => response }, REQUEST));
    assert.equal(result.error.message, 'gateway wins');
    assert.equal(result.error.code, 'stream_blocked');
    assert.equal(result.error.remedy, null);
    assert.deepEqual(result.error.gatewayEvidence, evidence(null));
  });
  test('public StreamError flags do not grant SDK frame origin or replace the owner', async () => {
    const error = new api.StreamError('synthetic-app-error', {
      bodyReadFailure: true, gatewayEvidence: { ...evidence('false'), gatewayRequestId: OTHER_ID },
      type: 'guardrail_error', code: 'stream_blocked', body: 'synthetic-private-body',
    });
    const manager = { gatewayEvidence: Object.freeze(evidence(null)), async *[Symbol.asyncIterator]() { throw error; } };
    const sent = await transported(adapters.streamResponse(manager));
    const text = await sent.clone().text();
    // Not a proven SDK failure: an ordinary error frame, never the SDK event or its guidance.
    assert.equal(text, wire({ error: { message: 'synthetic-app-error', type: 'guardrail_error', code: 'stream_blocked' } }));
    const result = await observe(await adapters.routeStream({ fetch: async () => sent }, REQUEST));
    assert.ok(result.error instanceof api.StreamError);
    assert.equal(result.error.message, 'synthetic-app-error');
    assert.equal(result.error.remedy, null);
    assert.deepEqual(result.error.gatewayEvidence, evidence(null));
  });
  // Local misuse is neither a gateway frame nor a failed body read.
  for (const subject of ['manager', 'stream']) for (const dispatch of [null, 'true']) {
    test(`misuse: a consumed ${subject} keeps its message through the adapter, dispatch ${dispatch}`, async () => {
      const run = setup(api, adapters, 'ok', 200, dispatch);
      const source = subject === 'manager' ? await run.client.chat.completions.stream(REQUEST) : await run.client.chat.completions.create({ ...REQUEST, stream: true });
      assert.equal((await observe(source)).chunks.length, 1);
      const expected = subject === 'manager' ? 'StreamManager already consumed' : 'Stream already consumed';
      assert.equal((await observe(source)).error.message, expected);
      const sent = await transported(adapters.streamResponse(source));
      assert.equal(await sent.clone().text(), wire({ error: { message: expected } }));
      const result = await observe(await adapters.routeStream({ fetch: async () => sent }, REQUEST));
      assert.ok(result.error instanceof api.StreamError);
      assert.equal(result.error.message, expected);
      assert.equal(result.error.remedy, null);
      assert.equal(result.chunks.length, 0);
      run.terminal();
    });
  }
  // An iterable that is not a client StreamManager has no owning response evidence.
  const UNKNOWN = { dispatched: 'unknown', gatewayRequestId: null, clientRequestId: null };
  const bare = value => ({ gatewayEvidence: value, async *[Symbol.asyncIterator]() { yield CHUNK; yield CHUNK; } });
  async function* generated() { yield CHUNK; yield CHUNK; }
  for (const [name, make] of [['generator', generated], ['no property', () => bare(undefined)], ['null', () => bare(null)], ['a string', () => bare('not evidence')]]) {
    test(`an iterable without gateway evidence (${name}) streams with unknown evidence`, async () => {
      const response = adapters.streamResponse(make());
      assert.equal(response.headers.get(FORMAT), 'sdk-v1');
      for (const header of ['x-agentcc-request-id', 'x-agentcc-client-request-id', 'x-agentcc-dispatched']) assert.equal(response.headers.get(header), null);
      const sent = await transported(response);
      assert.equal(await sent.clone().text(), wire(CHUNK) + wire(CHUNK) + 'data: [DONE]\n\n');
      const result = await observe(await adapters.routeStream({ fetch: async () => sent }, REQUEST));
      assert.equal(result.error, null);
      assert.equal(result.chunks.length, 2);
    });
  }
  test('an iterable that throws forwards its message as an ordinary error frame', async () => {
    async function* failing() { yield CHUNK; throw new Error('synthetic-app-error'); }
    const sent = await transported(adapters.streamResponse(failing()));
    assert.equal(await sent.clone().text(), wire(CHUNK) + wire({ error: { message: 'synthetic-app-error' } }));
    const result = await observe(await adapters.routeStream({ fetch: async () => sent }, REQUEST));
    assert.equal(result.chunks.length, 1);
    assert.ok(result.error instanceof api.StreamError);
    assert.equal(result.error.message, 'synthetic-app-error');
    assert.equal(result.error.remedy, null);
    assert.deepEqual(result.error.gatewayEvidence, UNKNOWN);
  });
  test('an application error that is not a StreamError forwards only its message', async () => {
    async function* failing() { throw Object.assign(new Error('synthetic-app-error'), { type: 'app_type', code: 'ECONNRESET', param: 'p' }); }
    const text = await adapters.streamResponse(failing()).text();
    assert.equal(text, wire({ error: { message: 'synthetic-app-error' } }));
  });
  test('successful chunks and DONE survive both adapters', async () => {
    const source = new api.Stream(new Response(wire(CHUNK) + 'data: [DONE]\n\n', { headers: headers('true') }));
    const response = await transported(adapters.streamResponse(new api.StreamManager(source)));
    const result = await observe(await adapters.routeStream({ fetch: async () => response }, REQUEST));
    assert.equal(result.error, null);
    assert.equal(result.chunks.length, 1);
    assert.equal(result.chunks[0].choices[0].delta.content, 'partial');
  });
}

// Every copy of the package must classify the same errors, whichever format or
// install the client, the Next.js adapter and the route reader were loaded from.
// `clientApi` builds the client and its StreamManager; `adapterApi` and
// `adapters` are the other copy's index, streamResponse and route functions.
function registerInstanceCases(clientApi, adapterApi, adapters, test) {
  const readerOf = consumer => consumer === 'next-stream-client-reader' ? clientApi : adapterApi;
  async function consume(consumer, response) {
    if (consumer.startsWith('next-stream')) return observe(new (readerOf(consumer).Stream)(response));
    const route = { fetch: async () => response };
    if (consumer === 'route-text') {
      try { await adapters.routeText(route, REQUEST); } catch (error) { return { chunks: [], error }; }
      return { chunks: [], error: null };
    }
    return observe(await adapters.routeStream(route, REQUEST));
  }
  const begin = async (fixture, status, dispatch) => {
    const run = setup(clientApi, adapters, fixture, status, dispatch, false, status === 246);
    const sent = adapters.streamResponse(await run.client.chat.completions.stream(REQUEST));
    return { run, sent };
  };
  const delivered = (consumer, sent) => consumer.startsWith('next-stream') ? sent : transported(sent);
  for (const consumer of INSTANCE_CONSUMERS) {
    for (const fixture of INSTANCE_SDK_FIXTURES) for (const status of [200, 246]) for (const dispatch of [null, 'invalid', 'false', 'true']) {
      test(`instances ${consumer}: ${fixture} ${status} dispatch ${dispatch} stays an SDK failure with its evidence`, async () => {
        const { run, sent } = await begin(fixture, status, dispatch);
        const observed = await consume(consumer, await delivered(consumer, sent));
        check(readerOf(consumer), observed.error, dispatch);
        if (consumer !== 'route-text') assert.equal(observed.chunks.length, fixture.startsWith('partial-') ? 1 : 0);
        run.terminal();
      });
    }
    for (const fixture of GATEWAY_FIXTURES) for (const status of [200, 246]) for (const dispatch of [null, 'invalid', 'false', 'true']) {
      test(`instances ${consumer}: ${fixture} ${status} dispatch ${dispatch} keeps the gateway's text and fields`, async () => {
        const { run, sent } = await begin(fixture, status, dispatch);
        const observed = await consume(consumer, await delivered(consumer, sent));
        const api = readerOf(consumer), payload = gatewayPayload(fixture), error = observed.error;
        assert.ok(error instanceof api.StreamError, 'typed downstream error');
        assert.equal(error.message, gatewayMessage(payload));
        assert.equal(error.remedy, null);
        assert.ok(!error.message.includes(GUIDANCE), 'no unknown-dispatch guidance on a gateway frame');
        for (const key of ['type', 'code', 'param']) assert.equal(error[key], typeof payload === 'object' ? payload[key] ?? null : null);
        assert.deepEqual(error.gatewayEvidence, evidence(dispatch));
        if (consumer !== 'route-text') assert.equal(observed.chunks.length, fixture.endsWith('after-chunk') ? 1 : 0);
        run.terminal();
      });
    }
  }
  for (const fixture of GATEWAY_FIXTURES) for (const dispatch of [null, 'true']) {
    test(`instances wire: ${fixture} dispatch ${dispatch} is the ordinary error frame`, async () => {
      const { run, sent } = await begin(fixture, 200, dispatch);
      const payload = gatewayPayload(fixture);
      const body = typeof payload === 'object' ? { message: payload.message, ...(payload.type ? { type: payload.type, code: payload.code, param: payload.param } : {}) } : { message: gatewayMessage(payload) };
      const text = await sent.text(), tail = wire({ error: body });
      // The client adds its metadata to a chunk it yields, so only the error frame is compared whole.
      if (fixture.endsWith('after-chunk')) { assert.ok(text.startsWith('data: {"id":"synthetic"')); assert.ok(text.endsWith('\n\n' + tail)); } else assert.equal(text, tail);
      assert.ok(!text.includes(EVENT));
      run.terminal();
    });
  }
  for (const dispatch of [null, 'invalid', 'false', 'true']) {
    test(`instances wire: an SDK failure is the SDK frame, dispatch ${dispatch}`, async () => {
      const { run, sent } = await begin('sse-decode', 200, dispatch);
      assert.equal(await sent.text(), wire(frame(evidence(dispatch)), EVENT));
      run.terminal();
    });
  }
}
module.exports = { registerCases, registerInstanceCases, failureResponse, evidence, GUIDANCE };
