'use strict';
const assert = require('node:assert/strict');
const GUIDANCE = 'check whether the request was applied before retrying';
const chunk = text => ({ id: 'cancel-test', object: 'chat.completion.chunk', created: 1,
  model: 'test-model', choices: [{ index: 0, delta: { content: text }, finish_reason: null }] });
const frame = text => new TextEncoder().encode(`data: ${JSON.stringify(chunk(text))}\n\n`);
const tick = () => new Promise(resolve => setTimeout(resolve, 0));

function observed(promise) {
  return promise.then(value => ({ value }), error => ({ error }));
}
async function promptly(promise) {
  let timer;
  try {
    return await Promise.race([promise, new Promise((_, reject) => {
      timer = setTimeout(() => reject(new Error('cancellation did not settle promptly')), 250);
    })]);
  } finally { clearTimeout(timer); }
}
function isAbort(result) {
  assert.ok(result.error, 'request must fail rather than complete');
  assert.equal(result.error.name, 'AbortError');
  assert.ok(!result.error.message.toLowerCase().includes(GUIDANCE));
  assert.ok(!result.error.message.includes('synthetic-private-reason'));
  assert.equal(result.error.cause, undefined);
  assert.ok(result.error.remedy == null);
}
function transport({ headersPending = false, json = false, status = 200 } = {}) {
  let controller, release, signal, closed = false;
  const state = { calls: 0, upstreamAborts: 0, bodyCancels: 0 };
  const body = new ReadableStream({
    start(value) { controller = value; },
    cancel() { closed = true; state.bodyCancels++; },
  });
  const response = new Response(body, { status,
    headers: { 'content-type': json ? 'application/json' : 'text/event-stream' } });
  const fetch = async (_url, init) => {
    state.calls++; signal = init.signal;
    const abort = () => {
      state.upstreamAborts++;
      if (!closed) { closed = true; controller.error(signal.reason); }
      if (release) release();
    };
    signal.addEventListener('abort', abort, { once: true });
    if (signal.aborted) abort();
    if (headersPending) await new Promise(resolve => { release = resolve; });
    if (signal.aborted) throw signal.reason;
    return response;
  };
  return { fetch, state, response, get signal() { return signal; },
    push(text) { if (!closed) controller.enqueue(frame(text)); },
    pushBytes(value) { if (!closed) controller.enqueue(new TextEncoder().encode(value)); },
    finish() { if (release) release(); if (!closed) { closed = true; controller.close(); } },
  };
}
function clientFor(api, fetch, extra = {}) {
  const retries = [], errors = [];
  const client = new api.AgentCC({ apiKey: 'synthetic-test-key', baseUrl: 'https://gateway.invalid',
    fetch, timeout: 10_000, maxRetries: 3,
    callbacks: [{ onRetry(...args) { retries.push(args); }, onError(_request, error) { errors.push(error); } }], ...extra });
  return { client, retries, errors };
}
function trackListeners(signal) {
  const active = new Set(), add = signal.addEventListener, remove = signal.removeEventListener;
  signal.addEventListener = function (type, listener, options) {
    if (type === 'abort') active.add(listener);
    return add.call(this, type, listener, options);
  };
  signal.removeEventListener = function (type, listener, options) {
    if (type === 'abort') active.delete(listener);
    return remove.call(this, type, listener, options);
  };
  return active;
}

