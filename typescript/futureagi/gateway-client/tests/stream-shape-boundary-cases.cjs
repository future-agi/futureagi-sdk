// Offline public streaming regressions shared by source, CJS and ESM. Synthetic values only.
const assert = require('node:assert/strict');
const ID = '01ARZ3NDEKTSV4RRFFQ69G5FAV';
const GUIDANCE = 'The gateway did not confirm whether the request was applied; check whether it was applied before sending it again.';
const PARAMS = { model: 'example/model', messages: [] };
const REQUEST = { method: 'POST', path: '/v1/chat/completions', body: PARAMS };
const CHUNK = { id: 'synthetic', object: 'chat.completion.chunk', created: 0, model: PARAMS.model, choices: [{ index: 0, delta: { content: 'partial' }, finish_reason: null }] };
const withDelta = delta => ({ ...CHUNK, choices: [{ index: 0, delta, finish_reason: null }] });
const CONSUMERS = ['iteration', 'events', 'textStream', 'getFinalCompletion', 'getFinalText', 'bareStream', 'accumulator'];
const SHAPES = [
  ['missing choices', { object: 'chat.completion.chunk' }],
  ['object choices', { ...CHUNK, choices: {} }],
  ['null choice', { ...CHUNK, choices: [null] }],
  ['object tool calls', withDelta({ tool_calls: {} })],
  ['null tool call', withDelta({ tool_calls: [null] })],
  ['uncoercible content', withDelta({ content: { toString: null } })],
];
const NESTED_SHAPES = [
  ['null choices', { ...CHUNK, choices: null }],
  ['string choices', { ...CHUNK, choices: 'invalid' }],
  ['array payload', []],
  ['array choice', { ...CHUNK, choices: [[]] }],
  ['primitive choice', { ...CHUNK, choices: [42] }],
  ['second null choice', { ...CHUNK, choices: [...CHUNK.choices, null] }],
  ['array delta', withDelta([])],
  ['primitive delta', withDelta('invalid')],
  ['array tool call', withDelta({ tool_calls: [[]] })],
  ['primitive tool call', withDelta({ tool_calls: [42] })],
  ['string tool calls', withDelta({ tool_calls: 'invalid' })],
  ['array function', withDelta({ tool_calls: [{ index: 0, function: [] }] })],
  ['primitive function', withDelta({ tool_calls: [{ index: 0, function: 'invalid' }] })],
  ['uncoercible function name', withDelta({ tool_calls: [{ index: 0, function: { name: { toString: null } } }] })],
  ['uncoercible function arguments', withDelta({ tool_calls: [{ index: 0, function: { arguments: { toString: null } } }] })],
  ['uncoercible tool index', withDelta({ tool_calls: [{ index: 0 }, { index: { toString: null } }] })],
];
const encode = (payload, format, prefix = []) => format === 'JSON'
  ? JSON.stringify(payload)
  : [...prefix, payload].map(chunk => `data: ${JSON.stringify(chunk)}\n\n`).join('') + 'data: [DONE]\n\n';

function setup(api, payload, format, status, dispatch, prefix = [], policy = true) {
  let calls = 0;
  const retries = [];
  class Observer extends api.CallbackHandler {
    onRetry(_request, error) { retries.push(error); }
  }
  const headers = { 'content-type': format === 'JSON' ? 'application/json' : 'text/event-stream', 'x-agentcc-request-id': ID, 'x-agentcc-client-request-id': 'correlation' };
  if (dispatch !== null) headers['x-agentcc-dispatched'] = dispatch;
  const text = encode(payload, format, prefix);
  const response = new Response(text, { status, headers });
  const client = new api.AgentCC({
    apiKey: 'synthetic-only', baseUrl: 'https://gateway.test', maxRetries: 5,
    ...(policy ? { retryPolicy: new api.RetryPolicy({ connectionErrorRetries: Infinity, timeoutRetries: Infinity }) } : {}),
    callbacks: [new Observer()], fetch: async () => { assert.equal(++calls, 1, 'Never replay'); return response; },
  });
  return { client, response, text, terminal() { assert.equal(calls, 1); assert.equal(retries.length, 0); } };
}

