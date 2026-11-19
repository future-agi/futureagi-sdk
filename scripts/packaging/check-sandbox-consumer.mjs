// Copy beside the clean consumer's node_modules, then run with Node.
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
globalThis.fetch = () => { throw new Error("Sandbox absence checks must not use the network"); };
for (const sdk of [await import("@future-agi/sdk"), require("@future-agi/sdk")]) {
  const client = new sdk.FutureAGIClient({ apiKey: "test-key", secretKey: "test-secret", baseUrl: "http://127.0.0.1:9" });
  assert.equal("sandboxes" in client, false);
  assert.equal("sandboxes" in client.withOptions({ retries: 0 }), false);
  for (const name of ["Sandbox", "AsyncSandbox", "SandboxesClient"]) assert.equal(name in sdk, false);
}
for (const subpath of ["sandboxes", "sandboxes/types", "sandboxes/commands", "sandboxes/files"]) {
  const name = `@future-agi/sdk/${subpath}`;
  await assert.rejects(import(name), { code: "ERR_PACKAGE_PATH_NOT_EXPORTED" });
  assert.throws(() => require(name), { code: "ERR_PACKAGE_PATH_NOT_EXPORTED" });
}
console.log("Installed tarball: ESM/CJS sandbox imports and accessors absent");
