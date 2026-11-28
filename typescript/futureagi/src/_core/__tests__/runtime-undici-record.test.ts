/**
 * The runtime-undici record (`Symbol.for("@future-agi/sdk.runtime-undici")`) and the global dispatcher slot, as the
 * application can set them before the SDK is loaded, and dispatchers whose routing slots the application turns into
 * getters or points at a Unix socket. The platform Client sends keyed plain HTTP requests to 127.0.0.1 and localhost;
 * the sinks count the planted keys.
 *
 * A record whose `Agent` is the application's `ProxyingAgent` (a subclass of the `undici` package's `Agent`, named
 * `ProxyingAgent` or `Agent`) with that agent in the slot puts no marker byte on the proxy sink, and the SDK builds no
 * `ProxyingAgent`: with the `undici` package resolvable the SDK reads no record and sends through its own direct agent;
 * with it unresolvable a record whose classes are not in the form the runtime's own undici classes have proves nothing,
 * and each send is refused or reaches the host. A `MockAgent` whose inner agent slot is a getter, and an `Agent` whose own
 * `dispatch` or `factory` slot (or a `factory` slot on a prototype of its own) is one, is not proven direct (no marker
 * byte on the proxy sink), and an `Agent` built with a socket path puts no marker byte on the Unix socket sink. Each case
 * runs in a fresh child process.
 */
import { execFile } from "node:child_process";
import { rmSync } from "node:fs";
import net from "node:net";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { CountingSink, proxyEnvironment } from "../__fixtures__/proxy-sink";

const SENDERS = ["platform"] as const;
type Sender = (typeof SENDERS)[number];
const HOSTS = ["127.0.0.1", "localhost"] as const;
type Host = (typeof HOSTS)[number];

const KEYS = Object.fromEntries(SENDERS.map((name) => [name, [`marker-undicirecord-${name}-key-0000000000`, `marker-undicirecord-${name}-secret-0000000000`]])) as Record<Sender, [string, string]>;
const MARKERS = Object.values(KEYS).flat();
const proxySink = new CountingSink(MARKERS);
const targetSinks = Object.fromEntries(SENDERS.map((name) => [name, Object.fromEntries(HOSTS.map((host) => [host, new CountingSink(KEYS[name])]))])) as Record<Sender, Record<Host, CountingSink>>;
const allTargets = (): CountingSink[] => SENDERS.flatMap((name) => HOSTS.map((host) => targetSinks[name][host]));

/** A Unix socket listener that counts the planted markers it receives and answers each request with `{}`. */
const SOCKET = join(tmpdir(), `runtime-undici-record-${process.pid}.sock`);
let socketBytes: Buffer[] = [];
const socketSink = net.createServer((connection) => {
  connection.on("error", () => undefined);
  connection.on("data", (chunk) => {
    socketBytes.push(chunk);
    connection.end("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}");
  });
});
const socketMarkers = (): number => { const blob = Buffer.concat(socketBytes).toString("latin1"); return MARKERS.reduce((n, marker) => n + blob.split(marker).length - 1, 0); };

let restoreEnv: () => void = () => undefined;
beforeAll(async () => {
  restoreEnv = proxyEnvironment();
  rmSync(SOCKET, { force: true });
  await Promise.all([proxySink.listen(), ...allTargets().map((sink) => sink.listen()), new Promise<void>((resolve) => socketSink.listen(SOCKET, resolve))]);
});
afterAll(async () => {
  restoreEnv();
  await Promise.all([proxySink.close(), ...allTargets().map((sink) => sink.close()), new Promise((resolve) => socketSink.close(resolve))]);
  rmSync(SOCKET, { force: true });
});
beforeEach(() => { proxySink.reset(); socketBytes = []; for (const sink of allTargets()) sink.reset(); });

interface Row { outcome: string; message?: string }
interface Result { forms: { root: string }; constructed: number; outcomes: Record<string, Row> }

const PACKAGE_ROOT = join(__dirname, "..", "..", "..");

async function probe(mode: string, probeCase: string, undici: "resolvable" | "unresolvable"): Promise<Result> {
  const tsx = require.resolve("tsx/cli");
  const env: NodeJS.ProcessEnv = {
    ...process.env, PROBE_MODE: mode, PROBE_CASE: probeCase, PROBE_UNDICI: undici, PROBE_SOCKET: SOCKET,
    PROBE_PROXY_PORT: String(proxySink.port), PROBE_KEYS: JSON.stringify(KEYS),
    PROBE_TARGETS: JSON.stringify(Object.fromEntries(SENDERS.map((name) => [name, Object.fromEntries(HOSTS.map((host) => [host, targetSinks[name][host].port]))]))),
  };
  delete env.FI_ALLOW_INSECURE_HTTP;
  const stdout = await new Promise<string>((resolve, reject) => {
    execFile(process.execPath, [tsx, join(__dirname, "../__fixtures__/runtime-undici-record-probe.mjs")], { cwd: PACKAGE_ROOT, encoding: "utf8", timeout: 60_000, env }, (error, out, err) => (error ? reject(new Error(`${String(error)} ${err}`)) : resolve(out)));
  });
  await new Promise((resolve) => { setTimeout(resolve, 100); });
  return JSON.parse(stdout.trim().split("\n").pop() ?? "{}") as Result;
}

