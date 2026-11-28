/**
 * `HttpClient` hands its headers to axios, which merges the `common` layer and the layer named for the request method into
 * the headers it writes. The decision for a request is made from that merged set: a Future AGI key held in a `common` or
 * method layer, of the client's defaults or of one call, is a keyed send like a key held in a top-level header. Each case is
 * driven against loopback listeners with a name-resolution shim and counted at the listeners: connections and raw marker
 * bytes at the target and at a redirect target.
 */
import net from "node:net";

import axios from "axios";

import { HttpClient } from "../../api/auth";
import { HttpMethod } from "../../api/types";
import { ConfigurationError } from "../errors";
import { resetHttpWarnings } from "../http-security";
import { MARKER_KEY, MARKER_SECRET, Sink, realConnect, shimConnect } from "../__fixtures__/plaintext-sinks";

const NAMES = ["FI_ALLOW_INSECURE_HTTP", "FI_EXTRA_HEADERS", "FI_API_KEY", "FI_SECRET_KEY", "HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy"];
const target = new Sink();
const redirect = new Sink("302 Found");
const landing = new Sink();
const all = [target, redirect, landing];
const saved: Record<string, string | undefined> = {};

beforeAll(async () => {
  await Promise.all(all.map((sink) => sink.listen()));
  net.Socket.prototype.connect = shimConnect as never;
  (redirect as unknown as { location: string }).location = `http://plain.example.test:${landing.port}/next`;
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

type Headers = Record<string, unknown>;
const REMOTE = (sink: Sink): string => `http://plain.example.test:${sink.port}`;
const LOOPBACK = (sink: Sink): string => `http://127.0.0.1:${sink.port}`;
const bytes = (): number => all.reduce((n, sink) => n + sink.markerBytes, 0);
const connections = (): number => all.reduce((n, sink) => n + sink.connections, 0);

async function outcome(run: () => PromiseLike<unknown>): Promise<unknown> {
  try { await run(); } catch (error) { return error; }
  return undefined;
}

/** A request whose key sits in `layers`: in the client's defaults, or in the headers of the one call. */
interface Case { name: string; defaults?: Headers; call?: Headers; method?: HttpMethod; env?: boolean }
const send = (base: string, entry: Case, allow?: boolean) => {
  if (entry.env === true) process.env.FI_API_KEY = MARKER_KEY;
  const client = new HttpClient({ baseUrl: base, retryAttempts: 1, ...(entry.defaults === undefined ? {} : { defaultHeaders: entry.defaults as never }), ...(allow === undefined ? {} : { allowInsecureHttp: allow }) } as never);
  return client.request({ method: entry.method ?? HttpMethod.GET, url: "/probe", ...(entry.call === undefined ? {} : { headers: entry.call as never }) });
};

const KEYED: Case[] = [
  { name: "a call's common layer X-Api-Key", call: { common: { "X-Api-Key": MARKER_KEY } } },
  { name: "a call's common layer X-Secret-Key", call: { common: { "X-Secret-Key": MARKER_SECRET } } },
  { name: "a call's common layer Authorization Bearer", call: { common: { Authorization: `Bearer ${MARKER_KEY}` } } },
  { name: "a call's common layer in another letter case", call: { common: { "x-API-key": MARKER_KEY } } },
  { name: "a call's get layer X-Api-Key", call: { get: { "X-Api-Key": MARKER_KEY } } },
  { name: "a call's post layer on a POST", method: HttpMethod.POST, call: { post: { "X-Api-Key": MARKER_KEY } } },
  { name: "a call's common layer value holding the environment key", env: true, call: { common: { "X-Trace": `pre-${MARKER_KEY}` } } },
  { name: "a call's get layer value holding the environment key", env: true, call: { get: { "X-Trace": MARKER_KEY } } },
  { name: "a call with a top-level header and a common layer", call: { "X-Team": "blue", common: { "X-Api-Key": MARKER_KEY } } },
  { name: "the client's common layer X-Api-Key", defaults: { common: { "X-Api-Key": MARKER_KEY } } },
  { name: "the client's get layer X-Secret-Key", defaults: { get: { "X-Secret-Key": MARKER_SECRET } } },
  { name: "the client's common layer Authorization Bearer", defaults: { common: { Authorization: `Bearer ${MARKER_SECRET}` } } },
  { name: "the client's common layer value holding the environment key", env: true, defaults: { common: { "X-Trace": `pre-${MARKER_KEY}-post` } } },
];

describe.each(KEYED)("$name", (entry) => {
  it("is refused for a non-loopback plain-http host without the opt-in: no connection, no key byte", async () => {
    const error = await outcome(() => send(REMOTE(target), entry));
    expect(error).toBeInstanceOf(ConfigurationError);
    expect((error as ConfigurationError).code).toBe("insecure_http_origin");
    expect(connections()).toBe(0);
    expect(bytes()).toBe(0);
  });

  it("names neither a key nor a header value in the refusal", async () => {
    const error = await outcome(() => send(REMOTE(target), entry));
    expect(error).toBeInstanceOf(ConfigurationError);
    for (const marker of [MARKER_KEY, MARKER_SECRET]) expect((error as Error).message).not.toContain(marker);
  });

  it("is refused for a Future AGI host whatever the opt-in", async () => {
    process.env.FI_ALLOW_INSECURE_HTTP = "1";
    const error = await outcome(() => send(`http://api.futureagi.com:${target.port}`, entry, true));
    expect(error).toBeInstanceOf(ConfigurationError);
    expect(connections()).toBe(0);
    expect(bytes()).toBe(0);
  });

  it("goes to the target with the opt-in and follows no redirect", async () => {
    const error = await outcome(() => send(REMOTE(redirect), entry, true));
    expect(error).toBeDefined();
    expect(redirect.requests).toBe(1);
    expect(redirect.markerBytes).toBeGreaterThan(0);
    expect(landing.connections).toBe(0);
    expect(landing.markerBytes).toBe(0);
  });

  it("goes to a loopback host without the opt-in", async () => {
    expect(await outcome(() => send(LOOPBACK(target), entry))).toBeUndefined();
    expect(target.markerBytes).toBeGreaterThan(0);
  });
});

describe("a layer axios does not write for the request", () => {
  const UNSENT: Case[] = [
    { name: "a post layer on a GET", call: { post: { "X-Api-Key": MARKER_KEY } } },
    { name: "a put layer of the client's defaults on a GET", defaults: { put: { "X-Secret-Key": MARKER_SECRET } } },
    { name: "a get layer on a POST", method: HttpMethod.POST, call: { get: { "X-Api-Key": MARKER_KEY } } },
  ];

  it.each(UNSENT)("puts no key on the wire, so $name is sent to a non-loopback plain-http host as an unkeyed request", async (entry) => {
    expect(await outcome(() => send(REMOTE(target), entry))).toBeUndefined();
    expect(target.requests).toBe(1);
    expect(target.markerBytes).toBe(0);
  });
});

describe("headers set on axios's global defaults", () => {
  const common = axios.defaults.headers.common as Record<string, unknown>;
  afterEach(() => { delete common["X-Api-Key"]; });

  it("make a client built after them a keyed one: refused for a non-loopback plain-http host without the opt-in", async () => {
    common["X-Api-Key"] = MARKER_KEY;
    const error = await outcome(() => send(REMOTE(target), { name: "global defaults" }));
    expect(error).toBeInstanceOf(ConfigurationError);
    expect(connections()).toBe(0);
    expect(bytes()).toBe(0);
  });

  it("follow no redirect with the opt-in", async () => {
    common["X-Api-Key"] = MARKER_KEY;
    expect(await outcome(() => send(REMOTE(redirect), { name: "global defaults" }, true))).toBeDefined();
    expect(landing.connections).toBe(0);
    expect(landing.markerBytes).toBe(0);
  });
});

describe("a call with no key in any layer", () => {
  it("is sent to a non-loopback plain-http host", async () => {
    expect(await outcome(() => send(REMOTE(target), { name: "plain", defaults: { common: { "X-Team": "blue" } }, call: { get: { "X-Trace": "t-1" } } }))).toBeUndefined();
    expect(target.requests).toBe(1);
  });
});
