// Copy this file into a clean consumer of the built npm tarball before running.
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { readFileSync } from "node:fs";
const require = createRequire(import.meta.url);
const esm = await import("@future-agi/sdk");
const cjs = require("@future-agi/sdk");
for (const sdk of [esm, cjs]) {
  const client = new sdk.FutureAGIClient({
    baseUrl: "http://127.0.0.1:9",
    fetch() { throw new Error("Absence checks must not send a request"); },
  });
  for (const target of [client, client.withOptions({ retries: 0 })]) {
    assert.equal("deployments" in target, false);
    assert.equal(target.deployments, undefined);
  }
  for (const name of ["Deployment", "Deployments", "DeploymentsClient", "deployments"]) {
    assert.equal(name in sdk, false);
  }
}
for (const subpath of ["deployments", "deployments/index.js", "dist/esm/deployments/index.js", "dist/src/deployments.js"]) {
  const name = `@future-agi/sdk/${subpath}`;
  await assert.rejects(import(name), { code: "ERR_PACKAGE_PATH_NOT_EXPORTED" });
  assert.throws(() => require(name), { code: "ERR_PACKAGE_PATH_NOT_EXPORTED" });
}
for (const format of ["esm", "src", "esnext"]) {
  const declaration = readFileSync(new URL(`./node_modules/@future-agi/sdk/dist/${format}/futureagi-client.d.ts`, import.meta.url), "utf8");
  assert.doesNotMatch(declaration, /\bdeployments\s*[(:]/);
}
console.log("Installed TypeScript deployment absence: PASS (ESM, CJS, copies, imports, declarations)");