interface Counts { proxyMarkers: number; socketMarkers: number; target: Record<string, number> }

/** What the sinks saw, printed so the per-row counts are in the run log. */
function seen(label: string, result: Result): Counts {
  const target = Object.fromEntries(SENDERS.flatMap((name) => HOSTS.map((host) => [`${name}@${host}`, targetSinks[name][host].markerCount])));
  const counts = { proxyMarkers: proxySink.markerCount, socketMarkers: socketMarkers(), target };
  const rows = Object.entries(result.outcomes).map(([row, { outcome }]) => `${row}=${outcome} target markers ${target[row] ?? "-"}`).join("; ");
  process.stdout.write(`${label}: forms ${JSON.stringify(result.forms)} proxy sink markers ${counts.proxyMarkers} socket sink markers ${counts.socketMarkers} constructed ${result.constructed}; ${rows}\n`);
  return counts;
}

const REFUSAL_CODES = new Set(["insecure_http_origin", "caller_proxy"]);
const refused = (row: Row): boolean => REFUSAL_CODES.has(row.outcome.split(":")[2] ?? "");
const rows = SENDERS.flatMap((name) => HOSTS.map((host) => `${name}@${host}`)).sort();

/** No marker on the proxy or socket sink; each send reached its target (or, with `refusable`, was refused and did not). */
function expectNoDetour(result: Result, counts: Counts, refusable: boolean): void {
  expect(Object.keys(result.outcomes).sort()).toEqual(rows);
  for (const [row, answer] of Object.entries(result.outcomes)) {
    const reached = (counts.target[row] ?? 0) > 0;
    if (refusable && refused(answer)) expect({ row, reached }).toEqual({ row, reached: false });
    else expect({ row, outcome: answer.outcome, reached }).toEqual({ row, outcome: "sent", reached: true });
  }
  expect(counts.proxyMarkers).toBe(0);
  expect(counts.socketMarkers).toBe(0);
}

const RECORD_MODES: Array<[string, string]> = [
  ["require of the root", "cjs:root"],
  ["an ES module graph that imports the root", "esm:root"],
];

describe("a record naming the application's ProxyingAgent, with that agent in the global slot", () => {
  it.each(RECORD_MODES.flatMap(([label, mode]) => (["resolvable", "unresolvable"] as const).map((undici) => [label, undici, mode] as const)))(
    "%s, undici %s: no marker on the proxy sink and no ProxyingAgent built", async (label, undici, mode) => {
      const result = await probe(mode, "record", undici);
      const counts = seen(`record, ${label}, undici ${undici}`, result);
      expect(result.constructed).toBe(0);
      expectNoDetour(result, counts, undici === "unresolvable");
    }, 90_000);

  it.each(["resolvable", "unresolvable"] as const)("its subclass named Agent, require of the root, undici %s: no marker on the proxy sink and no ProxyingAgent built", async (undici) => {
    const result = await probe("cjs:root", "record-named", undici);
    const counts = seen(`record of a subclass named Agent, undici ${undici}`, result);
    expect(result.constructed).toBe(0);
    expectNoDetour(result, counts, undici === "unresolvable");
  }, 90_000);
});

describe("a dispatcher whose routing slot is a getter", () => {
  it.each([
    ["a MockAgent whose inner agent slot", "mock-accessor"], ["an Agent whose own dispatch", "dispatch-accessor"],
    ["an Agent whose own factory slot", "factory-accessor"], ["an Agent whose factory slot on a prototype of its own", "proto-factory-accessor"],
  ])(
    "%s is a getter: no marker on the proxy sink, each send reaches the host", async (label, probeCase) => {
      const result = await probe("cjs:root", probeCase, "resolvable");
      const counts = seen(`${label} is a getter`, result);
      expectNoDetour(result, counts, false);
    }, 90_000);
});

describe("an undici dispatcher built with a Unix socket path", () => {
  it.each([["an Agent with socketPath", "socket-path"], ["an Agent with connect.socketPath", "connect-socket-path"], ["an Agent with connect.path", "connect-path"]])(
    "%s: no marker on the socket sink, each send reaches the host", async (label, probeCase) => {
      const result = await probe("cjs:root", probeCase, "resolvable");
      const counts = seen(label, result);
      expectNoDetour(result, counts, false);
    }, 90_000);
});
