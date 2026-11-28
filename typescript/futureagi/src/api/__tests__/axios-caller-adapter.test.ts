/**
 * An adapter function of the caller's runs after the SDK judged the request, and it may add a key before it hands the
 * request to axios's http adapter. The SDK cannot see what such an adapter adds, so a request through one is judged as
 * keyed: plain http to a host that is not loopback is refused without the opt-in, and a request connects to its host
 * directly, past an environment proxy that axios would read. Loopback listeners count connections and marker key bytes
 * at the target, at a CONNECT-aware proxy sink named by HTTP_PROXY, and at a plain-http host the resolver shim answers
 * with 127.0.0.1.
 */
import axios, { type AxiosAdapter, type AxiosInstance } from "axios";

import { HttpClient } from "../auth";
import { HttpMethod } from "../types";
import { MARKER_KEY, Sink } from "../../_core/__fixtures__/plaintext-sinks";
import { installNameShim, type NameShim } from "../../_core/__fixtures__/name-shim";
import { TunnelSink } from "../__fixtures__/tunnel-sink";

const VARS = ["HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy", "FI_ALLOW_INSECURE_HTTP", "FI_EXTRA_HEADERS"];
const saved = new Map(VARS.map((name) => [name, process.env[name]] as const));

const target = new Sink();
const plain = new Sink();
const proxy = new TunnelSink();
let shim: NameShim | undefined;

beforeAll(async () => { await Promise.all([target.listen(), plain.listen(), proxy.listen()]); });
afterAll(() => {
  target.close(); plain.close(); proxy.close();
  for (const [name, value] of saved) { if (value === undefined) delete process.env[name]; else process.env[name] = value; }
});
beforeEach(() => {
  for (const name of VARS) delete process.env[name];
  target.reset(); plain.reset(); proxy.reset();
  shim = installNameShim({ "plain.localhost": "127.0.0.1" });
});
afterEach(() => { shim?.restore(); shim = undefined; });

/** The caller's adapter: it adds a key header and sends with axios's http adapter. */
const addsKey: AxiosAdapter = (config) => {
  config.headers.set("X-Api-Key", MARKER_KEY);
  return axios.getAdapter("http")(config);
};
const throughCallerAdapter = (base: string): HttpClient => {
  const client = new HttpClient({ baseUrl: base, retryAttempts: 1 });
  (client as unknown as { _axiosInstance: AxiosInstance })._axiosInstance.defaults.adapter = addsKey;
  return client;
};
const outcome = async (call: () => Promise<unknown>): Promise<unknown> => {
  try { return await call(); } catch (error) { return error; }
};

describe("a request through an adapter function of the caller's that adds a key", () => {
  it("goes to its host directly, not through the proxy HTTP_PROXY names", async () => {
    process.env.HTTP_PROXY = `http://127.0.0.1:${proxy.port}`;
    process.env.http_proxy = `http://127.0.0.1:${proxy.port}`;
    const result = await outcome(() => throughCallerAdapter(`http://127.0.0.1:${target.port}`).request({ method: HttpMethod.GET, url: "/wrapped" }));
    expect({ connections: proxy.connections, markers: proxy.markerBytes }).toEqual({ connections: 0, markers: 0 });
    expect({ connections: target.connections, markers: target.markerBytes }).toEqual({ connections: 1, markers: 1 });
    expect((result as { status?: number }).status).toBe(200);
  });

  it("is refused over plain http to a host that is not loopback without the opt-in", async () => {
    const result = await outcome(() => throughCallerAdapter(`http://plain.localhost:${plain.port}`).request({ method: HttpMethod.GET, url: "/wrapped" }));
    expect({ connections: plain.connections, markers: plain.markerBytes }).toEqual({ connections: 0, markers: 0 });
    expect((result as { code?: string }).code).toBe("insecure_http_origin");
  });
});
