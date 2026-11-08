import { test } from 'node:test';
import assert from 'node:assert/strict';
import { getEventListeners } from 'node:events';
import { cpSync, mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { runInNewContext } from 'node:vm';
import helpers from './request-cancellation-cases.cjs';

const { clientFor, transport, observed, promptly, isAbort, tick, chunk } = helpers;
const root = process.env.GATEWAY_BUILD_ROOT ?? fileURLToPath(new URL('../../dist/gateway/', import.meta.url));
const require = createRequire(import.meta.url);
const copyRoot = mkdtempSync(join(tmpdir(), 'gateway-cancellation-copy-'));
process.on('exit', () => rmSync(copyRoot, { recursive: true, force: true }));
for (const mode of ['cjs', 'esm']) cpSync(resolve(root, mode), resolve(copyRoot, mode), { recursive: true });
const builds = [];
for (const [suffix, base] of [['', root], ['-copy', copyRoot]]) {
  for (const mode of ['cjs', 'esm']) {
    const entry = resolve(base, mode, 'index.js');
    builds.push({ label: mode + suffix, api: mode === 'cjs' ? require(entry) : await import(pathToFileURL(entry).href) });
  }
}
const [cjs, esm, cjsCopy, esmCopy] = builds;
const pairs = [[cjs, cjs], [esm, esm], [cjs, esm], [esm, cjs],
  [cjs, cjsCopy], [cjsCopy, cjs], [esm, esmCopy], [esmCopy, esm]];

test('duplicate installs and module formats really are different instances', () => {
  assert.notEqual(cjs.api.Stream, esm.api.Stream);
  assert.notEqual(cjs.api.Stream, cjsCopy.api.Stream);
  assert.notEqual(esm.api.Stream, esmCopy.api.Stream);
});

async function withComposition(fallback, run) {
  const descriptor = Object.getOwnPropertyDescriptor(AbortSignal, 'any');
  if (fallback) Object.defineProperty(AbortSignal, 'any', { value: undefined, configurable: true });
  try { await run(); }
  finally {
    if (descriptor) Object.defineProperty(AbortSignal, 'any', descriptor);
    else delete AbortSignal.any;
  }
}

for (const [from, to] of pairs) {
  const label = `${from.label} client -> ${to.label} consumer`;
  for (const fallback of [false, true]) for (const json of [false, true]) {
    for (const abort of ['caller-pending', 'caller-before-iteration', 'stream', 'manager']) {
      test(`${label}: ${fallback ? 'fallback' : 'native'} ${json ? 'JSON' : 'SSE'} ${abort}`, async () => {
        await withComposition(fallback, async () => {
          const upstream = transport({ json }), caller = new AbortController();
          const { client, retries } = clientFor(from.api, upstream.fetch);
          const response = await client.requestStream({ method: 'POST', path: '/test', signal: caller.signal });
          const stream = new to.api.Stream(response);
          const consumer = abort === 'manager' ? new to.api.StreamManager(stream) : stream;
          const iterator = consumer[Symbol.asyncIterator]();
          let pending;
          try {
            if (abort === 'caller-before-iteration') {
              caller.abort({ reason: 'synthetic-private-reason' });
              pending = observed(iterator.next());
            } else {
              pending = observed(iterator.next());
              await tick();
              assert.equal(response.body.locked, true);
              if (abort === 'caller-pending') caller.abort({ reason: 'synthetic-private-reason' });
              else { consumer.abort(); consumer.abort(); }
            }
            const result = await promptly(pending);
            isAbort(result);
            assert.equal(upstream.signal.aborted, true, 'the originating fetch must be aborted');
            assert.equal(upstream.state.upstreamAborts, 1);
            assert.equal(upstream.state.calls, 1);
            assert.equal(retries.length, 0);
            assert.equal((await iterator.next()).done, true);
          } finally {
            caller.abort(); upstream.finish();
            if (pending) await pending;
            await iterator.return();
          }
        });
      });
    }
  }

  for (const kind of ['sse', 'json', 'early-return', 'decode-error']) {
    test(`${label}: fallback retains zero caller or timeout listeners after ${kind}`, async () => {
      await withComposition(true, async () => {
        const timeout = AbortSignal.timeout, timeouts = [], caller = new AbortController();
        AbortSignal.timeout = () => {
          const controller = new AbortController(); timeouts.push(controller.signal); return controller.signal;
        };
        try {
          for (let i = 0; i < 4; i++) {
            const data = kind === 'json' ? JSON.stringify(chunk('complete'))
              : kind === 'decode-error' ? 'data: {\n\n'
              : `data: ${JSON.stringify(chunk('complete'))}\n\n`;
            const { client } = clientFor(from.api, async () => {
              assert.equal(getEventListeners(caller.signal, 'abort').length, 1);
              return new Response(data, { headers: { 'content-type': kind === 'json' ? 'application/json' : 'text/event-stream' } });
            });
            const response = await client.requestStream({ method: 'POST', path: '/test', signal: caller.signal });
            const stream = new to.api.Stream(response);
            const consume = async () => { for await (const _value of stream) { if (kind === 'early-return') break; } };
            if (kind === 'decode-error') await assert.rejects(consume, { name: 'StreamError' });
            else await consume();
            assert.equal(getEventListeners(caller.signal, 'abort').length, 0, 'caller listener retained');
            assert.ok(timeouts.every(signal => getEventListeners(signal, 'abort').length === 0), 'timeout listener retained');
          }
        } finally { caller.abort(); AbortSignal.timeout = timeout; }
      });
    });
  }

  for (const abort of ['manager', 'caller', 'stream']) for (const count of [1, 2, 3, 4, 5]) {
    test(`${label}: ${abort} abort after event ${count} stops the very next public yield`, async () => {
      const upstream = transport(), caller = new AbortController();
      const { client } = clientFor(from.api, upstream.fetch);
      const stream = new to.api.Stream(await client.requestStream({ method: 'POST', path: '/test', signal: caller.signal }));
      const manager = new to.api.StreamManager(stream), iterator = manager.events();
      const first = chunk('first');
      first.choices[0].delta.tool_calls = [0, 1].map(index => ({ index, id: `tool-${index}`, type: 'function', function: { name: 'lookup', arguments: '{}' } }));
      first.usage = { prompt_tokens: 2, completion_tokens: 1, total_tokens: 3 };
      upstream.pushBytes([first, chunk('last')].map(value => `data: ${JSON.stringify(value)}\n\n`).join('') + 'data: [DONE]\n\n');
      try {
        const expected = ['content', 'tool_call', 'tool_call', 'usage', 'content'];
        for (let i = 0; i < count; i++) assert.equal((await iterator.next()).value.type, expected[i]);
        if (abort === 'manager') manager.abort();
        else if (abort === 'stream') stream.abort();
        else caller.abort({ reason: 'synthetic-private-reason' });
        isAbort(await promptly(observed(iterator.next())));
        assert.equal((await iterator.next()).done, true);
        assert.equal(upstream.signal.aborted, true);
        assert.equal(upstream.state.calls, 1);
      } finally { caller.abort(); upstream.finish(); await iterator.return(); }
    });
  }

  for (const abort of ['manager', 'stream']) {
    test(`${label}: standalone foreign Stream stops buffered events after ${abort} abort`, async () => {
      const first = chunk('standalone');
      first.choices[0].delta.tool_calls = [{ index: 0, function: { name: 'lookup', arguments: '{}' } }];
      const response = new Response(`data: ${JSON.stringify(first)}\n\n`, { headers: { 'content-type': 'text/event-stream' } });
      const stream = new from.api.Stream(response), manager = new to.api.StreamManager(stream);
      const iterator = manager.events();
      try {
        assert.equal((await iterator.next()).value.type, 'content');
        if (abort === 'manager') manager.abort(); else stream.abort();
        isAbort(await promptly(observed(iterator.next())));
        assert.equal((await iterator.next()).done, true);
      } finally { await iterator.return(); }
    });
  }

  test(`${label}: normal event expansion still yields content, tools, usage and done`, async () => {
    const first = chunk('complete');
    first.choices[0].delta.tool_calls = [{ index: 0, function: { name: 'lookup', arguments: '{}' } }];
    first.usage = { prompt_tokens: 2, completion_tokens: 1, total_tokens: 3 };
    const { client } = clientFor(from.api, async () => new Response(`data: ${JSON.stringify(first)}\n\ndata: [DONE]\n\n`, { headers: { 'content-type': 'text/event-stream' } }));
    const manager = new to.api.StreamManager(new to.api.Stream(await client.requestStream({ method: 'POST', path: '/test' })));
    const types = [];
    for await (const event of manager.events()) types.push(event.type);
    assert.deepEqual(types, ['content', 'tool_call', 'usage', 'done']);
    assert.equal(manager.getFinalText(), 'complete');
  });
}

// Evaluate the small dependency-free module in fresh globals to exercise store
// initialization without replacing the process's established shared registry.
const registrySource = readFileSync(resolve(root, 'cjs', 'request-cancellation.js'), 'utf8');
const storeKey = Symbol.for('futureagi.gateway.request-cancellation.v1');
function loadRegistry(host = {}) {
  const exports = {};
  runInNewContext(registrySource, { exports, globalThis: host, AbortController, AbortSignal, DOMException });
  return exports;
}

test('registry survives late module loads and ignores patched WeakMap instance methods', () => {
  const host = {}, first = loadRegistry(host), response = {}, cancellation = {};
  first.setResponseCancellation(response, cancellation);
  const descriptor = Object.getOwnPropertyDescriptor(host, storeKey);
  assert.ok(descriptor, 'publish a process-wide cancellation registry');
  assert.equal(descriptor.writable, false);
  assert.equal(descriptor.configurable, false);
  assert.equal(descriptor.enumerable, false);
  const registry = descriptor.value;
  registry.get = registry.set = () => { throw new Error('patched instance method'); };
  const second = loadRegistry(host);
  assert.equal(host[storeKey], registry);
  assert.equal(second.getResponseCancellation(response), cancellation);
  const other = {};
  second.setResponseCancellation(other, cancellation);
  assert.equal(first.getResponseCancellation(other), cancellation);
});

test('registry accepts a real WeakMap from another realm without replacing it', () => {
  const registry = runInNewContext('new WeakMap()'), host = { [storeKey]: registry };
  const api = loadRegistry(host), response = {}, cancellation = {};
  api.setResponseCancellation(response, cancellation);
  assert.equal(host[storeKey], registry);
  assert.equal(WeakMap.prototype.get.call(registry, response), cancellation);
});

for (const existing of [undefined, null, {}, { get() { throw new Error('look-alike must not run'); } }]) {
  test(`an occupied non-store global slot is never replaced (${String(existing)})`, () => {
    const host = { [storeKey]: existing }, api = loadRegistry(host), response = {}, cancellation = {};
    api.setResponseCancellation(response, cancellation);
    assert.equal(host[storeKey], existing);
    assert.equal(api.getResponseCancellation(response), cancellation);
  });
}

test('a sealed global falls back to a usable private cancellation registry', () => {
  const api = loadRegistry(Object.preventExtensions({})), response = {}, cancellation = {};
  api.setResponseCancellation(response, cancellation);
  assert.equal(api.getResponseCancellation(response), cancellation);
});
