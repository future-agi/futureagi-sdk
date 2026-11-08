import { test } from 'node:test';
import { createRequire } from 'node:module';
import { resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import cases from './transport-boundary-cases.cjs';

const root = process.env.GATEWAY_BUILD_ROOT ?? fileURLToPath(new URL('../../dist/gateway/', import.meta.url));
const require = createRequire(import.meta.url);
const cjs = require(resolve(root, 'cjs/index.js'));
const esm = await import(pathToFileURL(resolve(root, 'esm/index.js')).href);
for (const [mode, api] of [['CJS', cjs], ['ESM', esm]]) {
  const route = mode === 'CJS' ? require(resolve(root, 'cjs/react/route.js')) : await import(pathToFileURL(resolve(root, 'esm/react/route.js')).href);
  cases.registerCases(api, (name, run) => test(`${mode}: ${name}`, run), route.routeStream);
}
