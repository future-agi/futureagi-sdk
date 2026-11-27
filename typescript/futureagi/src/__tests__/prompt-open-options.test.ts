// The client options of a Prompt instance in every request that Prompt.open() sends.
//
// open() sends no request for a template with an id. For a template with a name it looks the name up (the label
// lookup for "production", then the lookup by name when that label has no version) and creates the template when the
// name is not found; a template without a name is created directly. Each of these requests carries the keys of the
// instance and is sent with the options of the instance: an explicit `allowInsecureHttp: false` takes precedence over
// FI_ALLOW_INSECURE_HTTP=1, so a request to a plain-http host that is not loopback is refused with code
// insecure_http_origin before any connection is made, and open() rejects with that error (code at top level) instead
// of reading the refused lookup as "not found" and going on to create.
//
// Every listener here is on the loopback address. The host name below resolves to 127.0.0.1 through a lookup shim, so
// a request to it counts as a request to a host that is not loopback while its bytes land in a listener of this file.
// The proxy variables point at a second listener (with no exemptions), which records any request that goes through
// a proxy. Keys are random marker strings made per test, and the bytes of them that reach each listener are counted.

/* eslint-disable @typescript-eslint/no-explicit-any */
import { randomBytes } from "node:crypto";
import * as net from "node:net";

import { HttpClient } from "../api/auth";
import { Prompt } from "../prompt/client";
import { PromptTemplate } from "../prompt/types";

/** Milliseconds from a monotonic clock. */
const clockMs = (): number => Number(process.hrtime.bigint()) / 1e6;

// eslint-disable-next-line @typescript-eslint/no-var-requires
const dns: typeof import("node:dns") = require("node:dns");

jest.setTimeout(60_000);

const SHIM_HOST = "guard-target.futureagi.com";
const CODE = "insecure_http_origin";
const BOUND_MS = 20_000;

const LABEL_ROUTE = "/model-hub/prompt-labels/get-by-name/";
const BY_NAME_ROUTE = "/model-hub/prompt-templates/get-template-by-name/";
const CREATE_ROUTE = "/model-hub/prompt-templates/create-draft/";

// --- lookup shim ----------------------------------------------------------------------------------------------

const realLookup = dns.lookup;
beforeAll(() => {
  (dns as any).lookup = function lookup(hostname: string, options: any, callback: any) {
    if (typeof options === "function") {
      callback = options;
      options = {};
    }
    if (String(hostname).toLowerCase() === SHIM_HOST) {
      const all = typeof options === "object" && options !== null && options.all === true;
      process.nextTick(() => (all ? callback(null, [{ address: "127.0.0.1", family: 4 }]) : callback(null, "127.0.0.1", 4)));
      return {};
    }
    return (realLookup as any).call(dns, hostname, options, callback);
  };
});
afterAll(() => {
  (dns as any).lookup = realLookup;
});

// --- listeners ------------------------------------------------------------------------------------------------

interface Reply {
  status: number;
  body: string;
}

interface Sink {
  port: number;
  connections: number;
  /** "METHOD /path" of each request received, in order. */
  requests: string[];
  count(markers: string[]): number;
  close(): Promise<void>;
}

const STATUS_TEXT: Record<number, string> = { 200: "OK", 400: "Bad Request", 404: "Not Found" };

/** A raw listener that records every connection and byte, and answers each request with `respond(method, path)`
 * (one request per connection, Connection: close). */
