// The runner shells load an SDK BY PATH and run cases through it: smoked with the stub SDKs in
// this directory only (a TS client, a Python client and a test kit), against a local stand-in.
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { after, before, test } from "node:test";
import { fileURLToPath } from "node:url";
import { main } from "../sdk/run.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ONLY = "platform.capabilities.get,sandboxes.list.ok,sandboxes.get.unknown-id";
let server;
let base;
let scratch;
let fixturesFile;
let seen = [];

before(async () => {
  server = http.createServer((req, res) => {
    seen.push({ url: req.url, auth: req.headers.authorization });
    const send = (status, body) => (res.writeHead(status, { "content-type": "application/json" }), res.end(JSON.stringify(body)));
    if (req.headers.authorization !== "Bearer stub-key-a") return send(401, { error: { code: "unauthenticated" }, code: "unauthenticated" });
    if (req.url === "/workspace/capabilities") return send(200, { schemaVersion: "x", available: true, features: {}, generatedAt: "2026-10-20T00:00:00Z" });
    if (req.url === "/workspace/sandboxes") return send(200, { schemaVersion: "x", sandboxes: [], caps: {}, provider: {} });
    return send(404, { error: { code: "sandbox_not_found" }, code: "sandbox_not_found" });
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  base = `http://127.0.0.1:${server.address().port}`;
  scratch = mkdtempSync(path.join(os.tmpdir(), "sdkconf-shells-"));
  fixturesFile = path.join(scratch, "fixtures.json");
  writeFileSync(fixturesFile, JSON.stringify({ ee: { A: { orgId: "org-a", workspaceId: "ws-a", keys: { owner: "stub-key-a" } } } }));
});

after(() => {
  server.close();
  rmSync(scratch, { recursive: true, force: true });
});

const common = (out) => ["--mode", "ee-key", "--fixtures", fixturesFile, "--exporter", "http://127.0.0.1:4318", "--out", out, "--only", ONLY, "--run-id", "20261020t000000z-shells"];
const summary = (out) => JSON.parse(readFileSync(path.join(out, "summary.json"), "utf8"));

test("the ts shell loads a client by path and maps successes, typed errors and the host guard", async () => {
  seen = [];
  const out = path.join(scratch, "ts");
  const code = await main(["--lang", "ts", "--client-ts", path.join(HERE, "stub-client-ts"), "--base", base, ...common(out)]);
  const s = summary(out);
  assert.equal(code, 0, JSON.stringify(s.failed));
  assert.equal(s.package.name, "@platform-conformance/stub-client");
  assert.equal(s.counts.pass, 3);
  assert.equal(s.egressGuard.trips.length, 0);
  assert.ok(seen.every((r) => r.auth === "Bearer stub-key-a"));
  assert.ok(!readFileSync(path.join(out, "results.jsonl"), "utf8").includes("stub-key-a"), "no key in a receipt");
});

test("a client-side must-exist case: the host guard refuses before any request", async () => {
  seen = [];
  const out = path.join(scratch, "ts-guard");
  const args = ["--lang", "ts", "--client-ts", path.join(HERE, "stub-client-ts"), "--base", base, "--mode", "fi-keypair", "--exporter", "http://127.0.0.1:4318", "--out", out, "--only", "must-exist.host-guard.fi-keypair", "--run-id", "20261020t000000z-guard"];
  const code = await main(args);
  const s = summary(out);
  assert.equal(code, 0, JSON.stringify(s.failed));
  assert.equal(s.counts.pass, 1);
  assert.equal(seen.length, 0, "the refusal made no request");
});

test("the fake shell runs with the network denied and still answers from the test kit", async () => {
  seen = [];
  const out = path.join(scratch, "fake");
  const code = await main(["--lang", "fake", "--testkit", path.join(HERE, "stub-testkit"), ...common(out).map((a) => (a === ONLY ? "platform.capabilities.get,sandboxes.list.ok" : a))]);
  const s = summary(out);
  assert.equal(code, 0, JSON.stringify(s.failed));
  assert.equal(s.counts.pass, 2);
  assert.equal(s.egressGuard.denyAll, true);
  assert.equal(seen.length, 0, "the fake made no request");
});

test("a shell refuses to start without an exporter endpoint or with a production base URL", async () => {
  await assert.rejects(main(["--lang", "ts", "--client-ts", path.join(HERE, "stub-client-ts"), "--base", base, "--mode", "ee-key", "--out", scratch]), /exporter is unset/);
  await assert.rejects(main(["--lang", "ts", "--client-ts", path.join(HERE, "stub-client-ts"), "--base", "https://api.futureagi.com", "--exporter", "http://127.0.0.1:1", "--mode", "ee-key", "--out", scratch]), /production/);
});

const python = process.env.SDKCONF_PYTHON;
test("the py shell loads a Python client by path through the worker", { skip: python ? false : "set SDKCONF_PYTHON to a Python with httpx" }, async () => {
  execFileSync(python, ["-c", "import httpx"]);
  seen = [];
  const out = path.join(scratch, "py");
  const code = await main(["--lang", "py", "--client-py", path.join(HERE, "stub_client_py"), "--python", python, "--base", base, ...common(out).map((a) => (a === ONLY ? "platform.capabilities.get,sandboxes.list.ok,sandboxes.get.unknown-id" : a))]);
  const s = summary(out);
  assert.equal(code, 0, JSON.stringify(s.failed));
  assert.equal(s.package.name, "stub-client-py");
  assert.equal(s.counts.pass, 3);
  assert.equal(s.pythonEgressGuard.trips.length, 0);
  assert.ok(s.pythonEgressGuard.reached.includes("127.0.0.1"));
});

test("the py shell's worker guards the whole process: an SDK that builds its own clients trips, and the run exits 3", { skip: python ? false : "set SDKCONF_PYTHON to a Python with httpx" }, async () => {
  seen = [];
  const out = path.join(scratch, "py-bypass");
  const code = await main(["--lang", "py", "--client-py", path.join(HERE, "bypass_client_py"), "--python", python, "--base", base, ...common(out).map((a) => (a === ONLY ? "platform.capabilities.get" : a))]);
  const s = summary(out);
  assert.equal(code, 3, "a tripped guard fails the run");
  assert.deepEqual(s.pythonEgressGuard.trips.map((t) => t.host), ["bypass-probe.invalid", "bypass-probe2.invalid", "api.futureagi.com"]);
  assert.ok(s.pythonEgressGuard.trips.every((t) => t.via.startsWith("socket.")), JSON.stringify(s.pythonEgressGuard.trips));
  assert.equal(s.pythonEgressGuard.process.armed, true);
  const row = JSON.parse(readFileSync(path.join(out, "results.jsonl"), "utf8").trim().split("\n")[0]);
  assert.equal(row.attempts[0].code, "httpx=EgressBlockedError,urllib=EgressBlockedError,socket=EgressBlockedError");
  assert.equal(seen.length, 0, "nothing reached even the loopback stand-in");
});