async function open(api, run, consumer) {
  return consumer === 'bareStream' || consumer === 'accumulator'
    ? run.client.chat.completions.create({ ...PARAMS, stream: true })
    : run.client.chat.completions.stream(PARAMS);
}
async function consume(api, stream, consumer, seen = []) {
  const accumulator = consumer === 'accumulator' ? new api.ChunkAccumulator() : null;
  const iterable = consumer === 'events' ? stream.events() : consumer === 'textStream' ? stream.textStream() : stream;
  for await (const value of iterable) {
    if (accumulator) accumulator.add(value);
    seen.push(value);
  }
  if (consumer === 'getFinalCompletion') return stream.getFinalCompletion();
  if (consumer === 'getFinalText') return stream.getFinalText();
  if (accumulator) return accumulator.getFinalCompletion();
}
function evidence(api, error, run, stream, dispatch) {
  assert.ok(error instanceof api.StreamError, `Expected StreamError, got ${error?.name ?? 'no error'}`);
  assert.equal(error.name, 'StreamError');
  assert.equal(error.gatewayEvidence, stream.gatewayEvidence);
  assert.equal(error.gatewayEvidence, api.getGatewayEvidence(run.response));
  assert.ok(Object.isFrozen(error.gatewayEvidence));
  assert.deepEqual(error.gatewayEvidence, { dispatched: dispatch === 'true' ? true : dispatch === 'false' ? false : 'unknown', gatewayRequestId: ID, clientRequestId: 'correlation' });
  assert.equal(error.cause, undefined);
  for (const field of ['body', 'type', 'code', 'param']) assert.equal(error[field], null);
  const unknown = dispatch === null || dispatch === 'False';
  assert.equal(error.message.split(GUIDANCE).length - 1, unknown ? 1 : 0);
  assert.equal(error.remedy, unknown ? GUIDANCE : null);
}
async function checkShape(api, payload, consumer, format, status, dispatch, prefix = [], policy = true) {
  const run = setup(api, payload, format, status, dispatch, prefix, policy);
  const stream = await open(api, run, consumer);
  // A later header mutation or an untrusted payload must not replace captured evidence.
  run.response.headers.set('x-agentcc-dispatched', dispatch === 'true' ? 'false' : 'true');
  run.response.headers.set('x-agentcc-request-id', 'changed');
  const seen = [];
  let error;
  try { await consume(api, stream, consumer, seen); } catch (caught) { error = caught; }
  run.terminal();
  evidence(api, error, run, stream, dispatch);
  assert.equal(seen.length, prefix.length, 'Invalid chunks never reach consumers or accumulation');
  if (consumer === 'events') assert.equal(seen.some(event => event.type === 'done'), false);
  if (typeof stream.getFinalText === 'function') {
    assert.equal(stream.getFinalText(), prefix.length ? 'partial' : '');
    assert.equal(stream.getFinalCompletion().choices[0].message.content, prefix.length ? 'partial' : null);
  }
}

