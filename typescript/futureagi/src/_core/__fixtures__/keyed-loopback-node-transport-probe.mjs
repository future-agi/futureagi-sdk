import assert from "node:assert/strict";
import Module, { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const requireHere = createRequire(import.meta.url);
const parts = {
  root: new URL("../../index.ts", import.meta.url),
  platform: new URL("../../platform/index.ts", import.meta.url),
};

function hideUndiciPackage() {
  const check = (id) => {
    if (id === "undici" || id.startsWith("undici/")) {
      throw Object.assign(new Error(`Cannot find module '${id}'`), { code: "MODULE_NOT_FOUND" });
    }
  };
  const resolve = Module._resolveFilename;
  Module._resolveFilename = function (id, ...args) {
    check(id);
    return resolve.call(this, id, ...args);
  };
  assert.throws(() => requireHere.resolve("undici"), { code: "MODULE_NOT_FOUND" });

  if (Module.registerHooks) {
    Module.registerHooks({ resolve(id, context, next) { check(id); return next(id, context); } });
    assert.throws(() => import.meta.resolve("undici"), { code: "MODULE_NOT_FOUND" });
  }
}

async function loadSDK(mode) {
  if (mode.startsWith("request-")) assert.equal(typeof globalThis.Request, "function");
  if (mode === "request-cjs") {
    const loaded = Object.fromEntries(Object.entries(parts).map(([name, url]) => [name, requireHere(fileURLToPath(url))]));
    assert.equal(Object.prototype.toString.call(loaded.root), "[object Object]");
    return loaded;
  }
  assert.ok(mode === "esm" || mode === "request-esm");
  const imports = Object.entries(parts).map(([name, url]) => `import * as ${name} from ${JSON.stringify(url.href)};`);
  const entry = `${imports.join("\n")}\nexport { root, platform };`;
  const loaded = await import(`data:text/javascript,${encodeURIComponent(entry)}`);
  assert.equal(Object.prototype.toString.call(loaded.root), "[object Module]");
  return loaded;
}

const { PROBE_MODE: mode, PROBE_SENDER: sender, PROBE_BASE: baseUrl } = process.env;
const [apiKey, secretKey] = JSON.parse(process.env.PROBE_MARKERS);
hideUndiciPackage();
const sdk = mode === "runtime-fetch" ? undefined : await loadSDK(mode);
const credentials = { apiKey, secretKey };
const url = `${baseUrl}/probe`;
const sends = {
  "runtime-fetch": async () => {
    const response = await fetch(url, {
      headers: { "X-Api-Key": apiKey, "X-Secret-Key": secretKey },
      signal: AbortSignal.timeout(3000),
    });
    assert.equal(response.status, 200);
    await response.text();
  },
  platform: () => new sdk.platform.Client({ ...credentials, baseUrl, maxRetries: 0, timeout: 3000 }).request("GET", "/probe"),
};
assert.equal(typeof sends[sender], "function");
let outcome = "sent";
try {
  await sends[sender]();
} catch (error) {
  outcome = [error.name, error.code, error.cause?.code].filter(Boolean).join(":");
}
process.stdout.write(`${JSON.stringify({ outcome })}\n`);
