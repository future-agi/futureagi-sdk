// Loopback listeners for keyed requests sent through a proxy.
//
// - certificates(): a scratch CA and a server certificate for SHIM_HOST, localhost and 127.0.0.1, made with the
//   openssl command line in a new temporary directory, and trusted by this process (tls.setDefaultCACertificates).
// - tlsTarget(): an https listener that records the bytes it receives after TLS, so a test reads what reached the
//   target in the clear.
// - proxySink(): a proxy that records every request it receives, as CONNECT or in absolute form, with the raw bytes.
//   A CONNECT to SHIM_HOST or a loopback address is tunnelled to 127.0.0.1 at the requested port; any other CONNECT is
//   answered 502. A request in absolute form is answered by the proxy itself (200 with a JSON body), unless `forward`
//   is set, in which case it is passed to 127.0.0.1 at the port of the URL.
"use strict";
const fs = require("node:fs");
const net = require("node:net");
const os = require("node:os");
const path = require("node:path");
const tls = require("node:tls");
const { spawnSync } = require("node:child_process");

const SHIM_HOST = "guard-target.futureagi.com";
const REPLY_BODY = JSON.stringify({ status: true, result: {} });

let made;

/** A scratch CA and server certificate, trusted by this process. */
function certificates() {
  if (made) return made;
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "fi-proxy-tls-"));
  const run = (args) => {
    const out = spawnSync("openssl", args, { cwd: dir, encoding: "utf8" });
    if (out.status !== 0) throw new Error(`openssl ${args[0]} failed: ${out.stderr}`);
  };
  fs.writeFileSync(path.join(dir, "ext.cnf"), `subjectAltName=DNS:${SHIM_HOST},DNS:localhost,IP:127.0.0.1\nbasicConstraints=CA:FALSE\n`);
  run(["req", "-x509", "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:prime256v1", "-nodes", "-keyout", "ca.key", "-out", "ca.pem", "-days", "2", "-subj", "/CN=fi-test-ca"]);
  run(["req", "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:prime256v1", "-nodes", "-keyout", "server.key", "-out", "server.csr", "-subj", `/CN=${SHIM_HOST}`]);
  run(["x509", "-req", "-in", "server.csr", "-CA", "ca.pem", "-CAkey", "ca.key", "-CAcreateserial", "-out", "server.pem", "-days", "2", "-extfile", "ext.cnf"]);
  made = {
    ca: fs.readFileSync(path.join(dir, "ca.pem"), "utf8"),
    key: fs.readFileSync(path.join(dir, "server.key"), "utf8"),
    cert: fs.readFileSync(path.join(dir, "server.pem"), "utf8"),
  };
  fs.rmSync(dir, { recursive: true, force: true });
  if (typeof tls.setDefaultCACertificates !== "function") {
    throw new Error("tls.setDefaultCACertificates is missing: Node 22.19+ or 24.5+ is needed for these tests");
  }
  tls.setDefaultCACertificates([...tls.getCACertificates("default"), made.ca]);
  return made;
}

function counter(chunks) {
  return (markers) => {
    const all = chunks.join("");
    let bytes = 0;
    for (const marker of markers) {
      for (let at = all.indexOf(marker); at >= 0; at = all.indexOf(marker, at + marker.length)) bytes += marker.length;
    }
    return bytes;
  };
}

function closer(server, sockets) {
  return () =>
    new Promise((resolve) => {
      for (const socket of sockets) socket.destroy();
      server.close(() => resolve());
    });
}

/**
 * An https listener on 127.0.0.1. `respond(head, index)` may return the whole response text for a request (for
 * example a redirect); by default it answers 200 with a JSON body. Each request is answered on its own connection
 * (Connection: close).
 */
