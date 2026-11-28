/**
 * axios's `transport` option names the module its http adapter sends with, and it wins over `maxRedirects` and
 * `beforeRedirect`: with the follow-redirects http module as the transport, a request follows a redirect whatever
 * `maxRedirects: 0` says, and the SDK's redirect guard is not called. A request that carries a key goes to its host and
 * follows no redirect, whichever way the transport was set (an interceptor of the caller, the client's axios instance
 * defaults, or axios's global defaults when the client is built). Loopback listeners count connections and marker key
 * bytes: the origin at 127.0.0.1, which answers a redirect to another host (the name `localhost`, which the SDK's
 * loopback agent resolves to 127.0.0.1), and the redirect target.
 */
import { createRequire } from "node:module";

import axios, { type AxiosInstance } from "axios";

import { APIKeyAuth } from "../auth";
import { HttpMethod } from "../types";
import { MARKER_KEY, MARKER_SECRET, Sink } from "../../_core/__fixtures__/plaintext-sinks";

const VARS = ["HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy", "FI_ALLOW_INSECURE_HTTP", "FI_EXTRA_HEADERS"];
const saved = new Map(VARS.map((name) => [name, process.env[name]] as const));

/** The follow-redirects module axios itself depends on, resolved from axios's own location. */
const followRedirects = createRequire(require.resolve("axios"))("follow-redirects") as { http: unknown; https: unknown };

const next = new Sink();
let origin: Sink;

beforeAll(async () => {
  for (const name of VARS) delete process.env[name];
  await next.listen();
  origin = new Sink("302 Found", `http://localhost:${next.port}/next`);
  await origin.listen();
});
afterAll(() => {
  next.close(); origin.close();
  for (const [name, value] of saved) { if (value === undefined) delete process.env[name]; else process.env[name] = value; }
});
beforeEach(() => { next.reset(); origin.reset(); });

class Probe extends APIKeyAuth {
  get instance(): AxiosInstance { return this._axiosInstance; }
}
const keyed = (base: string): Probe => new Probe({ fiApiKey: MARKER_KEY, fiSecretKey: MARKER_SECRET, fiBaseUrl: base, retryAttempts: 1 });
const outcome = async (call: () => Promise<unknown>): Promise<unknown> => {
  try { return await call(); } catch (error) { return error; }
};

const ROUTES: Array<[string, (base: string) => Probe]> = [
  ["an interceptor of the caller sets the transport", (base) => {
    const client = keyed(base);
    client.instance.interceptors.request.use((config) => { (config as { transport?: unknown }).transport = followRedirects.http; return config; });
    return client;
  }],
  ["the client's axios instance has the transport as a default", (base) => {
    const client = keyed(base);
    client.instance.defaults.transport = followRedirects.http;
    return client;
  }],
  ["axios's global defaults carry the transport when the client is built", (base) => {
    const before = axios.defaults.transport;
    axios.defaults.transport = followRedirects.http;
    try { return keyed(base); } finally { axios.defaults.transport = before; }
  }],
];

describe.each(ROUTES)("a keyed request whose follow-redirects transport is set when %s", (_route, build) => {
  it("puts no marker key byte at the host the origin redirects to, and does not resolve as a success", async () => {
    const client = build(`http://127.0.0.1:${origin.port}`);
    const result = await outcome(() => client.request({ method: HttpMethod.GET, url: "/start" }));
    const atTarget = { connections: next.connections, markers: next.markerBytes };
    process.stdout.write(`redirect target with the transport set when ${_route}: ${JSON.stringify(atTarget)}\n`);
    expect(atTarget).toEqual({ connections: 0, markers: 0 });
    expect(result).toBeInstanceOf(Error);
  });
});

describe("a keyed request with axios's own transport choice", () => {
  it("stops at the origin's redirect: the redirect target sees no connection and no marker key byte", async () => {
    const client = keyed(`http://127.0.0.1:${origin.port}`);
    const result = await outcome(() => client.request({ method: HttpMethod.GET, url: "/start" }));
    const atTarget = { connections: next.connections, markers: next.markerBytes };
    process.stdout.write(`redirect target with axios's own transport choice: ${JSON.stringify(atTarget)}\n`);
    expect((result as Error).name).toBe("UnexpectedRedirectError");
    expect({ connections: origin.connections, markers: origin.markerBytes }).toEqual({ connections: 1, markers: 2 });
    expect(atTarget).toEqual({ connections: 0, markers: 0 });
  });
});
