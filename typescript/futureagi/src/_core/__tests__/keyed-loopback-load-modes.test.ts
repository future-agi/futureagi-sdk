/**
 * A keyed plain-http send to 127.0.0.1 or localhost, with no proxy variable and no dispatcher set by the application,
 * goes to the host whatever way the SDK was loaded: an ES module graph that imports the root (that graph imports
 * `node:http`, whose ES module exports load the runtime's undici while the graph is linked, before any SDK module is
 * evaluated), CommonJS `require`, and after the application's first `fetch` or a touch of the `Request` global.
 * The platform Client carries the planted keys to the target sinks; the proxy sink counts none.
 *
 * A `ProxyingAgent` the application puts in the global dispatcher slot before the SDK is loaded puts no marker byte on
 * the proxy sink and is not built by the SDK; with the `undici` package resolvable, the SDK sends each keyed loopback
 * request through its own direct agent built from that package's `Agent` instead of the slot's dispatcher. With the
 * package unresolvable the send is refused, or sent to the host directly.
 *
 * With the `undici` package unresolvable, the SDK loaded with `require` sends using the runtime's agent. An ES module graph that
 * imports the root either sends or refuses with a message that names what the SDK cannot prove and the remedy, and
 * does not name a proxy dispatcher the application did not set. Each case runs in a fresh child process.
 */
import { execFile } from "node:child_process";
import { join } from "node:path";

import { CountingSink, proxyEnvironment } from "../__fixtures__/proxy-sink";

const SENDERS = ["platform"] as const;
type Sender = (typeof SENDERS)[number];
const HOSTS = ["127.0.0.1", "localhost"] as const;
type Host = (typeof HOSTS)[number];

const KEYS = Object.fromEntries(SENDERS.map((name) => [name, [`marker-keyedload-${name}-key-0000000000`, `marker-keyedload-${name}-secret-0000000000`]])) as Record<Sender, [string, string]>;
const proxySink = new CountingSink(Object.values(KEYS).flat());
const targetSinks = Object.fromEntries(SENDERS.map((name) => [name, Object.fromEntries(HOSTS.map((host) => [host, new CountingSink(KEYS[name])]))])) as Record<Sender, Record<Host, CountingSink>>;
const allTargets = (): CountingSink[] => SENDERS.flatMap((name) => HOSTS.map((host) => targetSinks[name][host]));

let restoreEnv: () => void = () => undefined;
beforeAll(async () => {
  restoreEnv = proxyEnvironment();
  await Promise.all([proxySink.listen(), ...allTargets().map((sink) => sink.listen())]);
});
afterAll(async () => { restoreEnv(); await Promise.all([proxySink.close(), ...allTargets().map((sink) => sink.close())]); });
beforeEach(() => { proxySink.reset(); for (const sink of allTargets()) sink.reset(); });

interface Row { outcome: string; message?: string }
interface Result { before: string; forms: { root: string }; constructed: number; outcomes: Record<string, Row> }
interface Options { undici?: "resolvable" | "unresolvable"; slot?: "empty" | "forged" }

const PACKAGE_ROOT = join(__dirname, "..", "..", "..");

async function probe(mode: string, options: Options = {}): Promise<Result> {
  const tsx = require.resolve("tsx/cli");
  const env: NodeJS.ProcessEnv = {
    ...process.env, PROBE_MODE: mode, PROBE_UNDICI: options.undici ?? "resolvable", PROBE_SLOT: options.slot ?? "empty",
    PROBE_PROXY_PORT: String(proxySink.port), PROBE_KEYS: JSON.stringify(KEYS),
    PROBE_TARGETS: JSON.stringify(Object.fromEntries(SENDERS.map((name) => [name, Object.fromEntries(HOSTS.map((host) => [host, targetSinks[name][host].port]))]))),
  };
  delete env.FI_ALLOW_INSECURE_HTTP;
  const stdout = await new Promise<string>((resolve, reject) => {
    execFile(process.execPath, [tsx, join(__dirname, "../__fixtures__/keyed-loopback-load-probe.mjs")], { cwd: PACKAGE_ROOT, encoding: "utf8", timeout: 60_000, env }, (error, out, err) => (error ? reject(new Error(`${String(error)} ${err}`)) : resolve(out)));
  });
  await new Promise((resolve) => { setTimeout(resolve, 100); });
  return JSON.parse(stdout.trim().split("\n").pop() ?? "{}") as Result;
}

interface Counts { proxyMarkers: number; proxyConnections: number; target: Record<string, number> }

/** What the sinks saw, printed so the per-row counts are in the run log. */
function seen(label: string, result: Result, senders: readonly Sender[]): Counts {
  const target = Object.fromEntries(senders.flatMap((name) => HOSTS.map((host) => [`${name}@${host}`, targetSinks[name][host].markerCount])));
  const counts = { proxyMarkers: proxySink.markerCount, proxyConnections: proxySink.connections, target };
  const rows = Object.entries(result.outcomes).map(([row, { outcome }]) => `${row}=${outcome} target markers ${target[row] ?? "-"}`).join("; ");
  process.stdout.write(`${label}: forms ${JSON.stringify(result.forms)} proxy sink markers ${counts.proxyMarkers} connections ${counts.proxyConnections} constructed ${result.constructed}; ${rows}\n`);
  return counts;
}

