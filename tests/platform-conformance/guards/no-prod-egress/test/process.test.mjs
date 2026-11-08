// The process-wide layer of the Node guard: the request forms Node merges, the http Agent's socket
// options (path: null), ES-module bindings, worker threads and direct DNS lookups.
import assert from "node:assert/strict";
import dns from "node:dns";
import http from "node:http";
import net from "node:net";
import { test } from "node:test";
import { Worker } from "node:worker_threads";
import { createEgressGuard, EgressBlockedError } from "../index.mjs";
import { requestHost, socketHost } from "../process-patches.mjs";

const vias = (guard) => guard.trips.map((t) => `${t.host} via ${t.via}`);

/** Run `fn` with the guard installed; every patch is restored afterwards whatever happens. */
async function guarded(fn, options = {}) {
  const guard = createEgressGuard({ allow: [], ...options }).install();
  try {
    await fn(guard);
  } finally {
    guard.uninstall();
  }
  return guard;
}

test("requestHost decides the host as Node's ClientRequest does", () => {
  assert.equal(requestHost(["http://127.0.0.1:1/", { hostname: "bypass.invalid", port: 9 }]), "bypass.invalid");
  assert.equal(requestHost(["http://127.0.0.1:1/", { host: "ignored.invalid" }]), "127.0.0.1", "the URL's hostname wins over options.host");
  assert.equal(requestHost([new URL("http://[::1]:8/")]), "::1");
  assert.equal(requestHost([{ host: "::1", port: 80 }]), "::1", "an IPv6 literal keeps its colons");
  assert.equal(requestHost([{ host: "example.invalid:8080" }]), "example.invalid");
  assert.equal(requestHost([{ socketPath: "/tmp/docker.sock" }]), null);
  assert.equal(requestHost([{}]), "localhost");
});

test("socketHost checks an Agent's options (path: null) and skips only a real IPC path", () => {
  assert.equal(socketHost([[{ host: "bypass.invalid", port: 9, path: null }, () => {}]]), "bypass.invalid");
  assert.equal(socketHost([{ host: "bypass.invalid", port: 9 }]), "bypass.invalid");
  assert.equal(socketHost([{ path: "/tmp/x.sock" }]), null);
  assert.equal(socketHost(["/tmp/x.sock"]), null);
  assert.equal(socketHost([443, "evil.invalid"]), "evil.invalid");
  assert.equal(socketHost([443]), "localhost");
});

test("http.request(url, {hostname}) is refused at the first layer", async () => {
  const guard = await guarded(() => {
    assert.throws(() => http.request("http://127.0.0.1:1/", { hostname: "bypass-probe3.invalid", port: 9 }), EgressBlockedError);
  });
  assert.deepEqual(vias(guard), ["bypass-probe3.invalid via http.request"]);
});

test("a request captured before install() goes through an Agent and is refused at the socket, before DNS", async () => {
  const captured = http.request; // an SDK that grabbed the function at import time
  const guard = await guarded(async () => {
    let error;
    try {
      const req = captured({ hostname: "bypass-agent.invalid", port: 9, agent: new http.Agent() });
      error = await new Promise((resolve) => req.once("error", resolve));
    } catch (thrown) {
      error = thrown;
    }
    assert.ok(error instanceof EgressBlockedError, `${error?.name}: ${error?.message}`);
  });
  assert.deepEqual(vias(guard), ["bypass-agent.invalid via net.connect"]);
});

test("fetch captured before install() and redirected to a foreign host is refused at the socket", async () => {
  const captured = globalThis.fetch;
  const server = http.createServer((_, res) => (res.writeHead(302, { location: "http://bypass-redirect.invalid:8999/x" }), res.end()));
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  try {
    const guard = await guarded(async () => {
      await assert.rejects(captured(`http://127.0.0.1:${server.address().port}/`));
    });
    assert.deepEqual(vias(guard), ["bypass-redirect.invalid via net.connect"]);
  } finally {
    server.close();
  }
});

test("an ES-module import of node:http sees the patched request, and the original after uninstall", async () => {
  const original = http.request;
  await guarded(async () => {
    const ns = await import("node:http");
    assert.notEqual(ns.request, original);
    assert.throws(() => ns.request({ host: "api.futureagi.com", port: 443 }), EgressBlockedError);
  });
  assert.equal((await import("node:http")).request, original);
  assert.equal(http.request, original);
});

test("a worker thread is refused (it would run outside the guard), and Worker is restored after", async () => {
  const guard = await guarded(async () => {
    const ns = await import("node:worker_threads");
    assert.throws(() => new ns.Worker("fetch('http://bypass-probe4.invalid:8999/')", { eval: true }), EgressBlockedError);
  });
  assert.deepEqual(vias(guard), ["(worker thread) via worker_threads"]);
  assert.equal((await import("node:worker_threads")).Worker, Worker);
});

test("a direct DNS lookup of a refused name is refused before the query", async () => {
  const guard = await guarded(async () => {
    assert.throws(() => dns.lookup("api.futureagi.com", () => {}), EgressBlockedError);
    await assert.rejects(dns.promises.lookup("bypass-dns.invalid"), EgressBlockedError);
    await assert.rejects(dns.promises.resolve4("gateway.futureagi.com"), EgressBlockedError);
    await assert.rejects(new dns.promises.Resolver().resolveTxt("app.futureagi.com"), EgressBlockedError);
    const { address } = await dns.promises.lookup("localhost");
    assert.ok(address, "loopback still resolves");
  });
  assert.deepEqual(vias(guard), ["api.futureagi.com via dns.lookup", "bypass-dns.invalid via dns.lookup", "gateway.futureagi.com via dns.resolve4", "app.futureagi.com via dns.resolveTxt"]);
});

test("loopback through an Agent still works with the socket check on", async () => {
  const server = http.createServer((_, res) => res.end("ok"));
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  try {
    const guard = await guarded(async () => {
      const body = await new Promise((resolve, reject) => {
        http.get({ host: "127.0.0.1", port: server.address().port, agent: new http.Agent() }, (res) => {
          let text = "";
          res.on("data", (d) => (text += d)).on("end", () => resolve(text));
        }).on("error", reject);
      });
      assert.equal(body, "ok");
      const socket = net.connect({ host: "localhost", port: server.address().port });
      await new Promise((resolve, reject) => socket.once("connect", resolve).once("error", reject));
      socket.destroy();
    });
    assert.equal(guard.tripped, false, JSON.stringify(guard.trips));
    assert.equal(guard.receipt().processWide, true);
  } finally {
    server.close();
  }
});
