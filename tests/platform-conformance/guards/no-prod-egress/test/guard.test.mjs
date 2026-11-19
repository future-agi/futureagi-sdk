import assert from "node:assert/strict";
import http from "node:http";
import net from "node:net";
import { test } from "node:test";
import { classifyHost, isProductionHost, NAMED_PRODUCTION_HOSTS } from "../classify.mjs";
import { createEgressGuard, EgressBlockedError, requireEndpoints } from "../index.mjs";

test("every production Future AGI host is refused, even when allowlisted", () => {
  for (const host of [...NAMED_PRODUCTION_HOSTS, "futureagi.com", "FutureAGI.com.", "docs.futureagi.com", "x.y.futureagi.com"]) {
    assert.equal(isProductionHost(host), true, host);
    assert.equal(classifyHost(host, [host]).allowed, false, host);
  }
  for (const host of ["futureagi.com.evil.example", "notfutureagi.com", "futureagi.co"]) assert.equal(isProductionHost(host), false, host);
});

test("loopback is allowed, other hosts only when listed", () => {
  for (const host of ["127.0.0.1", "127.9.9.9", "localhost", "::1", "[::1]"]) assert.equal(classifyHost(host).allowed, true, host);
  assert.equal(classifyHost("rig.internal").allowed, false);
  assert.equal(classifyHost("rig.internal", ["rig.internal"]).allowed, true);
  assert.equal(classifyHost("", []).allowed, false);
});

test("the guard trips on api.futureagi.com before any socket opens (the trip test)", async () => {
  let sockets = 0;
  const original = net.Socket.prototype.connect;
  const guard = createEgressGuard({
    innerFetch: async () => {
      sockets += 1;
      return new Response("should not be reached");
    },
  });
  for (const url of ["https://api.futureagi.com/workspace/sandboxes", "https://app.futureagi.com/", "https://gateway.futureagi.com/x"]) {
    await assert.rejects(guard.fetch(url), EgressBlockedError);
  }
  assert.equal(sockets, 0);
  assert.equal(guard.tripped, true);
  assert.equal(guard.trips.length, 3);
  assert.throws(() => guard.assertNotTripped(), EgressBlockedError);
  assert.equal(net.Socket.prototype.connect, original);
});

test("install() guards global fetch, http.request and raw sockets, and uninstall() restores them", async () => {
  const originalFetch = globalThis.fetch;
  const guard = createEgressGuard({ allow: [] }).install();
  try {
    await assert.rejects(fetch("https://api.futureagi.com/"), EgressBlockedError);
    assert.throws(() => http.request({ host: "app.futureagi.com", port: 80 }), EgressBlockedError);
    assert.throws(() => net.connect({ host: "gateway.futureagi.com", port: 443 }), EgressBlockedError);
    assert.throws(() => net.connect(443, "evil.example"), EgressBlockedError);
    assert.equal(guard.trips.length, 4);
  } finally {
    guard.uninstall();
  }
  assert.equal(globalThis.fetch, originalFetch);
});

test("an allowed loopback request goes through and is not a trip", async () => {
  const server = http.createServer((_, res) => res.end("ok"));
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const guard = createEgressGuard().install();
  try {
    const response = await fetch(`http://127.0.0.1:${server.address().port}/`);
    assert.equal(await response.text(), "ok");
    assert.equal(guard.tripped, false);
    assert.doesNotThrow(() => guard.assertNotTripped());
  } finally {
    guard.uninstall();
    server.close();
  }
});

test("the span exporter is guarded on wrap and on every export", () => {
  const guard = createEgressGuard({ allow: ["collector.rig"] });
  const exported = [];
  const wrapped = guard.wrapExporter({ export: (spans, done) => (exported.push(spans), done?.({ code: 0 })) }, "http://collector.rig:4318/v1/traces");
  wrapped.export(["s1"], () => {});
  assert.deepEqual(exported, [["s1"]]);
  assert.throws(() => guard.wrapExporter({ export() {} }, "https://api.futureagi.com/tracer"), EgressBlockedError);
});

test("a runner refuses to start when a base URL or the exporter endpoint is unset or production", () => {
  assert.throws(() => requireEndpoints({ gateway: "http://127.0.0.1:18400/omega/api", ee: undefined, exporter: "http://127.0.0.1:4318" }), /ee is unset/);
  assert.throws(() => requireEndpoints({ gateway: "https://gateway.futureagi.com", exporter: "http://127.0.0.1:1" }), /production/);
  assert.deepEqual(requireEndpoints({ ee: "http://127.0.0.1:18402", exporter: "http://127.0.0.1:4318" }), ["127.0.0.1", "127.0.0.1"]);
});