async function tlsTarget(respond) {
  const { key, cert } = certificates();
  const chunks = [];
  const requests = [];
  const sockets = new Set();
  const state = { connections: 0 };
  const server = tls.createServer({ key, cert }, (socket) => {
    state.connections++;
    sockets.add(socket);
    socket.on("close", () => sockets.delete(socket));
    socket.on("error", () => undefined);
    let head = "";
    let answered = false;
    socket.on("data", (data) => {
      const text = data.toString("latin1");
      chunks.push(text);
      if (answered) return;
      head += text;
      if (!head.includes("\r\n\r\n")) return;
      answered = true;
      requests.push(head);
      const custom = respond ? respond(head, requests.length - 1) : undefined;
      socket.end(custom || `HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: ${REPLY_BODY.length}\r\nConnection: close\r\n\r\n${REPLY_BODY}`);
    });
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  return {
    port: server.address().port,
    get connections() {
      return state.connections;
    },
    requests,
    raw: () => chunks.join(""),
    count: counter(chunks),
    close: closer(server, sockets),
  };
}

/**
 * A proxy on 127.0.0.1 that records each request it receives. `connects` holds the head of every CONNECT request,
 * `absolute` the head of every request in absolute form. `raw()` is every byte received from clients, tunnelled bytes
 * included. Options: `connectStatus` answers every CONNECT with that status instead of tunnelling; `forward` passes
 * absolute-form requests on to 127.0.0.1.
 */
async function proxySink(options = {}) {
  const chunks = [];
  const connects = [];
  const absolute = [];
  const sockets = new Set();
  const state = { connections: 0 };
  const server = net.createServer((socket) => {
    state.connections++;
    sockets.add(socket);
    socket.on("close", () => sockets.delete(socket));
    socket.on("error", () => undefined);
    let head = Buffer.alloc(0);
    let decided = false;
    socket.on("data", (data) => {
      chunks.push(data.toString("latin1"));
      if (decided) return;
      head = Buffer.concat([head, data]);
      const end = head.indexOf("\r\n\r\n");
      if (end < 0) return;
      decided = true;
      const text = head.subarray(0, end + 4).toString("latin1");
      const rest = head.subarray(end + 4);
      const [method, authority] = text.split("\r\n")[0].split(" ");
      if (method === "CONNECT") {
        connects.push(text);
        if (options.connectStatus) {
          socket.end(`HTTP/1.1 ${options.connectStatus} Refused\r\nContent-Length: 0\r\nConnection: close\r\n\r\n`);
          return;
        }
        const at = authority.lastIndexOf(":");
        const host = authority.slice(0, at).replace(/^\[|\]$/g, "").toLowerCase();
        const port = Number(authority.slice(at + 1));
        if (!(host === SHIM_HOST || host === "localhost" || /^127\./.test(host) || host === "::1")) {
          socket.end("HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\nConnection: close\r\n\r\n");
          return;
        }
        const upstream = net.connect(port, "127.0.0.1", () => {
          socket.write("HTTP/1.1 200 Connection Established\r\n\r\n");
          if (rest.length) upstream.write(rest);
          socket.on("data", (more) => upstream.write(more));
          upstream.on("data", (back) => socket.write(back));
          upstream.on("end", () => socket.end());
          socket.on("end", () => upstream.end());
        });
        upstream.on("error", () => socket.destroy());
        sockets.add(upstream);
        upstream.on("close", () => sockets.delete(upstream));
        return;
      }
      absolute.push(text);
      if (options.forward) {
        let port = 80;
        try {
          port = Number(new URL(authority).port) || 80;
        } catch {
          /* answered below */
        }
        const upstream = net.connect(port, "127.0.0.1", () => {
          upstream.write(head);
          socket.on("data", (more) => upstream.write(more));
          upstream.pipe(socket);
        });
        upstream.on("error", () => socket.destroy());
        sockets.add(upstream);
        upstream.on("close", () => sockets.delete(upstream));
        return;
      }
      socket.end(`HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: ${REPLY_BODY.length}\r\nConnection: close\r\n\r\n${REPLY_BODY}`);
    });
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  return {
    port: server.address().port,
    get connections() {
      return state.connections;
    },
    connects,
    absolute,
    raw: () => chunks.join(""),
    count: counter(chunks),
    close: closer(server, sockets),
  };
}

/** Resolve SHIM_HOST to 127.0.0.1 in this process (every other name as before); returns the function that undoes it. */
function shimLookup() {
  const dns = require("node:dns");
  const real = dns.lookup;
  dns.lookup = function lookup(hostname, options, callback) {
    if (typeof options === "function") {
      callback = options;
      options = {};
    }
    if (String(hostname).toLowerCase() === SHIM_HOST) {
      const all = typeof options === "object" && options !== null && options.all === true;
      process.nextTick(() => (all ? callback(null, [{ address: "127.0.0.1", family: 4 }]) : callback(null, "127.0.0.1", 4)));
      return {};
    }
    return real.call(dns, hostname, options, callback);
  };
  return () => {
    dns.lookup = real;
  };
}

module.exports = { SHIM_HOST, REPLY_BODY, certificates, tlsTarget, proxySink, shimLookup };
