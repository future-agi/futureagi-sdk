"use strict";
// Run from a consumer installed from the candidate tarball, WITHOUT any custom
// resolver condition: ordinary import() and require() load all five gateway
// entry points (react installed, so ./gateway/react loads too).
const assert = require("node:assert/strict");
(async () => {
  if (/--conditions|-C\b/.test(process.env.NODE_OPTIONS || "") || process.execArgv.some((arg) => arg.startsWith("--conditions") || arg === "-C")) {
    throw new Error("Run without custom resolver conditions");
  }
  for (const path of ["gateway", "gateway/testing", "gateway/express", "gateway/nextjs", "gateway/react"]) {
    const specifier = `@future-agi/sdk/${path}`;
    assert.match(require.resolve(specifier), /[\\/]dist[\\/]gateway[\\/]cjs[\\/]/, `${specifier} resolves to the CommonJS build`);
    const required = require(specifier);
    const imported = await import(specifier);
    assert.ok(Object.keys(required).length > 0, `${specifier} (require) has exports`);
    assert.ok(Object.keys(imported).length > 0, `${specifier} (import) has exports`);
  }
  assert.equal(typeof require("@future-agi/sdk/gateway").AgentCC, "function");
  assert.equal(typeof (await import("@future-agi/sdk/gateway")).AgentCC, "function");
  console.log("All five gateway entry points load with the default conditions (ESM and CJS)");
})().catch((error) => { console.error(error); process.exitCode = 1; });
