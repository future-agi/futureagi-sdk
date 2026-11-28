/**
 * axios's 'fetch' adapter sends through the runtime's `fetch`: it reads none of the `proxy`, agent or `maxRedirects`
 * settings a keyed request gets, so it follows a redirect to another host with the key and goes through the runtime's
 * environment proxy. A request that carries a key is sent by axios's own http adapter, or by an adapter function the
 * caller wrote; with 'fetch' (set as axios's global default, as the client's default or by an interceptor) it is
 * refused before any connection. Loopback listeners count connections and marker key bytes: the origin, which answers
 * a redirect to another host (a name the resolver shim answers with 127.0.0.1), the redirect target, and a
 * CONNECT-aware proxy sink in a child process with the runtime's environment proxy on.
 */
import { execFile } from "node:child_process";
import { join } from "node:path";

import axios, { type AxiosInstance } from "axios";

import { APIKeyAuth, HttpClient } from "../auth";
import { HttpMethod } from "../types";
import { ConfigurationError } from "../../_core/errors";
import { MARKER_KEY, MARKER_SECRET, Sink } from "../../_core/__fixtures__/plaintext-sinks";
import { installNameShim, type NameShim } from "../../_core/__fixtures__/name-shim";
import { TunnelSink } from "../__fixtures__/tunnel-sink";

const PROXY_VARS = ["HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy", "FI_ALLOW_INSECURE_HTTP", "FI_EXTRA_HEADERS"];
const saved = new Map(PROXY_VARS.map((name) => [name, process.env[name]] as const));

const next = new Sink();
let origin: Sink;
const plain = new Sink();
let shim: NameShim | undefined;

beforeAll(async () => {
  for (const name of PROXY_VARS) delete process.env[name];
  await next.listen();
  origin = new Sink("302 Found", `http://redirect.localhost:${next.port}/next`);
  await Promise.all([origin.listen(), plain.listen()]);
});
afterAll(() => {
  next.close(); origin.close(); plain.close();
  for (const [name, value] of saved) { if (value === undefined) delete process.env[name]; else process.env[name] = value; }
});
beforeEach(() => { next.reset(); origin.reset(); plain.reset(); shim = installNameShim({ "redirect.localhost": "127.0.0.1" }); });
afterEach(() => { shim?.restore(); shim = undefined; });

class Probe extends APIKeyAuth {
  get instance(): AxiosInstance { return this._axiosInstance; }
}
const keyed = (base: string): Probe => new Probe({ fiApiKey: MARKER_KEY, fiSecretKey: MARKER_SECRET, fiBaseUrl: base, retryAttempts: 1 });
const outcome = async (call: () => Promise<unknown>): Promise<unknown> => {
  try { return await call(); } catch (error) { return error; }
};

const ROUTES: Array<[string, (base: string) => Probe]> = [
  ["axios's global default adapter is 'fetch' when the client is built", (base) => {
    const before = axios.defaults.adapter;
    axios.defaults.adapter = "fetch";
    try { return keyed(base); } finally { axios.defaults.adapter = before; }
  }],
  ["the client's axios instance has 'fetch' as its default adapter", (base) => {
    const client = keyed(base);
    client.instance.defaults.adapter = "fetch";
    return client;
  }],
  ["an interceptor of the caller sets the adapter to 'fetch'", (base) => {
    const client = keyed(base);
    client.instance.interceptors.request.use((config) => { config.adapter = "fetch"; return config; });
    return client;
  }],
];

describe.each(ROUTES)("a keyed request when %s", (_route, build) => {
  it("reaches neither the origin nor the host it redirects to, and is refused with ConfigurationError", async () => {
    const client = build(`http://127.0.0.1:${origin.port}`);
    const result = await outcome(() => client.request({ method: HttpMethod.GET, url: "/start" }));
    expect({ connections: next.connections, markers: next.markerBytes }).toEqual({ connections: 0, markers: 0 });
    expect({ connections: origin.connections, markers: origin.markerBytes }).toEqual({ connections: 0, markers: 0 });
    expect(result).toBeInstanceOf(ConfigurationError);
    expect((result as ConfigurationError).code).toBe("keyed_adapter_unsupported");
  });
});

