// Copy beside the clean consumer's node_modules, then run with Node: the installed tarball offers hosted
// sandboxes from the root and from "@future-agi/sdk/sandbox", in ESM and CJS, without touching the network.
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
globalThis.fetch = () => { throw new Error("Sandbox consumer checks must not use the network"); };
const METHODS = [
  "list", "create", "connect", "getInfo", "update", "kill", "hibernate", "resume", "settings.get", "networkPolicy.get",
  "networkPolicy.update", "files.list", "files.read", "files.write", "files.remove", "files.download", "files.upload",
  "files.rename", "files.makeDir", "snapshots.list", "snapshots.create", "snapshots.restore", "activity.list",
  "commands.run", "commands.cancel",
];
const at = (root, dotted) => dotted.split(".").reduce((node, part) => (node == null ? undefined : node[part]), root);

for (const [sdk, sandbox] of [
  [await import("@future-agi/sdk"), await import("@future-agi/sdk/sandbox")],
  [require("@future-agi/sdk"), require("@future-agi/sdk/sandbox")],
]) {
  for (const name of ["FutureAGIClient", "Sandbox", "SandboxError", "CommandResult", "CommandIncompleteError", "CommandFailedError"]) {
    assert.equal(typeof sdk[name], "function", name);
  }
  assert.equal(sandbox.Sandbox, sdk.Sandbox);
  assert.equal(sandbox.SandboxError, sdk.SandboxError);
  for (const name of [
    "Sandbox", "SandboxError", "NotFoundError", "ConflictError", "SandboxStateError", "ValidationError",
    "UnprocessableEntityError", "PreconditionRequiredError", "SandboxConnectionError",
  ]) {
    assert.equal(typeof sandbox[name], "function", name);
  }
  // the root's own status classes stay the root's; the sandbox ones extend them
  assert.ok(sandbox.NotFoundError.prototype instanceof sdk.NotFoundError);
  assert.ok(sandbox.ValidationError.prototype instanceof sdk.BadRequestError);
  assert.ok(sandbox.UnprocessableEntityError.prototype instanceof sdk.UnprocessableEntityError);
  assert.ok(sandbox.SandboxStateError.prototype instanceof sdk.SandboxStateError);
  assert.ok(sandbox.SandboxHibernatedError.prototype instanceof sdk.SandboxStateError);
  for (const name of ["create", "connect", "list", "settings"]) assert.equal(typeof sdk.Sandbox[name], "function", name);
  const client = new sdk.FutureAGIClient({ apiKey: "test-key", secretKey: "test-secret", baseUrl: "http://127.0.0.1:9" });
  for (const view of [client, client.withOptions({ retries: 0 })]) {
    assert.equal("sandboxes" in view, true);
    for (const method of METHODS) assert.equal(typeof at(view.sandboxes, method), "function", method);
    assert.equal(at(view.sandboxes, "settings.update"), undefined);
  }
}
console.log("Installed tarball: ESM/CJS sandbox imports, root names and client.sandboxes present");
