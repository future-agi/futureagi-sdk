import { test } from 'node:test';
import { createRequire } from 'node:module';
import { resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import cases from './request-cancellation-cases.cjs';

const root = process.env.GATEWAY_BUILD_ROOT ?? fileURLToPath(new URL('../../dist/gateway/', import.meta.url));
const require = createRequire(import.meta.url);
for (const mode of ['cjs', 'esm']) {
  const entry = resolve(root, mode, 'index.js');
  const api = mode === 'cjs' ? require(entry) : await import(pathToFileURL(entry).href);
  cases.registerCases(api, (name, run) => test(`${mode.toUpperCase()}: ${name}`, run));
}