function registerCases(api, test) {
  for (const fallback of [false, true]) {
    const register = (name, run) => test(`${fallback ? 'Node 18 fallback' : 'native composition'}: ${name}`, async () => {
      const descriptor = Object.getOwnPropertyDescriptor(AbortSignal, 'any');
      if (fallback) Object.defineProperty(AbortSignal, 'any', { value: undefined, configurable: true });
      try { await run(); }
      finally { if (descriptor) Object.defineProperty(AbortSignal, 'any', descriptor); else delete AbortSignal.any; }
    });
    register('caller already aborted never sends and ignores arbitrary reason', async () => {
      const caller = new AbortController(); caller.abort(new Error('synthetic-private-reason'));
      let sends = 0;
      const { client, retries } = clientFor(api, async () => { sends++; return Response.json({ ok: true }); });
      isAbort(await observed(client.request({ method: 'POST', path: '/test', signal: caller.signal })));
      assert.equal(sends, 0); assert.equal(retries.length, 0);
    });
    register('caller abort while awaiting headers reaches fetch and is terminal', async () => {
      const upstream = transport({ headersPending: true }), caller = new AbortController();
      const { client, retries, errors } = clientFor(api, upstream.fetch);
      const result = observed(client.request({ method: 'POST', path: '/test', signal: caller.signal }));
      try {
        await tick(); caller.abort(new Error('synthetic-private-reason'));
        isAbort(await promptly(result));
        assert.equal(upstream.signal.aborted, true); assert.equal(upstream.state.upstreamAborts, 1);
        assert.equal(upstream.state.calls, 1); assert.equal(retries.length, 0);
        for (const error of errors) isAbort({ error });
      } finally { upstream.finish(); await result; }
    });
    for (const mode of ['json', 'error-json', 'sse', 'stream-json']) {
      register(`caller abort mid-body (${mode}) has no body-failure guidance`, async () => {
        const upstream = transport({ json: mode !== 'sse', status: mode === 'error-json' ? 503 : 200 });
        const caller = new AbortController(), { client, retries, errors } = clientFor(api, upstream.fetch);
        let result;
        try {
          if (mode === 'sse' || mode === 'stream-json') {
            const response = await client.requestStream({ method: 'POST', path: '/test', signal: caller.signal });
            result = observed(new api.Stream(response)[Symbol.asyncIterator]().next());
          } else result = observed(client.request({ method: 'POST', path: '/test', signal: caller.signal }));
          await tick(); assert.equal(upstream.response.body.locked, true);
          caller.abort({ reason: 'synthetic-private-reason' });
          isAbort(await promptly(result));
          assert.equal(upstream.signal.aborted, true); assert.equal(upstream.state.upstreamAborts, 1);
          assert.equal(upstream.state.calls, 1); assert.equal(retries.length, 0);
          for (const error of errors) isAbort({ error });
        } finally { upstream.finish(); if (result) await result; }
      });
    }
    for (const manager of [false, true]) {
      register(`${manager ? 'StreamManager' : 'Stream'}.abort cancels locked fetch and stops iteration`, async () => {
        const upstream = transport(), { client, retries } = clientFor(api, upstream.fetch);
        const params = { model: 'test-model', messages: [] };
        const stream = manager ? await client.chat.completions.stream(params)
          : await client.chat.completions.create({ ...params, stream: true });
        const iterator = stream[Symbol.asyncIterator]();
        let pending;
        try {
          upstream.push('first'); assert.equal((await iterator.next()).value.choices[0].delta.content, 'first');
          pending = observed(iterator.next()); await tick();
          assert.equal(upstream.response.body.locked, true);
          stream.abort(); stream.abort();
          assert.equal(upstream.signal.aborted, true);
          assert.equal(upstream.state.upstreamAborts, 1);
          isAbort(await promptly(pending));
          upstream.push('must not arrive');
          assert.equal((await iterator.next()).done, true);
          assert.equal(upstream.state.calls, 1); assert.equal(retries.length, 0);
        } finally { upstream.finish(); if (pending) await pending; await iterator.return(); }
      });
    }
    register('abort discards already buffered SSE chunks', async () => {
      const upstream = transport(), { client } = clientFor(api, upstream.fetch);
      const stream = new api.Stream(await client.requestStream({ method: 'POST', path: '/test' }));
      const iterator = stream[Symbol.asyncIterator]();
      try {
        upstream.pushBytes(new TextDecoder().decode(frame('first')) + new TextDecoder().decode(frame('second')));
        assert.equal((await iterator.next()).value.choices[0].delta.content, 'first');
        stream.abort(); isAbort(await observed(iterator.next()));
      } finally { upstream.finish(); await iterator.return(); }
    });
    register('caller abort between headers and iteration is AbortError, not consumed misuse', async () => {
      const upstream = transport(), caller = new AbortController(), { client } = clientFor(api, upstream.fetch);
      try {
        const stream = new api.Stream(await client.requestStream({ method: 'POST', path: '/test', signal: caller.signal }));
        caller.abort(); isAbort(await promptly(observed(stream[Symbol.asyncIterator]().next())));
      } finally { upstream.finish(); }
    });
    register('timeout still terminates headers with an un-aborted caller signal', async () => {
      const upstream = transport({ headersPending: true }), caller = new AbortController();
      const { client, retries } = clientFor(api, upstream.fetch, { timeout: 20 });
      const result = observed(client.request({ method: 'POST', path: '/test', signal: caller.signal }));
      try {
        const { error } = await promptly(result);
        assert.ok(error instanceof api.APITimeoutError); assert.equal(caller.signal.aborted, false);
        assert.equal(upstream.signal.aborted, true); assert.equal(upstream.state.calls, 1);
        assert.equal(retries.length, 0);
      } finally { upstream.finish(); await result; }
    });
    register('timeout continues bounding a streaming body after headers', async () => {
      const upstream = transport(), caller = new AbortController();
      const { client } = clientFor(api, upstream.fetch, { timeout: 20 });
      try {
        const response = await client.requestStream({ method: 'POST', path: '/test', signal: caller.signal });
        const { error } = await promptly(observed(new api.Stream(response)[Symbol.asyncIterator]().next()));
        assert.ok(error instanceof api.StreamError); assert.equal(caller.signal.aborted, false);
        assert.equal(upstream.state.upstreamAborts, 1);
      } finally { upstream.finish(); }
    });
    register('caller abort during retry delay is prompt and sends no second attempt', async () => {
      const caller = new AbortController(); let attempts = 0;
      const { client } = clientFor(api, async () => {
        attempts++; return Response.json({ error: { message: 'busy' } }, { status: 429,
          headers: { 'x-agentcc-dispatched': 'false', 'retry-after': '0.5' } });
      }, { callbacks: [{ onRetry() { caller.abort(); } }] });
      const result = observed(client.request({ method: 'POST', path: '/test', signal: caller.signal }));
      isAbort(await promptly(result)); assert.equal(attempts, 1);
    });
  }
  test('standalone Stream.abort cancels its active reader', async () => {
    const upstream = transport(), stream = new api.Stream(upstream.response);
    const iterator = stream[Symbol.asyncIterator](), pending = observed(iterator.next());
    try {
      await tick(); stream.abort(); isAbort(await promptly(pending));
      assert.equal(upstream.state.bodyCancels, 1);
    } finally { upstream.finish(); await pending; await iterator.return(); }
  });
  test('standalone JSON Stream.abort cancels its active reader', async () => {
    const upstream = transport({ json: true }), stream = new api.Stream(upstream.response);
    const iterator = stream[Symbol.asyncIterator](), pending = observed(iterator.next());
    try {
      await tick(); assert.equal(upstream.response.body.locked, true);
      stream.abort(); isAbort(await promptly(pending));
      assert.equal(upstream.state.bodyCancels, 1);
    } finally { upstream.finish(); await pending; await iterator.return(); }
  });
  test('JSON stream text decoding preserves split UTF-8 and a leading BOM', async () => {
    const bytes = new TextEncoder().encode('﻿' + JSON.stringify(chunk('hello € 漢')));
    const body = new ReadableStream({ start(controller) {
      for (const byte of bytes) controller.enqueue(new Uint8Array([byte]));
      controller.close();
    } });
    const stream = new api.Stream(new Response(body, { headers: { 'content-type': 'application/json' } }));
    const chunks = [];
    for await (const value of stream) chunks.push(value);
    assert.equal(chunks.length, 1);
    assert.equal(chunks[0].choices[0].delta.content, 'hello € 漢');
  });
  test('fallback removes caller and timeout listeners after each parsed attempt', async () => {
    const any = Object.getOwnPropertyDescriptor(AbortSignal, 'any'), timeout = AbortSignal.timeout;
    const caller = new AbortController(), listeners = trackListeners(caller.signal), timeoutListeners = [];
    Object.defineProperty(AbortSignal, 'any', { value: undefined, configurable: true });
    AbortSignal.timeout = () => { const controller = new AbortController(); timeoutListeners.push(trackListeners(controller.signal)); return controller.signal; };
    try {
      for (const kind of ['json', 'stream', 'status', 'transport', 'decode']) {
        for (let i = 0; i < 15; i++) {
          let activeDuringFetch = -1;
          const { client } = clientFor(api, async () => {
            activeDuringFetch = listeners.size;
            if (kind === 'transport') throw new TypeError('synthetic transport failure');
            if (kind === 'status') return Response.json({ error: { message: 'refused' } }, { status: 400 });
            if (kind === 'decode') return new Response('{', { headers: { 'content-type': 'application/json' } });
            if (kind === 'stream') return new Response(frame('complete'), { headers: { 'content-type': 'text/event-stream' } });
            return Response.json({ ok: true });
          });
          const options = { method: 'POST', path: '/test', signal: caller.signal };
          if (kind === 'stream') {
            const stream = new api.Stream(await client.requestStream(options));
            for await (const _chunk of stream) { /* consume to completion */ }
          } else await observed(client.request(options));
          assert.equal(activeDuringFetch, 1, 'fallback must listen while the request is active');
          assert.equal(listeners.size, 0, `caller listener retained after ${kind}`);
          assert.ok(timeoutListeners.every(set => set.size === 0), `timeout listener retained after ${kind}`);
        }
      }
    } finally {
      if (any) Object.defineProperty(AbortSignal, 'any', any); else delete AbortSignal.any;
      AbortSignal.timeout = timeout;
    }
  });
}
module.exports = { registerCases, clientFor, transport, observed, promptly, isAbort, tick, chunk };