function registerCases(api, test) {
  for (const [shape, payload] of SHAPES) for (const consumer of CONSUMERS) for (const format of ['JSON', 'SSE']) {
    for (const status of [200, 246]) for (const dispatch of [null, 'False', 'false', 'true']) {
      test(`shape ${shape}: ${consumer} ${format} ${status} dispatch=${dispatch}`, () => checkShape(api, payload, consumer, format, status, dispatch));
    }
  }
  for (const [shape, payload] of NESTED_SHAPES) for (const consumer of CONSUMERS) for (const format of ['JSON', 'SSE']) {
    test(`nested ${shape}: ${consumer} ${format}`, () => checkShape(api, payload, consumer, format, 200, null));
  }
  for (const consumer of CONSUMERS) for (const status of [200, 246]) for (const dispatch of [null, 'False', 'false', 'true']) for (const policy of [false, true]) {
    test(`partial shape: ${consumer} ${status} dispatch=${dispatch} policy=${policy}`, () => checkShape(api, SHAPES[3][1], consumer, 'SSE', status, dispatch, [CHUNK], policy));
  }
  for (const consumer of CONSUMERS) for (const format of ['JSON', 'SSE']) for (const status of [200, 246]) {
    test(`gateway frame before shape: ${consumer} ${format} ${status}`, async () => {
      const body = { message: 'Synthetic refusal', type: 'guardrail_error', code: 'stream_blocked', param: 'model' };
      const run = setup(api, { error: body, choices: {} }, format, status, null);
      const stream = await open(api, run, consumer);
      await assert.rejects(() => consume(api, stream, consumer), error => {
        assert.ok(error instanceof api.StreamError);
        assert.equal(error.gatewayEvidence, stream.gatewayEvidence);
        assert.equal(error.message, body.message);
        assert.deepEqual(error.body, body);
        for (const key of ['type', 'code', 'param']) assert.equal(error[key], body[key]);
        assert.equal(error.remedy, null);
        return true;
      });
      run.terminal();
    });
  }
  for (const method of ['requestRaw', 'requestStream']) for (const format of ['JSON', 'SSE']) for (const status of [200, 246]) {
    test(`raw ownership: ${method} ${format} ${status}`, async () => {
      const run = setup(api, SHAPES[1][1], format, status, null);
      const raw = await run.client[method](REQUEST);
      assert.equal(raw.bodyUsed, false);
      assert.equal(await raw.text(), run.text);
      run.terminal();
    });
  }
  // Keep permissive optional/null deltas, usage-only chunks and whole JSON answers.
  for (const format of ['JSON', 'SSE']) for (const status of [200, 246]) {
    const payloads = [
      ['empty choices', { ...CHUNK, choices: [], usage: { prompt_tokens: 2, completion_tokens: 3, total_tokens: 5 } }],
      ['missing delta', { ...CHUNK, choices: [{ index: 0, finish_reason: 'stop' }] }],
      ['null delta', withDelta(null)],
      ['null optionals', withDelta({ content: null, tool_calls: null })],
      ['null function', withDelta({ tool_calls: [{ index: 0, function: null }] })],
      ['tool call', withDelta({ content: 'partial', tool_calls: [{ index: 0, id: 'synthetic-call', function: { name: 'example', arguments: '{}' } }] })],
    ];
    for (const [name, payload] of payloads) test(`valid ${name}: ${format} ${status}`, async () => {
      const run = setup(api, payload, format, status, null);
      const stream = await run.client.chat.completions.stream(PARAMS);
      const events = [];
      for await (const event of stream.events()) events.push(event);
      assert.equal(events.filter(event => event.type === 'done').length, 1);
      const final = stream.getFinalCompletion();
      assert.equal(final.choices[0].message.content, name === 'tool call' ? 'partial' : null);
      if (name === 'tool call') assert.deepEqual(final.choices[0].message.tool_calls, [{ id: 'synthetic-call', type: 'function', function: { name: 'example', arguments: '{}' } }]);
      if (payload.usage) assert.deepEqual(final.usage, payload.usage);
      run.terminal();
    });
  }
  test('whole JSON completion still converts to a chunk', async () => {
    const payload = { ...CHUNK, object: 'chat.completion', choices: [{ index: 0, message: { role: 'assistant', content: 'complete', tool_calls: [{ id: 'synthetic-call', type: 'function', function: { name: 'example', arguments: '{}' } }] }, finish_reason: 'tool_calls' }] };
    const run = setup(api, payload, 'JSON', 246, null);
    const stream = await run.client.chat.completions.stream(PARAMS);
    await consume(api, stream, 'iteration');
    const final = stream.getFinalCompletion();
    assert.equal(final.choices[0].message.content, 'complete');
    assert.equal(final.choices[0].finish_reason, 'tool_calls');
    assert.equal(final.choices[0].message.tool_calls[0].function.name, 'example');
    run.terminal();
  });
}
module.exports = { registerCases };
