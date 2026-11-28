/**
 * HttpClient header forms and the final decision: the key a request carries is judged from the headers that go on the
 * wire. Loopback listeners with a name-resolution shim count connections and raw marker key bytes at each sink.
 */
import net from "node:net";

import { HttpClient } from "../auth";
import { HttpMethod } from "../types";
import { ConfigurationError } from "../../_core/errors";
import { UnexpectedRedirectError } from "../../_core/errors";
import { resetHttpWarnings } from "../../_core/http-security";
import { MARKER_KEY, Sink, realConnect, shimConnect } from "../../_core/__fixtures__/plaintext-sinks";

const NAMES = ["FI_ALLOW_INSECURE_HTTP", "HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy", "FI_API_KEY", "FI_SECRET_KEY"];
const saved: Record<string, string | undefined> = {};

const target = new Sink();
const proxy = new Sink("502 Bad Gateway");
const redirecting = new Sink("302 Found");
const landing = new Sink();
const all = [target, proxy, redirecting, landing];

beforeAll(async () => {
  await Promise.all(all.map((sink) => sink.listen()));
  net.Socket.prototype.connect = shimConnect as never;
  (redirecting as unknown as { location: string }).location = `http://landing.example.test:${landing.port}/next`;
});
afterAll(() => {
  net.Socket.prototype.connect = realConnect;
  all.forEach((sink) => sink.close());
});
beforeEach(() => {
  for (const name of NAMES) { saved[name] = process.env[name]; delete process.env[name]; }
  all.forEach((sink) => sink.reset());
  resetHttpWarnings();
  jest.spyOn(console, "warn").mockImplementation(() => undefined);
});
afterEach(() => {
  jest.restoreAllMocks();
  for (const name of NAMES) { if (saved[name] === undefined) delete process.env[name]; else process.env[name] = saved[name]; }
});

const FUTURE = (sink: Sink): string => `http://api.futureagi.com:${sink.port}`;
const REMOTE = (sink: Sink): string => `http://plain.example.test:${sink.port}`;
const LOOPBACK = (sink: Sink): string => `http://127.0.0.1:${sink.port}`;
const bytes = (): number => all.reduce((n, sink) => n + sink.markerBytes, 0);
const connections = (): number => all.reduce((n, sink) => n + sink.connections, 0);
const wire = (sink: Sink): string => Buffer.concat(sink.chunks).toString("latin1");

function make(base: string, defaultHeaders?: unknown, allow?: boolean): HttpClient {
  return new HttpClient({ baseUrl: base, defaultHeaders: defaultHeaders as never, retryAttempts: 1, timeout: 3000, ...(allow === undefined ? {} : { allowInsecureHttp: allow }) });
}
const get = (client: HttpClient, headers?: unknown) => client.request({ method: HttpMethod.GET, url: "/probe", ...(headers === undefined ? {} : { headers: headers as never }) });
async function outcome(run: () => PromiseLike<unknown>): Promise<unknown> {
  try { await run(); } catch (error) { return error; }
  return undefined;
}

const DEFAULT_FORMS: Array<[string, () => unknown]> = [
  ["a list of pairs", () => [["X-Api-Key", MARKER_KEY]]],
  ["a Headers", () => new Headers({ "X-Api-Key": MARKER_KEY })],
  ["a Map", () => new Map([["X-Api-Key", MARKER_KEY]])],
];

describe("defaultHeaders in every container form", () => {
  it.each(DEFAULT_FORMS)("refuses %s with a key to a Future AGI host over http: no connection, no key byte", async (_name, build) => {
    const error = await outcome(() => get(make(FUTURE(target), build())));
    expect(error).toBeInstanceOf(ConfigurationError);
    expect(connections()).toBe(0);
    expect(bytes()).toBe(0);
  });

  it.each(DEFAULT_FORMS)("sends the key of %s as the header it names, to loopback", async (_name, build) => {
    await outcome(() => get(make(LOOPBACK(target), build())));
    expect(target.requests).toBe(1);
    expect(target.markerBytes).toBe(1);
    expect(wire(target)).toMatch(/^x-api-key: /imu);
    expect(wire(target)).not.toMatch(/^0: /mu);
  });

  it.each(DEFAULT_FORMS)("refuses %s with a key to a non-loopback http host without the opt-in", async (_name, build) => {
    const error = await outcome(() => get(make(REMOTE(target), build())));
    expect(error).toBeInstanceOf(ConfigurationError);
    expect(connections()).toBe(0);
    expect(bytes()).toBe(0);
  });
});

