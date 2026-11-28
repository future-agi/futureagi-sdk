/**
 * An adapter FUNCTION that sends through `fetch` reads none of the `proxy`, agent or `maxRedirects` settings a keyed
 * request gets: axios's own 'fetch' adapter taken from another copy of axios (its identity is not the SDK's), and an
 * adapter function of a third party that calls the global `fetch`. The SDK cannot route a request through such an
 * adapter, so a request that carries a key is refused before any connection with the code 'keyed_adapter_unsupported',
 * however the adapter was set: as axios's global default when the client is built, as the client's instance default,
 * by an interceptor, or on the request itself. A caller who owns the adapter opts in with
 * `customAdapterReceivesKeys: true`, and the request then goes through that adapter.
 *
 * Loopback listeners count connections and marker key bytes: the origin answers 302 or 307 with a Location on another
 * host (a name the resolver shim answers with 127.0.0.1), and that host answers 200. With the runtime's environment
 * proxy on, a CONNECT-aware proxy sink in a child process counts what reaches the proxy.
 */
import { execFile } from "node:child_process";
import { join } from "node:path";

import axios, { type AxiosAdapter, type AxiosInstance } from "axios";

import { APIKeyAuth, HttpClient, type APIKeyAuthConfig } from "../auth";
import { HttpMethod } from "../types";
import { ConfigurationError } from "../../_core/errors";
import { MARKER_KEY, MARKER_SECRET, Sink } from "../../_core/__fixtures__/plaintext-sinks";
import { installNameShim, type NameShim } from "../../_core/__fixtures__/name-shim";
import { globalFetchAdapter } from "../__fixtures__/global-fetch-adapter";
import { TunnelSink } from "../__fixtures__/tunnel-sink";

const VARS = ["HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy", "FI_ALLOW_INSECURE_HTTP", "FI_EXTRA_HEADERS"];
const saved = new Map(VARS.map((name) => [name, process.env[name]] as const));

const next = new Sink();
const plain = new Sink();
const origins: Record<string, Sink> = {};
let shim: NameShim | undefined;

beforeAll(async () => {
  for (const name of VARS) delete process.env[name];
  await next.listen();
  origins["302"] = new Sink("302 Found", `http://redirect.localhost:${next.port}/next`);
  origins["307"] = new Sink("307 Temporary Redirect", `http://redirect.localhost:${next.port}/next`);
  await Promise.all([origins["302"].listen(), origins["307"].listen(), plain.listen()]);
});
afterAll(() => {
  next.close(); plain.close(); origins["302"]?.close(); origins["307"]?.close();
  for (const [name, value] of saved) { if (value === undefined) delete process.env[name]; else process.env[name] = value; }
});
beforeEach(() => {
  next.reset(); plain.reset(); origins["302"].reset(); origins["307"].reset();
  shim = installNameShim({ "redirect.localhost": "127.0.0.1" });
});
afterEach(() => { shim?.restore(); shim = undefined; });

/** axios's 'fetch' adapter from a second copy of axios: the adapter an application with its own axios would hand over. */
const otherCopyFetch = (): AxiosAdapter => {
  let other: typeof axios | undefined;
  jest.isolateModules(() => { other = (require("axios") as { default: typeof axios }).default; });
  const adapter = (other as typeof axios).getAdapter("fetch");
  if (adapter === axios.getAdapter("fetch")) throw new Error("the second copy of axios shares the SDK's fetch adapter");
  return adapter;
};

const ADAPTERS: Array<[string, () => AxiosAdapter]> = [
  ["axios's 'fetch' adapter from another copy of axios", otherCopyFetch],
  ["a third-party adapter function that calls the global fetch", () => globalFetchAdapter().adapter],
];

class Probe extends APIKeyAuth {
  get instance(): AxiosInstance { return this._axiosInstance; }
}
const keyed = (base: string, extra: Record<string, unknown> = {}): Probe =>
  new Probe({ fiApiKey: MARKER_KEY, fiSecretKey: MARKER_SECRET, fiBaseUrl: base, retryAttempts: 1, ...extra } as APIKeyAuthConfig);
const outcome = async (call: () => Promise<unknown>): Promise<unknown> => {
  try { return await call(); } catch (error) { return error; }
};

type Route = (base: string, adapter: AxiosAdapter) => () => Promise<unknown>;
const ROUTES: Array<[string, Route]> = [
  ["axios's global default when the client is built", (base, adapter) => {
    const before = axios.defaults.adapter;
    axios.defaults.adapter = adapter;
    let client: Probe;
    try { client = keyed(base); } finally { axios.defaults.adapter = before; }
    return () => client.request({ method: HttpMethod.GET, url: "/start" });
  }],
  ["the client's instance default", (base, adapter) => {
    const client = keyed(base);
    client.instance.defaults.adapter = adapter;
    return () => client.request({ method: HttpMethod.GET, url: "/start" });
  }],
  ["an interceptor of the caller", (base, adapter) => {
    const client = keyed(base);
    client.instance.interceptors.request.use((config) => { config.adapter = adapter; return config; });
    return () => client.request({ method: HttpMethod.GET, url: "/start" });
  }],
  ["the request's own config on the client's axios instance", (base, adapter) => {
    const client = keyed(base);
    return () => client.instance.request({ method: "get", url: "/start", adapter });
  }],
];

const CASES = ADAPTERS.flatMap(([adapterName, adapter]) =>
  ROUTES.flatMap(([routeName, route]) => (["302", "307"] as const).map((status) => [adapterName, routeName, status, adapter, route] as const)));

