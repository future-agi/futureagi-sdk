/**
 * With the `undici` package unresolvable, the global dispatcher has the shape of undici's `EnvHttpProxyAgent` and
 * holds the caller's `ProxyingAgent` subclass in its "no proxy agent" slot. The SDK sends keyed loopback requests
 * through its own direct transport and refuses keyed requests to the opted-in non-loopback HTTP name with a
 * `ConfigurationError`. The SDK constructs no `ProxyingAgent`, and the proxy sink receives no connections or markers.
 * Each case runs in a fresh child process. The control cases load the SDK before the caller installs the dispatcher.
 */
import { execFile } from "node:child_process";
import { join } from "node:path";

import { CountingSink, proxyEnvironment } from "../__fixtures__/proxy-sink";

const MARKER_KEY = "marker-callerclass-key-0000000000";
const MARKER_SECRET = "marker-callerclass-secret-0000000000";
const proxySink = new CountingSink([MARKER_KEY, MARKER_SECRET]);
const targetSink = new CountingSink([MARKER_KEY, MARKER_SECRET]);
let restoreEnv: () => void = () => undefined;
beforeAll(async () => {
  restoreEnv = proxyEnvironment();
  await Promise.all([proxySink.listen(), targetSink.listen()]);
});
afterAll(async () => { restoreEnv(); await Promise.all([proxySink.close(), targetSink.close()]); });
beforeEach(() => { proxySink.reset(); targetSink.reset(); });

type Host = "plain" | "loopback";
type Shape = "method" | "symbol";
interface Seen { outcome: string; constructed: number; undiciResolvable: boolean }

async function probe(host: Host, shape: Shape, order: "dispatcherFirst" | "sdkFirst"): Promise<Seen> {
  const tsx = require.resolve("tsx/cli");
  const env: NodeJS.ProcessEnv = {
    ...process.env, PROBE_HOST: host, PROBE_SHAPE: shape, PROBE_ORDER: order,
    PROBE_PROXY_PORT: String(proxySink.port), PROBE_TARGET_PORT: String(targetSink.port), PROBE_KEY: MARKER_KEY, PROBE_SECRET: MARKER_SECRET,
  };
  delete env.FI_ALLOW_INSECURE_HTTP;
  const stdout = await new Promise<string>((resolve, reject) => {
    execFile(process.execPath, [tsx, join(__dirname, "../__fixtures__/caller-agent-class-probe.ts")], { encoding: "utf8", timeout: 20_000, env }, (error, out, err) => (error ? reject(new Error(`${String(error)} ${err}`)) : resolve(out)));
  });
  return JSON.parse(stdout.trim().split("\n").pop() ?? "{}") as Seen;
}

/** Lets the sinks read what the child wrote before it exited. */
const settle = (): Promise<void> => new Promise((resolve) => { setTimeout(resolve, 100); });

const CASES: Array<[string, Host, Shape]> = [
  ["platform Client, opted-in plain-http name, dispatch method", "plain", "method"],
  ["platform Client, opted-in plain-http name, symbol-keyed dispatch", "plain", "symbol"],
  ["platform Client, loopback address, dispatch method", "loopback", "method"],
  ["platform Client, loopback address, symbol-keyed dispatch", "loopback", "symbol"],
];

const CONTROL_CASES = CASES.filter((_, at) => [1, 2].includes(at));
const DIRECT_DELIVERY = "sends directly to the loopback target without constructing the caller's Agent or contacting the proxy (%s)";

async function expectDirectDelivery(host: Host, shape: Shape, order: "dispatcherFirst" | "sdkFirst"): Promise<void> {
  const seen = await probe(host, shape, order);
  await settle();
  const counts = {
    proxyMarkers: proxySink.markerCount,
    proxyConnections: proxySink.connections,
    proxyTunnels: proxySink.tunnels,
    targetMarkers: targetSink.markerCount,
    constructed: seen.constructed,
    outcome: seen.outcome,
  };
  process.stdout.write(`${order} platformClient ${host} ${shape}: ${JSON.stringify(counts)}\n`);
  expect(seen.undiciResolvable).toBe(false);
  expect(counts).toEqual({
    proxyMarkers: 0,
    proxyConnections: 0,
    proxyTunnels: 0,
    targetMarkers: 2,
    constructed: 0,
    outcome: "status:ok",
  });
}

describe("a caller's Agent subclass held by an EnvHttpProxyAgent-shaped global dispatcher, with undici unresolvable", () => {
  it.each(CASES.filter(([, host]) => host === "plain"))("is not constructed by the SDK and carries no key to the proxy (%s)", async (_name, host, shape) => {
    const seen = await probe(host, shape, "dispatcherFirst");
    await settle();
    const counts = { proxyMarkers: proxySink.markerCount, proxyConnections: proxySink.connections, proxyTunnels: proxySink.tunnels, constructed: seen.constructed, outcome: seen.outcome };
    process.stdout.write(`platformClient ${host} ${shape}: ${JSON.stringify(counts)}\n`);
    expect(seen.undiciResolvable).toBe(false);
    expect(counts).toEqual({ proxyMarkers: 0, proxyConnections: 0, proxyTunnels: 0, constructed: 0, outcome: "error:ConfigurationError" });
    expect(targetSink.markerCount).toBe(0);
  }, 30_000);

  it.each(CASES.filter(([, host]) => host === "loopback"))(DIRECT_DELIVERY, (_name, host, shape) =>
    expectDirectDelivery(host, shape, "dispatcherFirst"), 30_000);
});

describe("the same dispatcher put in the slot after the SDK is loaded (control)", () => {
  it.each(CONTROL_CASES.filter(([, host]) => host === "plain"))("is refused, with no construction and no marker at the proxy (%s)", async (_name, host, shape) => {
    const seen = await probe(host, shape, "sdkFirst");
    await settle();
    const counts = { proxyMarkers: proxySink.markerCount, proxyConnections: proxySink.connections, proxyTunnels: proxySink.tunnels, constructed: seen.constructed, outcome: seen.outcome };
    process.stdout.write(`control platformClient ${host} ${shape}: ${JSON.stringify(counts)}\n`);
    expect(seen.undiciResolvable).toBe(false);
    expect(counts).toEqual({ proxyMarkers: 0, proxyConnections: 0, proxyTunnels: 0, constructed: 0, outcome: "error:ConfigurationError" });
    expect(targetSink.markerCount).toBe(0);
  }, 30_000);

  it.each(CONTROL_CASES.filter(([, host]) => host === "loopback"))(DIRECT_DELIVERY, (_name, host, shape) =>
    expectDirectDelivery(host, shape, "sdkFirst"), 30_000);
});