function* generator(): Generator<[string, string]> { yield ["X-Api-Key", MARKER_KEY]; }
const custom = { [Symbol.iterator]: () => ({ next: (() => { let done = false; return () => (done ? { done: true as const, value: undefined } : ((done = true), { done: false as const, value: ["X-Api-Key", MARKER_KEY] as [string, string] })); })() }) };
const CALL_FORMS: Array<[string, () => unknown]> = [
  ["a Set of pairs", () => new Set([["X-Api-Key", MARKER_KEY]])],
  ["a generator", () => generator()],
  ["an array iterator", () => [["X-Api-Key", MARKER_KEY]].values()],
  ["a custom iterable", () => custom],
  ["a pair of length 3", () => [["X-Api-Key", MARKER_KEY, "extra"]]],
  ["a raw string", () => `X-Api-Key: ${MARKER_KEY}`],
];

describe("per-call headers in every container form", () => {
  it.each(CALL_FORMS)("refuses %s with a key to a Future AGI host over http: no connection, no key byte", async (_name, build) => {
    const error = await outcome(() => get(make(FUTURE(target)), build()));
    expect(error).toBeInstanceOf(ConfigurationError);
    expect(connections()).toBe(0);
    expect(bytes()).toBe(0);
  });

  it.each(CALL_FORMS)("refuses %s with a key to a non-loopback http host without the opt-in", async (_name, build) => {
    const error = await outcome(() => get(make(REMOTE(target)), build()));
    expect(error).toBeInstanceOf(ConfigurationError);
    expect(connections()).toBe(0);
    expect(bytes()).toBe(0);
  });
});

describe("a key a request interceptor adds", () => {
  const intercepted = (base: string, allow?: boolean): HttpClient => {
    const client = make(base, undefined, allow);
    (client as unknown as { _axiosInstance: { interceptors: { request: { use(f: (c: { headers: { set(n: string, v: string): void } }) => unknown): void } } } })
      ._axiosInstance.interceptors.request.use((config) => { config.headers.set("X-Api-Key", MARKER_KEY); return config; });
    return client;
  };

  it("is refused to a Future AGI host over http: no connection, no key byte", async () => {
    const error = await outcome(() => get(intercepted(FUTURE(target))));
    expect(error).toBeInstanceOf(ConfigurationError);
    expect(connections()).toBe(0);
    expect(bytes()).toBe(0);
  });

  it("is refused to a non-loopback http host without the opt-in", async () => {
    const error = await outcome(() => get(intercepted(REMOTE(target))));
    expect(error).toBeInstanceOf(ConfigurationError);
    expect(connections()).toBe(0);
    expect(bytes()).toBe(0);
  });

  it("goes straight to the target, not to an environment proxy, with the opt-in", async () => {
    const url = `http://127.0.0.1:${proxy.port}`;
    Object.assign(process.env, { HTTP_PROXY: url, http_proxy: url });
    await outcome(() => get(intercepted(REMOTE(target), true)));
    expect(target.markerBytes).toBe(1);
    expect(proxy.connections).toBe(0);
    expect(proxy.markerBytes).toBe(0);
  });

  it("follows no redirect: the landing host gets no connection and no key byte", async () => {
    const error = await outcome(() => get(intercepted(REMOTE(redirecting), true)));
    expect(error).toBeInstanceOf(UnexpectedRedirectError);
    expect(landing.connections).toBe(0);
    expect(landing.markerBytes).toBe(0);
  });
});

describe("what counts as a key", () => {
  it("an empty X-Api-Key value carries no key: the request is sent to a non-loopback http host without the opt-in", async () => {
    const error = await outcome(() => get(make(REMOTE(target), { "X-Api-Key": "" })));
    expect(error).not.toBeInstanceOf(ConfigurationError);
    expect(target.requests).toBe(1);
    expect(target.markerBytes).toBe(0);
  });

  it("a key in the post layer of the defaults is not a key of a GET: the GET follows its redirect, a POST does not", async () => {
    const layered = { post: { "X-Api-Key": MARKER_KEY } };
    redirecting.reset();
    landing.reset();
    const got = await outcome(() => get(make(LOOPBACK(redirecting), layered)));
    expect(got).not.toBeInstanceOf(UnexpectedRedirectError);
    expect(landing.connections).toBe(1);
    expect(landing.markerBytes).toBe(0);
    landing.reset();
    const posted = await outcome(() => make(LOOPBACK(redirecting), layered).request({ method: HttpMethod.POST, url: "/probe", data: {} }));
    expect(posted).toBeInstanceOf(UnexpectedRedirectError);
    expect(landing.connections).toBe(0);
    expect(landing.markerBytes).toBe(0);
  });
});