describe("requests the adapter rule leaves as they are", () => {
  it("sends a request with no key through the 'fetch' adapter", async () => {
    const client = new HttpClient({ baseUrl: `http://127.0.0.1:${plain.port}`, retryAttempts: 1 });
    (client as unknown as { _axiosInstance: AxiosInstance })._axiosInstance.defaults.adapter = "fetch";
    const response = (await client.request({ method: HttpMethod.GET, url: "/open" })) as { status: number };
    expect(response.status).toBe(200);
    expect({ connections: plain.connections, markers: plain.markerBytes }).toEqual({ connections: 1, markers: 0 });
  });

  it("sends a keyed request through axios's 'http' adapter chosen by name, and refuses its redirect", async () => {
    const client = keyed(`http://127.0.0.1:${origin.port}`);
    client.instance.defaults.adapter = "http";
    const result = await outcome(() => client.request({ method: HttpMethod.GET, url: "/start" }));
    expect((result as Error).name).toBe("UnexpectedRedirectError");
    expect({ connections: origin.connections, markers: origin.markerBytes }).toEqual({ connections: 1, markers: 2 });
    expect({ connections: next.connections, markers: next.markerBytes }).toEqual({ connections: 0, markers: 0 });
  });
});

// The runtime reads NODE_USE_ENV_PROXY when it starts, from Node.js 22.21 in the 22 line and from 24 on: the requests run
// in a child process.
const [major, minor] = process.versions.node.split(".").map(Number) as [number, number];
const runtimeProxy = major >= 24 || (major === 22 && minor >= 21) ? describe : describe.skip;

runtimeProxy("with the runtime's environment proxy on and axios's default adapter set to 'fetch'", () => {
  const proxy = new TunnelSink();
  const target = new Sink();
  beforeAll(async () => { await Promise.all([proxy.listen(), target.listen()]); });
  afterAll(() => { proxy.close(); target.close(); });

  it("puts no marker key byte at the proxy and refuses each keyed request", async () => {
    const env: NodeJS.ProcessEnv = {
      ...process.env, NODE_USE_ENV_PROXY: "1", PROBE_TARGET_PORT: String(target.port), PROBE_KEY: MARKER_KEY, PROBE_SECRET: MARKER_SECRET,
      HTTP_PROXY: `http://127.0.0.1:${proxy.port}`, http_proxy: `http://127.0.0.1:${proxy.port}`,
      HTTPS_PROXY: `http://127.0.0.1:${proxy.port}`, https_proxy: `http://127.0.0.1:${proxy.port}`,
    };
    for (const name of ["NO_PROXY", "no_proxy", "ALL_PROXY", "all_proxy", "FI_ALLOW_INSECURE_HTTP", "FI_EXTRA_HEADERS"]) delete env[name];
    const tsx = require.resolve("tsx/cli");
    const probe = join(__dirname, "../__fixtures__/axios-fetch-adapter-probe.ts");
    const seen = await new Promise<Record<string, string>>((resolve, reject) => {
      execFile(process.execPath, [tsx, probe], { env, timeout: 60_000 }, (error, stdout) => {
        if (error !== null && stdout === "") reject(error);
        else resolve(JSON.parse(stdout.trim().split("\n").pop() as string) as Record<string, string>);
      });
    });
    // the control fetch is the one request the proxy carries: the environment proxy is on
    expect(seen.control).toBe("200");
    expect({ connections: proxy.connections, markers: proxy.markerBytes }).toEqual({ connections: 1, markers: 0 });
    expect({ connections: target.connections, markers: target.markerBytes }).toEqual({ connections: 0, markers: 0 });
    expect([seen.keyedAuth, seen.keyedCall]).toEqual(["error:ConfigurationError:keyed_adapter_unsupported", "error:ConfigurationError:keyed_adapter_unsupported"]);
  }, 90_000);
});