const REFUSAL_CODES = new Set(["insecure_http_origin", "caller_proxy"]);
const refused = (row: Row): boolean => REFUSAL_CODES.has(row.outcome.split(":")[2] ?? "");

/** Every send of every sender reached its target sink, carried its keys there, and the proxy sink counted nothing. */
function expectSent(result: Result, counts: Counts, senders: readonly Sender[]): void {
  expect(Object.keys(result.outcomes).sort()).toEqual(senders.flatMap((name) => HOSTS.map((host) => `${name}@${host}`)).sort());
  for (const [row, answer] of Object.entries(result.outcomes)) {
    expect({ row, refused: refused(answer), reached: (counts.target[row] ?? 0) > 0 }).toEqual({ row, refused: false, reached: true });
  }
  expect(counts.proxyMarkers).toBe(0);
  expect(counts.proxyConnections).toBe(0);
}

type Forms = Result["forms"];
const esm: Forms = { root: "esm" };
const cjs: Forms = { root: "cjs" };

const LOAD_MODES: Array<[string, string, Forms]> = [
  ["an ES module graph that imports the root", "esm:root", esm],
  ["require of the root", "cjs:root", cjs],
  ["the application's first fetch, then require of the root", "fetch,cjs:root", cjs],
  ["the Request global touched, then require of the root", "request,cjs:root", cjs],
  ["the Request global touched, then an ES module graph that imports the root", "request,esm:root", esm],
];

describe("keyed plain-http sends to a loopback host, by the way the SDK is loaded", () => {
  it.each(LOAD_MODES)("%s: every sender reaches the target sink and the proxy sink counts no marker", async (label, mode, forms) => {
    const result = await probe(mode);
    const counts = seen(label, result, SENDERS);
    expect(result.before).toBe("empty");
    expect(result.forms).toEqual(forms);
    expectSent(result, counts, SENDERS);
  }, 90_000);
});

const FORGED_MODES: Array<[string, string, Forms]> = [
  ["an ES module graph that imports the root", "esm:root", esm],
  ["require of the root", "cjs:root", cjs],
];

describe("a ProxyingAgent the application puts in the global dispatcher slot before the SDK is loaded", () => {
  it.each(FORGED_MODES)("%s: the proxy sink counts no marker, the SDK does not build the application's class, and each send reaches the host through the SDK's own direct agent", async (label, mode, forms) => {
    const result = await probe(mode, { slot: "forged" });
    const counts = seen(`forged slot, ${label}`, result, SENDERS);
    expect(result.forms).toEqual(forms);
    expect(counts.proxyMarkers).toBe(0);
    expect(counts.proxyConnections).toBe(0);
    expect(result.constructed).toBe(0);
    expectSent(result, counts, SENDERS);
  }, 90_000);
});

describe("with the undici package unresolvable", () => {
  it("require of the root: every sender reaches the target sink and the proxy sink counts no marker", async () => {
    const result = await probe("cjs:root", { undici: "unresolvable" });
    const counts = seen("undici unresolvable, require of the root", result, SENDERS);
    expect(result.forms).toEqual(cjs);
    expectSent(result, counts, SENDERS);
  }, 90_000);

  it("an ES module graph that imports the root: each send reaches the host or is refused naming the remedy, not a proxy dispatcher", async () => {
    const result = await probe("esm:root", { undici: "unresolvable" });
    const counts = seen("undici unresolvable, an ES module graph that imports the root", result, SENDERS);
    expect(result.forms).toEqual(esm);
    expect(Object.keys(result.outcomes)).toHaveLength(SENDERS.length * HOSTS.length);
    for (const [row, answer] of Object.entries(result.outcomes)) {
      const reached = (counts.target[row] ?? 0) > 0;
      if (refused(answer)) {
        expect({ row, reached }).toEqual({ row, reached: false });
        expect(answer.message ?? "").not.toContain("proxy dispatcher (undici ProxyAgent)");
        expect(answer.message ?? "").toMatch(/undici/u);
        expect(answer.message ?? "").toMatch(/install/iu);
      } else {
        expect({ row, outcome: answer.outcome, reached }).toEqual({ row, outcome: answer.outcome, reached: true });
      }
    }
    expect(counts.proxyMarkers).toBe(0);
    expect(counts.proxyConnections).toBe(0);
  }, 90_000);

  it.each(FORGED_MODES)("a ProxyingAgent in the global slot, %s: the proxy sink counts no marker and the SDK does not build the class", async (label, mode, forms) => {
    const result = await probe(mode, { undici: "unresolvable", slot: "forged" });
    const counts = seen(`undici unresolvable, forged slot, ${label}`, result, SENDERS);
    expect(result.forms).toEqual(forms);
    expect(Object.keys(result.outcomes)).toHaveLength(SENDERS.length * HOSTS.length);
    expect(counts.proxyMarkers).toBe(0);
    expect(counts.proxyConnections).toBe(0);
    expect(result.constructed).toBe(0);
  }, 90_000);
});
