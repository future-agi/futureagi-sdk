/**
 * The process-wide patches behind `guard.install()`. Each layer checks the host NAME
 * through the guard's `check` before Node does anything with it, so a refused host gets no socket and
 * no DNS query:
 *
 *   globalThis.fetch                  the guarded fetch
 *   http(s).request / get             the host Node's ClientRequest will use ({...url, ...options})
 *   net.Socket#connect                every TCP connection (http Agents, undici's fetch, tls, http2);
 *                                     an IPC path (options.path set) is local and skipped
 *   dns.lookup / resolve* (+promises, Resolver)  a name lookup made directly
 *   worker_threads.Worker             REFUSED: a worker thread runs outside these patches
 *
 * After patching (and after restoring) `syncBuiltinESMExports()` updates the ES-module bindings, so
 * `import { request } from "node:http"` sees the patched function too. A reference an SDK captured
 * BEFORE install() is outside the first layer (the runner shells install before they import the SDK);
 * the socket layer still sees its connections. Limits: a child process and native addons are outside
 * an in-process guard (README "The egress guard").
 */
import dns from "node:dns";
import http from "node:http";
import https from "node:https";
import { syncBuiltinESMExports } from "node:module";
import net from "node:net";
import workerThreads from "node:worker_threads";
import { hostOf } from "./classify.mjs";

const DNS_FUNCTIONS = ["lookup", "resolve", "resolve4", "resolve6", "resolveAny", "resolveCaa", "resolveCname", "resolveMx", "resolveNaptr", "resolveNs", "resolvePtr", "resolveSoa", "resolveSrv", "resolveTxt"];

/** Drop a :port from a host, but never from an IPv6 literal (`::1`). */
function withoutPort(host) {
  const value = String(host);
  return value.split(":").length === 2 ? value.replace(/:\d+$/, "") : value;
}

/**
 * The host an http(s).request/get call connects to, decided as Node's ClientRequest decides it: a URL
 * argument becomes options, the options object is merged over it, then `hostname || host || localhost`.
 * Returns null for a Unix socket (`socketPath`).
 */
export function requestHost(args) {
  const [first, second] = args;
  const isUrl = typeof first === "string" || first instanceof URL;
  const own = isUrl ? (second && typeof second === "object" ? second : {}) : first && typeof first === "object" ? first : {};
  const merged = { ...(isUrl ? { hostname: hostOf(first) ?? "" } : {}), ...own };
  if (merged.socketPath) return null;
  return withoutPort(merged.hostname || merged.host || "localhost");
}

/** The host a net.Socket#connect call will dial, or null for an IPC path (local). */
export function socketHost(args) {
  // net.connect() hands the socket its normalised arguments as an array: [options, callback].
  const first = Array.isArray(args[0]) ? args[0][0] : args[0];
  if (first && typeof first === "object") return first.path == null ? String(first.host || "localhost") : null;
  if (typeof first === "number" || (typeof first === "string" && /^\d+$/.test(first))) return typeof args[1] === "string" && args[1] ? args[1] : "localhost";
  return null; // a string path: an IPC socket
}

/**
 * Install every patch. `check(host, via)` throws (and records) on a refused host; `refuse(what, reason)`
 * records a trip and throws. Returns the function that restores everything.
 */
export function installProcessPatches({ check, refuse, guardedFetch }) {
  const restore = [];
  const patch = (target, name, wrapper) => {
    if (!target || typeof target[name] !== "function") return;
    const original = target[name];
    target[name] = wrapper(original);
    restore.push(() => {
      target[name] = original;
    });
  };

  patch(globalThis, "fetch", () => guardedFetch);
  for (const mod of [http, https]) {
    for (const name of ["request", "get"]) {
      patch(mod, name, (original) => function guarded(...args) {
        const host = requestHost(args);
        if (host !== null) check(host, `${mod === http ? "http" : "https"}.${name}`);
        return original.apply(this, args);
      });
    }
  }
  patch(net.Socket.prototype, "connect", (original) => function guarded(...args) {
    const host = socketHost(args);
    if (host !== null) check(host, "net.connect");
    return original.apply(this, args);
  });
  const dnsTargets = [
    [dns, false],
    [dns.promises, true],
    [dns.Resolver?.prototype, false],
    [dns.promises?.Resolver?.prototype, true],
  ];
  for (const [target, async] of dnsTargets) {
    for (const name of DNS_FUNCTIONS) {
      patch(target, name, (original) => function guarded(hostname, ...rest) {
        try {
          check(String(hostname ?? ""), `dns.${name}`);
        } catch (error) {
          if (async) return Promise.reject(error);
          throw error;
        }
        return original.call(this, hostname, ...rest);
      });
    }
  }
  patch(workerThreads, "Worker", () => function RefusedWorker() {
    refuse("(worker thread)", "a worker thread runs outside the egress guard (refused)", "worker_threads");
  });
  syncBuiltinESMExports();
  return () => {
    while (restore.length) restore.pop()();
    syncBuiltinESMExports();
  };
}
