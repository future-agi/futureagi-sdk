import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cpSync, mkdtempSync, rmSync } from 'node:fs';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import cases from './stream-adapter-boundary-cases.cjs';

const root = process.env.GATEWAY_BUILD_ROOT ?? fileURLToPath(new URL('../../dist/gateway/', import.meta.url));
const require = createRequire(import.meta.url);
// A second install of the package is a second module instance: same code, another path.
const copyRoot = mkdtempSync(join(tmpdir(), 'gateway-copy-'));
process.on('exit', () => rmSync(copyRoot, { recursive: true, force: true }));
for (const mode of ['cjs', 'esm']) cpSync(resolve(root, mode), resolve(copyRoot, mode), { recursive: true });
const builds = [];
for (const [label, base] of [['', root], ['-copy', copyRoot]]) {
  for (const mode of ['cjs', 'esm']) {
    const load = name => mode === 'cjs' ? require(resolve(base, mode, name)) : import(pathToFileURL(resolve(base, mode, name)).href);
    const api = await load('index.js');
    const adapters = { ...await load('nextjs.js'), ...await load('react/route.js'), ...await load('express.js') };
    builds.push({ mode: mode + label, api, adapters });
  }
}
const [cjs, esm, cjsCopy, esmCopy] = builds;
for (const build of [cjs, esm]) cases.registerCases(build.api, build.adapters, (name, run) => test(`${build.mode.toUpperCase()}: ${name}`, run));
for (const [from, to] of [[cjs, esm], [esm, cjs]]) {
  test(`${from.mode} producer -> ${to.mode} route reader`, async () => {
    const source = new from.api.Stream(cases.failureResponse('sse-decode', 200, null));
    const response = from.adapters.streamResponse(new from.api.StreamManager(source));
    const received = new Response(await response.text(), { headers: response.headers });
    const stream = await to.adapters.routeStream({ fetch: async () => received }, {});
    await assert.rejects(async () => { for await (const _chunk of stream) { /* consume */ } }, error => {
      assert.ok(error instanceof to.api.StreamError);
      assert.deepEqual(error.gatewayEvidence, cases.evidence(null));
      assert.equal(error.remedy, cases.GUIDANCE);
      assert.equal(error.message.split(cases.GUIDANCE).length - 1, 1);
      return true;
    });
  });
}
test('a copy of a build is a separate module instance', () => {
  assert.notEqual(cjs.api.StreamError, cjsCopy.api.StreamError);
  assert.notEqual(esm.api.StreamError, esmCopy.api.StreamError);
  assert.notEqual(cjs.api.StreamError, esm.api.StreamError);
});
// Client and adapter from different formats, and from two installs of one format.
for (const [from, to] of [[cjs, esm], [esm, cjs], [cjs, cjsCopy], [cjsCopy, cjs], [esm, esmCopy], [esmCopy, esm]]) {
  cases.registerInstanceCases(from.api, to.api, to.adapters, (name, run) => test(`${from.mode} client -> ${to.mode} adapter: ${name}`, run));
}
