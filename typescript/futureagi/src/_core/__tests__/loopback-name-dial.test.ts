/**
 * A loopback host is dialed as written. A request whose host is the literal name `localhost` reaches only 127.0.0.1
 * (then ::1): the name is not handed to the system resolver, so an answer of some other address is never connected to.
 * A name that merely resolves to 127.0.0.1 (`loop.test`, through a resolver shim) is routed like any other host: https
 * goes through the environment proxy. Each sender with a direct path runs in its own process with the runtime's
 * environment proxy on (the switch is read when the runtime starts), against loopback listeners that count raw marker
 * key bytes and connections at the listener the name was written for, at the listener the shim answers, and at the
 * environment-proxy listener, which records the request line. The switch loads the runtime's undici at start-up, so
 * the SDK can prove no agent of that copy: the probe puts the `undici` package's `EnvHttpProxyAgent`, which reads the
 * same proxy variables, in the global slot with the package's `setGlobalDispatcher`. With the switch off the probe
 * loads the SDK before anything else loads the runtime's undici, and the global agent is the runtime's default one.
 */
import { execFile } from "node:child_process";
import { type AddressInfo, createServer } from "node:net";
import { join as pathJoin } from "node:path";

interface Seen {
  connected: string[]; asked: string[];
  targetBytes: number; targetConnections: number; answeredBytes: number; answeredConnections: number;
  proxyConnections: number; proxyLine: string; port: number;
}

function freePort(): Promise<number> {
  const server = createServer();
  return new Promise((resolve) => { server.listen(0, "127.0.0.1", () => { const { port } = server.address() as AddressInfo; server.close(() => { resolve(port); }); }); });
}

type Kind = "localhost-http" | "localhost-https" | "name-https" | "literal-http" | "ipv6-http";

/** `runtimeProxy: false` runs the process with no proxy variable and the runtime's default agent as its global one. */
async function runProbe(sender: string, kind: Kind, runtimeProxy = true): Promise<Seen> {
  const free = await freePort();
  const proxy = `http://127.0.0.1:${free}`;
  const env: NodeJS.ProcessEnv = {
    ...process.env, NODE_USE_ENV_PROXY: "1", HTTP_PROXY: proxy, http_proxy: proxy, HTTPS_PROXY: proxy, https_proxy: proxy,
    ALL_PROXY: proxy, all_proxy: proxy, PROBE_PROXY_PORT: String(free), PROBE_SENDER: sender, PROBE_CASE: kind,
  };
  delete env.NO_PROXY;
  delete env.no_proxy;
  if (!runtimeProxy) {
    for (const name of ["NODE_USE_ENV_PROXY", "HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy"]) delete env[name];
  }
  const tsx = require.resolve("tsx/cli");
  const probe = pathJoin(__dirname, "../__fixtures__/loopback-name-probe.ts");
  const out = await new Promise<string>((resolve, reject) => {
    execFile(process.execPath, [tsx, probe], { env, timeout: 60_000 }, (error, stdout) => { if (error !== null && stdout === "") reject(error); else resolve(stdout); });
  });
  return JSON.parse(out.trim().split("\n").pop()!) as Seen;
}

const SENDERS = ["platform Client", "APIKeyAuth (axios)"];
const ONLY_LOCAL = (port: number): string[] => [`127.0.0.1:${port}`, `::1:${port}`];

describe.each(SENDERS)("%s dials a loopback name as written", (sender) => {
  it("sends localhost to 127.0.0.1 alone, whatever the resolver answers, with an environment proxy set", async () => {
    const seen = await runProbe(sender, "localhost-http");
    expect(seen.targetBytes).toBeGreaterThan(0);
    expect(seen.answeredConnections).toBe(0);
    expect(seen.answeredBytes).toBe(0);
    expect(seen.proxyConnections).toBe(0);
    expect(seen.asked).not.toContain("localhost");
    expect(seen.connected.filter((address) => !ONLY_LOCAL(seen.port).includes(address)).filter((a) => a.endsWith(`:${seen.port}`))).toEqual([]);
  }, 90_000);

  it("sends https://localhost to 127.0.0.1 alone, with an environment proxy set", async () => {
    const seen = await runProbe(sender, "localhost-https");
    expect(seen.targetConnections).toBeGreaterThan(0);
    expect(seen.answeredConnections).toBe(0);
    expect(seen.proxyConnections).toBe(0);
    expect(seen.asked).not.toContain("localhost");
  }, 90_000);

  it("sends http://[::1] to ::1 without asking the resolver, with an environment proxy set", async () => {
    const seen = await runProbe(sender, "ipv6-http");
    expect(seen.targetBytes).toBeGreaterThan(0);
    expect(seen.asked).toEqual([]);
    expect(seen.proxyConnections).toBe(0);
  }, 90_000);

  it("sends http://127.0.0.1 straight to its listener with an environment proxy set", async () => {
    const seen = await runProbe(sender, "literal-http");
    expect(seen.targetBytes).toBeGreaterThan(0);
    expect(seen.proxyConnections).toBe(0);
    expect(seen.proxyLine).toBe("");
  }, 90_000);

  it("sends localhost to 127.0.0.1 alone when the runtime's default agent is the global one", async () => {
    const seen = await runProbe(sender, "localhost-http", false);
    expect(seen.targetBytes).toBeGreaterThan(0);
    expect(seen.answeredConnections).toBe(0);
    expect(seen.answeredBytes).toBe(0);
    expect(seen.asked).not.toContain("localhost");
  }, 90_000);

  it("sends https://localhost to 127.0.0.1 alone when the runtime's default agent is the global one", async () => {
    const seen = await runProbe(sender, "localhost-https", false);
    expect(seen.targetConnections).toBeGreaterThan(0);
    expect(seen.answeredConnections).toBe(0);
    expect(seen.asked).not.toContain("localhost");
  }, 90_000);

  it("sends https to a name that resolves to 127.0.0.1 through the environment proxy, like any other host", async () => {
    const seen = await runProbe(sender, "name-https");
    expect(seen.proxyConnections).toBeGreaterThan(0);
    expect(seen.proxyLine).toContain(`CONNECT loop.test:${seen.port}`);
    expect(seen.targetConnections).toBe(0);
    expect(seen.targetBytes).toBe(0);
  }, 90_000);
});