describe.each(CASES)("a keyed request through %s set as %s, the origin answering %s to another host", (_adapterName, _routeName, status, adapter, route) => {
  it("puts no marker key byte at the other host and is refused with keyed_adapter_unsupported", async () => {
    const call = route(`http://127.0.0.1:${origins[status].port}`, adapter());
    const result = await outcome(call);
    expect({ host: "redirect target", connections: next.connections, markers: next.markerBytes }).toEqual({ host: "redirect target", connections: 0, markers: 0 });
    expect({ host: "origin", connections: origins[status].connections, markers: origins[status].markerBytes }).toEqual({ host: "origin", connections: 0, markers: 0 });
    expect(result).toBeInstanceOf(ConfigurationError);
    expect((result as ConfigurationError).code).toBe("keyed_adapter_unsupported");
  });
});

describe("requests the harness sees go through", () => {
  it.each(ADAPTERS)("a request with no key through %s follows the redirect to the other host, which counts the connection", async (_name, adapter) => {
    const client = new HttpClient({ baseUrl: `http://127.0.0.1:${origins["307"].port}`, retryAttempts: 1 });
    (client as unknown as { _axiosInstance: AxiosInstance })._axiosInstance.defaults.adapter = adapter();
    const response = (await client.request({ method: HttpMethod.GET, url: "/open" })) as { status: number };
    expect(response.status).toBe(200);
    expect({ connections: next.connections, markers: next.markerBytes }).toEqual({ connections: 1, markers: 0 });
  });

  it.each(["302", "307"] as const)("a keyed request on axios's http adapter stops at the origin's %s, and the other host sees no marker", async (status) => {
    const client = keyed(`http://127.0.0.1:${origins[status].port}`);
    const result = await outcome(() => client.request({ method: HttpMethod.GET, url: "/start" }));
    expect((result as Error).name).toBe("UnexpectedRedirectError");
    expect({ connections: origins[status].connections, markers: origins[status].markerBytes }).toEqual({ connections: 1, markers: 2 });
    expect({ connections: next.connections, markers: next.markerBytes }).toEqual({ connections: 0, markers: 0 });
  });
});

describe("customAdapterReceivesKeys: true", () => {
  it("sends a keyed request through the caller's adapter function, which receives the keys", async () => {
    const counting = globalFetchAdapter();
    const client = keyed(`http://127.0.0.1:${plain.port}`, { customAdapterReceivesKeys: true });
    client.instance.defaults.adapter = counting.adapter;
    const result = await outcome(() => client.request({ method: HttpMethod.GET, url: "/owned" }));
    expect(counting.calls).toBe(1);
    expect({ connections: plain.connections, markers: plain.markerBytes }).toEqual({ connections: 1, markers: 2 });
    expect((result as { status?: number }).status).toBe(200);
  });
});

// The runtime reads NODE_USE_ENV_PROXY when it starts, from Node.js 22.21 and 24 on: the requests run in a child process.
const [major, minor] = process.versions.node.split(".").map(Number);
const runtimeProxy = major >= 24 || (major === 22 && minor >= 21) ? describe : describe.skip;

runtimeProxy("with the runtime's environment proxy on", () => {
  const proxy = new TunnelSink();
  const target = new Sink();
  beforeAll(async () => { await Promise.all([proxy.listen(), target.listen()]); });
  afterAll(() => { proxy.close(); target.close(); });
  beforeEach(() => { proxy.reset(); target.reset(); });

  const run = (adapter: string): Promise<Record<string, string>> => {
    const env: NodeJS.ProcessEnv = {
      ...process.env, NODE_USE_ENV_PROXY: "1", PROBE_ADAPTER: adapter, PROBE_TARGET_PORT: String(target.port), PROBE_KEY: MARKER_KEY, PROBE_SECRET: MARKER_SECRET,
      HTTP_PROXY: `http://127.0.0.1:${proxy.port}`, http_proxy: `http://127.0.0.1:${proxy.port}`,
      HTTPS_PROXY: `http://127.0.0.1:${proxy.port}`, https_proxy: `http://127.0.0.1:${proxy.port}`,
    };
    for (const name of ["NO_PROXY", "no_proxy", "ALL_PROXY", "all_proxy", "FI_ALLOW_INSECURE_HTTP", "FI_EXTRA_HEADERS"]) delete env[name];
    const tsx = require.resolve("tsx/cli");
    const probe = join(__dirname, "../__fixtures__/axios-adapter-function-probe.ts");
    return new Promise<Record<string, string>>((resolve, reject) => {
      execFile(process.execPath, [tsx, probe], { env, cwd: join(__dirname, "../../.."), timeout: 30_000 }, (error, stdout, stderr) => {
        const last = stdout.trim().split("\n").pop() ?? "";
        if (last.startsWith("{")) resolve(JSON.parse(last) as Record<string, string>);
        else reject(error ?? new Error(`the probe printed no answer: ${stderr}`));
      });
    });
  };

  it.each([
    ["axios's 'fetch' adapter from the axios build the SDK did not load", "other-build-fetch"],
    ["a third-party adapter function that calls the global fetch", "global-fetch"],
  ])("puts no marker key byte at the proxy and refuses each keyed request through %s", async (_name, adapter) => {
    const seen = await run(adapter);
    // the control fetch is the one request the proxy carries: the environment proxy is on
    expect(seen.control).toBe("200");
    expect({ host: "proxy", connections: proxy.connections, tunnels: proxy.tunnels, markers: proxy.markerBytes }).toEqual({ host: "proxy", connections: 1, tunnels: 1, markers: 0 });
    expect({ host: "target", connections: target.connections, markers: target.markerBytes }).toEqual({ host: "target", connections: 0, markers: 0 });
    expect([seen.keyedAuth, seen.keyedCall]).toEqual(["error:ConfigurationError:keyed_adapter_unsupported", "error:ConfigurationError:keyed_adapter_unsupported"]);
  }, 40_000);
});
