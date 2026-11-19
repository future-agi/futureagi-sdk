/**
 * The egress guard for every conformance runner: `tests/platform-conformance/guards/no-prod-egress`.
 *
 *   const guard = createEgressGuard({ allow: ["rig-host"] });
 *   guard.install();            // process-wide: fetch, http(s), net.Socket#connect, dns, worker_threads
 *   guard.fetch(url, init);     // the wrapped transport an SDK under test is given
 *   guard.wrapExporter(exp, endpoint)  // a span exporter that refuses a non-allowed endpoint
 *
 * The first request to a host that is not allowed (classify.mjs) TRIPS the guard: the request is
 * refused before any socket or DNS lookup, the trip is recorded, and `assertNotTripped()` fails the
 * run. What install() patches, and its limits, are in process-patches.mjs; install it BEFORE the SDK
 * under test is imported. A runner must call `requireEndpoints()` first: it refuses to start when any
 * base URL or the exporter endpoint is unset, or names a host the guard would refuse.
 */
import { classifyHost, hostOf } from "./classify.mjs";
import { installProcessPatches } from "./process-patches.mjs";

export class EgressBlockedError extends Error {
  constructor(host, reason) {
    super(`egress guard: refused ${host || "(no host)"} (${reason})`);
    this.name = "EgressBlockedError";
    this.host = host;
    this.reason = reason;
  }
}

function fetchHost(input) {
  if (typeof input === "string" || input instanceof URL) return hostOf(input);
  if (input && typeof input === "object" && "url" in input) return hostOf(input.url);
  return null;
}

export function createEgressGuard({ allow = [], denyAll = false, innerFetch = globalThis.fetch } = {}) {
  const trips = [];
  const allowed = [];
  let restore = null;
  let processWide = false;

  function check(host, via) {
    // denyAll: the fake runner's network is denied outright, loopback included.
    const verdict = denyAll ? { allowed: false, reason: "network denied (fake runner)" } : classifyHost(host, allow);
    if (!verdict.allowed) {
      trips.push({ host, reason: verdict.reason, via, at: new Date().toISOString() });
      throw new EgressBlockedError(host, verdict.reason);
    }
    if (!allowed.includes(host)) allowed.push(host);
  }

  /** Refuse something the guard cannot see into (a worker thread): always a trip. */
  function refuse(what, reason, via) {
    trips.push({ host: what, reason, via, at: new Date().toISOString() });
    throw new EgressBlockedError(what, reason);
  }

  const guardedFetch = (input, init) => {
    try {
      check(fetchHost(input), "fetch");
    } catch (error) {
      return Promise.reject(error);
    }
    return innerFetch(input, init);
  };

  return {
    fetch: guardedFetch,
    check: (url) => check(hostOf(url), "check"),
    checkHost: (host) => check(host, "check"),
    trips,
    allowedHosts: allowed,
    get tripped() {
      return trips.length > 0;
    },
    install() {
      restore ??= installProcessPatches({ check, refuse, guardedFetch });
      processWide = true;
      return this;
    },
    uninstall() {
      restore?.();
      restore = null;
    },
    /** A span exporter whose endpoint is checked before every export. */
    wrapExporter(exporter, endpoint) {
      check(hostOf(endpoint), "exporter");
      return {
        export(spans, done) {
          try {
            check(hostOf(endpoint), "exporter");
          } catch (error) {
            done?.({ code: 1, error });
            return;
          }
          exporter.export(spans, done);
        },
        shutdown: () => exporter.shutdown?.(),
      };
    },
    assertNotTripped() {
      if (trips.length) throw new EgressBlockedError(trips[0].host, `${trips.length} refused request(s); first: ${trips[0].reason}`);
    },
    receipt() {
      return { armed: true, processWide, denyAll, allowlist: [...allow], reached: [...allowed], trips: trips.map((t) => ({ ...t })) };
    },
  };
}

/**
 * Refuse to start unless every named endpoint is set and allowed. `endpoints` is
 * { name: url | undefined }; returns the list of hosts to allow.
 */
export function requireEndpoints(endpoints, allow = []) {
  const problems = [];
  for (const [name, url] of Object.entries(endpoints)) {
    if (!url) {
      problems.push(`${name} is unset`);
      continue;
    }
    const host = hostOf(url);
    if (!host) {
      problems.push(`${name} is not a URL`);
      continue;
    }
    const verdict = classifyHost(host, allow);
    if (!verdict.allowed) problems.push(`${name} names ${host} (${verdict.reason})`);
  }
  if (problems.length) throw new Error(`refusing to start: ${problems.join("; ")}`);
  return Object.values(endpoints).map(hostOf);
}
