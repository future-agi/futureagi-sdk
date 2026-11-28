/**
 * axios's `auth` option (HTTP Basic) is an `Authorization` header the http adapter writes after the headers are judged.
 * A request that an interceptor of the caller gives `auth` is a keyed request: it connects to its host directly, past an
 * environment proxy that axios would read, and follows no redirect. Loopback listeners count connections and the
 * Basic credential token at the target, at a CONNECT-aware proxy sink named by HTTP_PROXY, at an origin that answers a
 * redirect to another host (a name the resolver shim answers with 127.0.0.1) and at that host.
 */
import type { AxiosInstance } from "axios";

import { HttpClient } from "../auth";
import { HttpMethod } from "../types";
import { MARKER_KEY, Sink } from "../../_core/__fixtures__/plaintext-sinks";
import { installNameShim, type NameShim } from "../../_core/__fixtures__/name-shim";
import { TunnelSink } from "../__fixtures__/tunnel-sink";

const TOKEN = Buffer.from(`marker-user:${MARKER_KEY}`).toString("base64");
const tokens = (blob: Buffer): number => blob.toString("latin1").split(TOKEN).length - 1;

const VARS = ["HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy", "FI_ALLOW_INSECURE_HTTP", "FI_EXTRA_HEADERS"];
const saved = new Map(VARS.map((name) => [name, process.env[name]] as const));

const target = new Sink();
const next = new Sink();
let origin: Sink;
const proxy = new TunnelSink();
let shim: NameShim | undefined;

beforeAll(async () => {
  await Promise.all([target.listen(), next.listen(), proxy.listen()]);
  origin = new Sink("302 Found", `http://redirect.localhost:${next.port}/next`);
  await origin.listen();
});
afterAll(() => {
  target.close(); next.close(); origin.close(); proxy.close();
  for (const [name, value] of saved) { if (value === undefined) delete process.env[name]; else process.env[name] = value; }
});
beforeEach(() => {
  for (const name of VARS) delete process.env[name];
  for (const sink of [target, next, origin, proxy]) sink.reset();
  shim = installNameShim({ "redirect.localhost": "127.0.0.1" });
});
afterEach(() => { shim?.restore(); shim = undefined; });

const withBasicAuth = (base: string): HttpClient => {
  const client = new HttpClient({ baseUrl: base, retryAttempts: 1 });
  const instance = (client as unknown as { _axiosInstance: AxiosInstance })._axiosInstance;
  instance.interceptors.request.use((config) => { config.auth = { username: "marker-user", password: MARKER_KEY }; return config; });
  return client;
};
const outcome = async (call: () => Promise<unknown>): Promise<unknown> => {
  try { return await call(); } catch (error) { return error; }
};
const seen = (sink: Sink | TunnelSink): { connections: number; tokens: number } =>
  ({ connections: sink.connections, tokens: tokens(sink instanceof Sink ? Buffer.concat(sink.chunks) : sink.received) });

describe("a request given axios's auth option by an interceptor", () => {
  it("goes to its host directly, not through the proxy HTTP_PROXY names", async () => {
    process.env.HTTP_PROXY = `http://127.0.0.1:${proxy.port}`;
    process.env.http_proxy = `http://127.0.0.1:${proxy.port}`;
    const result = await outcome(() => withBasicAuth(`http://127.0.0.1:${target.port}`).request({ method: HttpMethod.GET, url: "/basic" }));
    expect(seen(proxy)).toEqual({ connections: 0, tokens: 0 });
    expect(seen(target)).toEqual({ connections: 1, tokens: 1 });
    expect((result as { status?: number }).status).toBe(200);
  });

  it("follows no redirect to another host", async () => {
    const result = await outcome(() => withBasicAuth(`http://127.0.0.1:${origin.port}`).request({ method: HttpMethod.GET, url: "/start" }));
    expect(seen(next)).toEqual({ connections: 0, tokens: 0 });
    expect(seen(origin)).toEqual({ connections: 1, tokens: 1 });
    expect((result as Error).name).toBe("UnexpectedRedirectError");
  });
});
