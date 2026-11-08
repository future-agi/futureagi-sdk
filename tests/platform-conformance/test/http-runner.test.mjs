// The http runner end to end against a local stand-in for the platform API: credentials by mode,
// cross-tenant repeats, contract checks of the answers (and of stream frames), receipts without keys.
import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { after, before, test } from "node:test";
import { buildContract } from "../lib/contract.mjs";
import { createExecutor, splitDrift } from "../runners/http/execute.mjs";
import { main } from "../runners/http/run.mjs";

let server;
let base;
let dir;
const KEYS = { "key-a": "A", "key-b": "B" };
const SANDBOXES = { "sbx-a": "A", "sbx-b": "B" };
const ORG_IDS = { A: "oa", B: "ob" };
let seenScopes = [];
const SANDBOX = { type: "object", required: ["id", "state"], properties: { id: { type: "string" }, state: { type: "string" } } };
const sdk = (family, method) => ({ "x-omega-sdk": { family, method } });
const openapi = {
  openapi: "3.1.0",
  paths: {
    "/workspace/capabilities": { get: { ...sdk("platform", "capabilities.get"), responses: { 200: { content: { "application/json": { schema: { type: "object", required: ["features"], properties: { features: { type: "object" } } } } } } } } },
    "/workspace/sandboxes/{id}": { get: { ...sdk("sandboxes", "getInfo"), responses: { 200: { content: { "application/json": { schema: { type: "object", required: ["sandbox"], properties: { sandbox: SANDBOX } } } } } } } },
    "/workspace/conversations/{id}/events": {
      get: {
        ...sdk("runs", "events"),
        "x-omega-stream": { kind: "sse-get", resume: "last-event-id", events: "#/components/schemas/Frame" },
        responses: { 200: { content: { "text/event-stream": { schema: { type: "string" } } } } },
      },
    },
  },
  components: {
    schemas: {
      Frame: { oneOf: [{ type: "object", required: ["event", "data"], properties: { event: { const: "done" }, id: { type: "string" }, data: { type: "object", required: ["type"], properties: { type: { enum: ["done"] } } } } }] },
    },
  },
};
before(async () => {
  server = http.createServer((req, res) => {
    const org = KEYS[(req.headers.authorization ?? "").replace(/^Bearer /, "")];
    const send = (status, body) => (res.writeHead(status, { "content-type": "application/json", "x-request-id": `req-${status}` }), res.end(JSON.stringify(body)));
    if (!org) return send(401, { error: { code: "unauthenticated", message: "no" }, code: "unauthenticated", request_id: "ee-1" });
    seenScopes.push(`${org}:${req.headers["x-omega-org"]}`);
    if (req.headers["x-omega-org"] && req.headers["x-omega-org"] !== ORG_IDS[org]) return send(403, { error: { code: "workspace_scope_denied", message: "no" }, code: "workspace_scope_denied", request_id: "ee-4" });
    if (req.url === "/workspace/capabilities") return send(200, { features: {}, request_id: "ee-2" });
    const m = /^\/workspace\/sandboxes\/([^/]+)$/.exec(req.url);
    if (m && SANDBOXES[m[1]] === org) return send(200, { sandbox: { id: m[1], state: "running" } });
    const e = /^\/workspace\/conversations\/([^/]+)\/events$/.exec(req.url);
    if (e) {
      res.writeHead(200, { "content-type": "text/event-stream" });
      res.write(`event: done\nid: 1\ndata: ${JSON.stringify({ type: "done", seq: 1 })}\n\n`);
      return res.end();
    }
    return send(404, { error: { code: "sandbox_not_found", message: "no" }, code: "sandbox_not_found", request_id: "ee-3" });
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  base = `http://127.0.0.1:${server.address().port}`;
  dir = mkdtempSync(path.join(os.tmpdir(), "sdkconf-http-"));
  writeFileSync(path.join(dir, "openapi.json"), JSON.stringify(openapi));
  writeFileSync(path.join(dir, "fixtures.json"), JSON.stringify({ ee: { A: { orgId: "oa", workspaceId: "wa", keys: { owner: "key-a" } }, B: { orgId: "ob", workspaceId: "wb", keys: { owner: "key-b" } } } }));
  writeFileSync(path.join(dir, "world.json"), JSON.stringify({ A: { sandbox: "sbx-a", conversation: "c-a" }, B: { sandbox: "sbx-b", conversation: "c-b" } }));
});

after(() => {
  server.close();
  rmSync(dir, { recursive: true, force: true });
});

const args = (out, only, extra = []) => ["--target", "ee", "--base", base, "--mode", "ee-key", "--fixtures", path.join(dir, "fixtures.json"), "--world", path.join(dir, "world.json"), "--openapi", path.join(dir, "openapi.json"), "--exporter", "http://127.0.0.1:4318", "--out", out, "--only", only, "--run-id", "20261020t000000z-httptest", ...extra];
const summaryOf = (out) => JSON.parse(readFileSync(path.join(out, "summary.json"), "utf8"));

test("plain cases pass: own sandbox 200 (contract-checked), the other org's 404 20/20, and nothing secret is written", async () => {
  const out = path.join(dir, "plain");
  const code = await main(args(out, "platform.capabilities.get,sandboxes.get.ok,sandboxes.get.cross-tenant"));
  const s = summaryOf(out);
  assert.equal(code, 0, JSON.stringify(s.failed));
  assert.equal(s.counts.pass, 3);
  const lines = readFileSync(path.join(out, "results.jsonl"), "utf8");
  const cross = lines.split("\n").filter(Boolean).map((l) => JSON.parse(l)).find((r) => r.id === "sandboxes.get.cross-tenant");
  assert.equal(cross.attempts.length, 20);
  assert.ok(cross.attempts.every((a) => a.status === 404 && a.errorClass === "NotFoundError" && a.upstreamRequestId === "ee-3"));
  assert.ok(!lines.includes("key-a") && !lines.includes("key-b"));
  assert.equal(s.egressGuard.trips.length, 0);
});

test("a contract mismatch fails the case even when the status is right", async () => {
  SANDBOXES["sbx-a"] = "A";
  const original = server.listeners("request")[0];
  server.removeAllListeners("request");
  server.on("request", (req, res) => (req.url === "/workspace/capabilities" ? (res.writeHead(200, { "content-type": "application/json" }), res.end("{\"nope\":1}")) : original(req, res)));
  try {
    const out = path.join(dir, "drift");
    assert.equal(await main(args(out, "platform.capabilities.get")), 1);
    assert.match(summaryOf(out).failed[0].failures.join(" "), /contract: response: missing required features|features: missing/);
  } finally {
    server.removeAllListeners("request");
    server.on("request", original);
  }
});

test("the runner refuses a production base URL before sending anything", async () => {
  await assert.rejects(main(["--target", "gateway", "--base", "https://gateway.futureagi.com/omega/api", "--mode", "none", "--exporter", "http://127.0.0.1:1", "--openapi", "x", "--out", dir]), /production Future AGI host/);
});

test("an undeclared answer field is drift recorded for the contract owner; a missing required field is a failure", () => {
  const split = splitDrift({ checked: true }, ["contract: response.items[3]: unknown property extra", "contract: response.items[4]: unknown property extra", "contract: response: missing required id"]);
  assert.deepEqual(split.drift, ["response.items[]: unknown property extra"]);
  assert.deepEqual(split.failures, ["contract: response: missing required id"]);
});

test("a missing required field the case declares as known drift is owned drift; an undeclared one still fails", () => {
  const known = { owner: "contract", reason: "settings never saved", messages: ["response: missing required updatedAt"] };
  const split = splitDrift({ checked: true }, ["contract: response: missing required updatedAt", "contract: response: missing required id"], known);
  assert.deepEqual(split.drift, ["response: missing required updatedAt (known, owner contract)"]);
  assert.deepEqual(split.failures, ["contract: response: missing required id"]);
  assert.deepEqual(splitDrift({ checked: true }, ["contract: response: missing required updatedAt"]).failures, ["contract: response: missing required updatedAt"]);
});

test("a setup the declared gap breaks is xfail with its owner; the same setup break without a declaration fails", async () => {
  const fixtures = JSON.parse(readFileSync(path.join(dir, "fixtures.json"), "utf8"));
  const run = createExecutor({ target: "ee", base, contract: buildContract({ openapi }), fixtures, world: { A: { sandbox: "sbx-a" } }, runId: "20261020t000000z-setup", fetchImpl: fetch });
  const make = (expectedFailure) => ({
    id: "t.setup-gap", tenant: { org: "A", role: "owner" }, tags: ["deterministic"], sdk: { family: "sandboxes", method: "get" },
    op: { method: "GET", path: "/workspace/sandboxes/{sandbox}" }, call: { params: { sandbox: "${res.sandbox}" } }, expect: { status: 200 },
    setup: [{ op: { method: "PUT", path: "/workspace/sandboxes/{sandbox}/folders/{filePath}" }, params: { sandbox: "${res.sandbox}", filePath: "d" }, expectStatus: [200, 201] }],
    ...(expectedFailure ? { expectedFailure } : {}),
  });
  const gap = await run(make({ owner: "server", reason: "workspace not writable" }), "ee-key");
  assert.equal(gap.verdict, "xfail");
  assert.equal(gap.expectedFailure.owner, "server");
  assert.match(gap.failures[0], /^setup: PUT .* answered 404/);
  assert.equal((await run(make(null), "ee-key")).verdict, "fail");
});

test("a forged scope selector: org B's key goes out with org A's selectors, and EE's 403 is the expected answer", async () => {
  seenScopes = [];
  const out = path.join(dir, "forged");
  const code = await main(args(out, "sandboxes.get.forged-scope,sandboxes.get.cross-tenant"));
  const s = summaryOf(out);
  assert.equal(code, 0, JSON.stringify(s.failed));
  assert.equal(s.counts.pass, 2);
  assert.equal(seenScopes.filter((v) => v === "B:oa").length, 20, "B's key with A's org selector, 20 times");
  assert.equal(seenScopes.filter((v) => v === "B:ob").length, 20, "the plain cross-tenant case keeps B's own selector");
});