async function sink(respond: (method: string, path: string) => Reply): Promise<Sink> {
  const chunks: string[] = [];
  const requests: string[] = [];
  const sockets = new Set<net.Socket>();
  const state = { connections: 0 };
  const server = net.createServer((socket) => {
    state.connections++;
    sockets.add(socket);
    socket.on("close", () => sockets.delete(socket));
    socket.on("error", () => undefined);
    let head = "";
    let answered = false;
    socket.on("data", (data) => {
      const text = data.toString("latin1");
      chunks.push(text);
      if (answered) return;
      head += text;
      if (!head.includes("\r\n\r\n")) return;
      answered = true;
      const [method = "", target = ""] = head.split("\r\n")[0].split(" ");
      let path = target;
      try {
        path = new URL(target, "http://listener.invalid").pathname;
      } catch {
        // the raw request target is kept
      }
      requests.push(`${method} ${path}`);
      const reply = respond(method, path);
      socket.end(
        `HTTP/1.1 ${reply.status} ${STATUS_TEXT[reply.status] ?? "Status"}\r\nContent-Type: application/json\r\n` +
          `Content-Length: ${Buffer.byteLength(reply.body)}\r\nConnection: close\r\n\r\n${reply.body}`,
      );
    });
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  return {
    port: (server.address() as net.AddressInfo).port,
    get connections() {
      return state.connections;
    },
    requests,
    count(markers: string[]) {
      const all = chunks.join("");
      let bytes = 0;
      for (const marker of markers) {
        for (let at = all.indexOf(marker); at >= 0; at = all.indexOf(marker, at + marker.length)) bytes += marker.length;
      }
      return bytes;
    },
    close: () =>
      new Promise<void>((resolve) => {
        for (const socket of sockets) socket.destroy();
        server.close(() => resolve());
      }),
  };
}

const marker = (tag: string) => `fitest_${tag}_${randomBytes(8).toString("hex")}`;

// --- the server side of each path -----------------------------------------------------------------------------

const json = (status: number, body: unknown): Reply => ({ status, body: JSON.stringify(body) });

function foundTemplate(id: string, name: string): Record<string, unknown> {
  return {
    id,
    name,
    version: "v1",
    prompt_config: [{ messages: [{ role: "user", content: "Hello {{who}}" }], configuration: { model: "gpt-4o-mini" } }],
  };
}

/** The label lookup finds the template. */
const lookupFinds = (name: string) => (method: string, path: string): Reply =>
  method === "GET" && path === LABEL_ROUTE ? json(200, foundTemplate("tpl-found", name)) : json(404, { result: "not here" });

/** The label lookup answers that the label has no version, and the lookup by name finds the template. */
const fallbackFinds = (name: string) => (method: string, path: string): Reply => {
  if (method === "GET" && path === LABEL_ROUTE) return json(400, { result: "No version found for label production" });
  if (method === "GET" && path === BY_NAME_ROUTE) return json(200, foundTemplate("tpl-by-name", name));
  return json(404, { result: "not here" });
};

/** Neither lookup finds the name; the create request is answered with a new template. */
const nothingFound = (name: string) => (method: string, path: string): Reply => {
  if (method === "POST" && path === CREATE_ROUTE) return json(200, { result: { id: "tpl-created", name, template_version: "v1" } });
  return json(404, { result: "no template with that name" });
};

// --- settling within a bound ----------------------------------------------------------------------------------

type Outcome =
  | { settled: true; rejected: false; value: unknown; elapsedMs: number }
  | { settled: true; rejected: true; error: unknown; elapsedMs: number }
  | { settled: false; elapsedMs: number };

/** `promise` raced against `ms`: an outcome that is not settled when the bound passes first. */
async function settleWithin(promise: Promise<unknown>, ms: number): Promise<Outcome> {
  const started = clockMs();
  let timer: NodeJS.Timeout | undefined;
  const expiry = new Promise<Outcome>((resolve) => {
    timer = setTimeout(() => resolve({ settled: false, elapsedMs: clockMs() - started }), ms);
  });
  const result = promise.then(
    (value): Outcome => ({ settled: true, rejected: false, value, elapsedMs: clockMs() - started }),
    (error: unknown): Outcome => ({ settled: true, rejected: true, error, elapsedMs: clockMs() - started }),
  );
  try {
    return await Promise.race([result, expiry]);
  } finally {
    clearTimeout(timer);
  }
}

// --- environment ----------------------------------------------------------------------------------------------

const ENV_NAMES = [
  "HTTP_PROXY",
  "http_proxy",
  "HTTPS_PROXY",
  "https_proxy",
  "ALL_PROXY",
  "all_proxy",
  "NO_PROXY",
  "no_proxy",
  "FI_ALLOW_INSECURE_HTTP",
  "FI_API_KEY",
  "FI_SECRET_KEY",
  "FI_BASE_URL",
];

let savedEnv: Map<string, string | undefined>;
let target: Sink | undefined;
let proxy: Sink | undefined;
let sent: string[] = [];
const closers: Array<() => Promise<void> | void> = [];

/** The listeners for one test, with the proxy variables set to the proxy listener and (with `optIn`) the opt-in
 * variable set to 1. */
async function setUp(respond: (method: string, path: string) => Reply, optIn = true): Promise<{ target: Sink; proxy: Sink; baseUrl: string }> {
  target = await sink(respond);
  proxy = await sink(() => json(200, {}));
  const proxyUrl = `http://127.0.0.1:${proxy.port}`;
  for (const name of ["HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy"]) process.env[name] = proxyUrl;
  process.env.NO_PROXY = "";
  process.env.no_proxy = "";
  if (optIn) process.env.FI_ALLOW_INSECURE_HTTP = "1";
  return { target, proxy, baseUrl: `http://${SHIM_HOST}:${target.port}` };
}

beforeEach(() => {
  savedEnv = new Map(ENV_NAMES.map((name) => [name, process.env[name]]));
  for (const name of ENV_NAMES) delete process.env[name];
  sent = [];
  // Every request the SDK client makes (an instance or a client of its own) passes here: its method and URL are noted.
  const original = HttpClient.prototype.request;
  jest.spyOn(HttpClient.prototype, "request").mockImplementation(function (this: HttpClient, config: any, handler?: any) {
    sent.push(`${String(config?.method ?? "").toUpperCase()} ${String(config?.url ?? "")}`);
    return original.call(this, config, handler);
  } as any);
});

afterEach(async () => {
  jest.restoreAllMocks();
  for (const close of closers.splice(0)) await close();
  if (target) await target.close();
  if (proxy) await proxy.close();
  target = undefined;
  proxy = undefined;
  for (const [name, value] of savedEnv) {
    if (value === undefined) delete process.env[name];
    else process.env[name] = value;
  }
});

function prompt(template: PromptTemplate, keys: string[], baseUrl: string, extra: Record<string, unknown>): Prompt {
  const client = new Prompt(template, { fiApiKey: keys[0], fiSecretKey: keys[1], fiBaseUrl: baseUrl, timeout: 3_000, retryAttempts: 1, ...extra } as any);
  closers.push(() => client.close());
  return client;
}

function template(fields: Partial<PromptTemplate>): PromptTemplate {
  return new PromptTemplate({ messages: [{ role: "user", content: "Hello {{who}}" } as any], ...fields });
}

/** The outcome of open() as the caller and the listeners saw it, for a call that is expected to be refused. */
function observed(outcome: Outcome, keys: string[], sinks: { target: Sink; proxy: Sink }) {
  const error = outcome.settled && outcome.rejected ? outcome.error : undefined;
  const summary = {
    settled: outcome.settled,
    rejected: outcome.settled && outcome.rejected,
    isError: error instanceof Error,
    code: (error as { code?: unknown } | undefined)?.code,
    targetConnections: sinks.target.connections,
    targetKeyBytes: sinks.target.count(keys),
    proxyConnections: sinks.proxy.connections,
    proxyKeyBytes: sinks.proxy.count(keys),
    createAttempts: sent.filter((line) => line.startsWith("POST ") && line.includes(CREATE_ROUTE)).length,
    elapsedMs: outcome.elapsedMs,
    errorText: error instanceof Error ? `${error.name}: ${error.message}` : undefined,
  };
  if (process.env.FI_TEST_TRACE) console.log(JSON.stringify({ ...summary, received: sinks.target.requests, sent }));
  return summary;
}

const REFUSED = {
  settled: true,
  rejected: true,
  isError: true,
  code: CODE,
  targetConnections: 0,
  targetKeyBytes: 0,
  proxyConnections: 0,
  proxyKeyBytes: 0,
  createAttempts: 0,
  elapsedMs: expect.any(Number),
  errorText: expect.any(String),
};

// --- explicit false with the variable set ---------------------------------------------------------------------

describe("Prompt.open() with allowInsecureHttp: false and FI_ALLOW_INSECURE_HTTP=1, for a plain-http host that is not loopback", () => {
  test("a template with a name that the label lookup would find: open() rejects with code insecure_http_origin and no connection is made", async () => {
    const name = `tpl-${randomBytes(4).toString("hex")}`;
    const sinks = await setUp(lookupFinds(name));
    const keys = [marker("pok"), marker("pos")];
    const client = prompt(template({ name }), keys, sinks.baseUrl, { allowInsecureHttp: false });
    const outcome = await settleWithin(client.open(), BOUND_MS);
    expect(observed(outcome, keys, sinks)).toEqual(REFUSED);
    expect(client.template?.id).toBeUndefined();
  });

  test("a template with a name whose label has no version and that the lookup by name would find: open() rejects with code insecure_http_origin and no connection is made", async () => {
    const name = `tpl-${randomBytes(4).toString("hex")}`;
    const sinks = await setUp(fallbackFinds(name));
    const keys = [marker("pok"), marker("pos")];
    const client = prompt(template({ name }), keys, sinks.baseUrl, { allowInsecureHttp: false });
    const outcome = await settleWithin(client.open(), BOUND_MS);
    expect(observed(outcome, keys, sinks)).toEqual(REFUSED);
    expect(client.template?.id).toBeUndefined();
  });

  test("a template with a name that neither lookup would find: open() rejects with code insecure_http_origin from the lookup, makes no create attempt and no connection", async () => {
    const name = `tpl-${randomBytes(4).toString("hex")}`;
    const sinks = await setUp(nothingFound(name));
    const keys = [marker("pok"), marker("pos")];
    const client = prompt(template({ name }), keys, sinks.baseUrl, { allowInsecureHttp: false });
    const outcome = await settleWithin(client.open(), BOUND_MS);
    expect(observed(outcome, keys, sinks)).toEqual(REFUSED);
    expect(client.template?.id).toBeUndefined();
  });

  test("control: a template without a name goes to create, which is refused with code insecure_http_origin with no connection made", async () => {
    const sinks = await setUp(nothingFound("unnamed"));
    const keys = [marker("pok"), marker("pos")];
    const client = prompt(template({}), keys, sinks.baseUrl, { allowInsecureHttp: false });
    const outcome = await settleWithin(client.open(), BOUND_MS);
    // The create request is attempted (and refused before it connects); there is no lookup to make first.
    expect(observed(outcome, keys, sinks)).toEqual({ ...REFUSED, createAttempts: 1 });
    expect(sent.filter((line) => line.startsWith("GET "))).toEqual([]);
  });

  test("control: a template with an id sends no request and open() resolves to the same instance", async () => {
    const sinks = await setUp(lookupFinds("with-id"));
    const keys = [marker("pok"), marker("pos")];
    const client = prompt(template({ id: "tpl-given", name: "with-id" }), keys, sinks.baseUrl, { allowInsecureHttp: false });
    const outcome = await settleWithin(client.open(), BOUND_MS);
    expect({
      settled: outcome.settled,
      sameInstance: outcome.settled && !outcome.rejected && outcome.value === client,
      sent,
      targetConnections: sinks.target.connections,
      targetKeyBytes: sinks.target.count(keys),
      proxyConnections: sinks.proxy.connections,
      proxyKeyBytes: sinks.proxy.count(keys),
    }).toEqual({ settled: true, sameInstance: true, sent: [], targetConnections: 0, targetKeyBytes: 0, proxyConnections: 0, proxyKeyBytes: 0 });
  });
});

// --- a refusal from the lookup is not read as "not found" -----------------------------------------------------

describe("Prompt.open() surfaces a refused lookup", () => {
  test("with neither the option nor the variable, a template with a name rejects with code insecure_http_origin from the lookup and no create attempt is made", async () => {
    const name = `tpl-${randomBytes(4).toString("hex")}`;
    const sinks = await setUp(nothingFound(name), false);
    const keys = [marker("pok"), marker("pos")];
    const client = prompt(template({ name }), keys, sinks.baseUrl, {});
    const outcome = await settleWithin(client.open(), BOUND_MS);
    expect(observed(outcome, keys, sinks)).toEqual(REFUSED);
  });
});

// --- the variable alone ---------------------------------------------------------------------------------------

describe("without the option, FI_ALLOW_INSECURE_HTTP=1 lets Prompt.open() reach a plain-http host that is not loopback", () => {
  test("control: a template with a name that the label lookup finds is adopted, with the keys sent directly to the host", async () => {
    const name = `tpl-${randomBytes(4).toString("hex")}`;
    const sinks = await setUp(lookupFinds(name));
    const keys = [marker("pok"), marker("pos")];
    const client = prompt(template({ name }), keys, sinks.baseUrl, {});
    const outcome = await settleWithin(client.open(), BOUND_MS);
    const summary = {
      settled: outcome.settled,
      rejected: outcome.settled && outcome.rejected,
      errorText: outcome.settled && outcome.rejected ? String(outcome.error) : undefined,
      templateId: client.template?.id,
      received: sinks.target.requests,
      targetCarriesKeys: sinks.target.count(keys) > 0,
      proxyConnections: sinks.proxy.connections,
      proxyKeyBytes: sinks.proxy.count(keys),
    };
    if (process.env.FI_TEST_TRACE) console.log(JSON.stringify({ ...summary, targetKeyBytes: sinks.target.count(keys) }));
    expect(summary).toEqual({
      settled: true,
      rejected: false,
      errorText: undefined,
      templateId: "tpl-found",
      received: [`GET ${LABEL_ROUTE}`],
      targetCarriesKeys: true,
      proxyConnections: 0,
      proxyKeyBytes: 0,
    });
  });

  test("control: a template with a name that neither lookup finds is created, with the keys sent directly to the host", async () => {
    const name = `tpl-${randomBytes(4).toString("hex")}`;
    const sinks = await setUp(nothingFound(name));
    const keys = [marker("pok"), marker("pos")];
    const client = prompt(template({ name }), keys, sinks.baseUrl, {});
    const outcome = await settleWithin(client.open(), BOUND_MS);
    const summary = {
      settled: outcome.settled,
      rejected: outcome.settled && outcome.rejected,
      errorText: outcome.settled && outcome.rejected ? String(outcome.error) : undefined,
      templateId: client.template?.id,
      lookedUp: sinks.target.requests.some((line) => line === `GET ${LABEL_ROUTE}`),
      created: sinks.target.requests.filter((line) => line === `POST ${CREATE_ROUTE}`).length,
      targetCarriesKeys: sinks.target.count(keys) > 0,
      proxyConnections: sinks.proxy.connections,
      proxyKeyBytes: sinks.proxy.count(keys),
    };
    if (process.env.FI_TEST_TRACE) console.log(JSON.stringify({ ...summary, received: sinks.target.requests, targetKeyBytes: sinks.target.count(keys) }));
    expect(summary).toEqual({
      settled: true,
      rejected: false,
      errorText: undefined,
      templateId: "tpl-created",
      lookedUp: true,
      created: 1,
      targetCarriesKeys: true,
      proxyConnections: 0,
      proxyKeyBytes: 0,
    });
  });
});
