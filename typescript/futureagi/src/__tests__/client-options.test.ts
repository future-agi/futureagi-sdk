// The allowInsecureHttp option of the KnowledgeBase, Annotation, ProviderAPIKeyClient and APIKeyManager clients.
//
// An explicit `allowInsecureHttp: false` takes precedence over FI_ALLOW_INSECURE_HTTP=1: a keyed request to a
// plain-http host that is not loopback is refused with code insecure_http_origin and no connection is made. Without
// the option, FI_ALLOW_INSECURE_HTTP=1 lets the same request reach its host.
//
// Every listener here is on the loopback address. The host name below resolves to 127.0.0.1 through a lookup shim, so
// a request to it counts as a request to a host that is not loopback while its bytes land in a listener of this file.
// The proxy variables point at a second listener (with no exemptions), which records any request that goes through
// a proxy. Keys are random marker strings made per test.

/* eslint-disable @typescript-eslint/no-explicit-any */
import { randomBytes } from "node:crypto";
import * as net from "node:net";

import { KnowledgeBase } from "../kb/client";
import { Annotation } from "../annotations/annotation";
import { ProviderAPIKeyClient, APIKeyManager } from "../api/apikeys";
import { ModelProvider } from "../api/types";
import { Prompt } from "../prompt/client";
import { PromptTemplate } from "../prompt/types";

// eslint-disable-next-line @typescript-eslint/no-var-requires
const dns: typeof import("node:dns") = require("node:dns");

jest.setTimeout(30_000);

const SHIM_HOST = "guard-target.futureagi.com";
const CODE = "insecure_http_origin";
const BOUND_MS = 5_000;

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

interface Sink {
  port: number;
  connections: number;
  count(markers: string[]): number;
  close(): Promise<void>;
}

/** A raw listener that records every connection and byte, and answers a request with `body` as JSON. */
async function sink(body: string): Promise<Sink> {
  const chunks: string[] = [];
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
      socket.end(`HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: ${Buffer.byteLength(body)}\r\nConnection: close\r\n\r\n${body}`);
    });
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  return {
    port: (server.address() as net.AddressInfo).port,
    get connections() {
      return state.connections;
    },
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

// --- settling within a bound ----------------------------------------------------------------------------------

type Outcome =
  | { settled: true; rejected: false; value: unknown; elapsedMs: number }
  | { settled: true; rejected: true; error: unknown; elapsedMs: number }
  | { settled: false; elapsedMs: number };

/** `promise` raced against `ms`: an outcome that is not settled when the bound passes first. */
async function settleWithin(promise: Promise<unknown>, ms: number): Promise<Outcome> {
  const started = Date.now();
  let timer: NodeJS.Timeout | undefined;
  const expiry = new Promise<Outcome>((resolve) => {
    timer = setTimeout(() => resolve({ settled: false, elapsedMs: Date.now() - started }), ms);
  });
  const result = promise.then(
    (value): Outcome => ({ settled: true, rejected: false, value, elapsedMs: Date.now() - started }),
    (error: unknown): Outcome => ({ settled: true, rejected: true, error, elapsedMs: Date.now() - started }),
  );
  try {
    return await Promise.race([result, expiry]);
  } finally {
    clearTimeout(timer);
  }
}

/** The error in `error` or in its chain of causes that carries `code` (a client may wrap it). */
function withCode(error: unknown, code: string): { code?: unknown } | undefined {
  const seen = new Set<unknown>();
  for (let current = error; typeof current === "object" && current !== null && !seen.has(current); current = (current as { cause?: unknown }).cause) {
    seen.add(current);
    if ((current as { code?: unknown }).code === code) return current as { code?: unknown };
  }
  return undefined;
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
const closers: Array<() => Promise<void> | void> = [];

/** The listeners for one test, with the proxy variables set to the proxy listener and (with `optIn`) the opt-in
 * variable set to 1. */
async function setUp(body: string, optIn = true): Promise<{ target: Sink; proxy: Sink; baseUrl: string }> {
  target = await sink(body);
  proxy = await sink(JSON.stringify({}));
  const proxyUrl = `http://127.0.0.1:${proxy.port}`;
  for (const name of ["HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy"]) process.env[name] = proxyUrl;
  process.env.NO_PROXY = "";
  process.env.no_proxy = "";
  if (optIn) process.env.FI_ALLOW_INSECURE_HTTP = "1";
  return { target, proxy, baseUrl: `http://${SHIM_HOST}:${target.port}` };
}

function resetManager(): void {
  (APIKeyManager as any)._instance = undefined;
}

beforeEach(() => {
  savedEnv = new Map(ENV_NAMES.map((name) => [name, process.env[name]]));
  for (const name of ENV_NAMES) delete process.env[name];
  resetManager();
});

afterEach(async () => {
  const manager = (APIKeyManager as any)._instance as { close?: () => Promise<void> } | undefined;
  resetManager();
  if (manager && typeof manager.close === "function") await manager.close();
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

/** The outcome of a call as the caller and the listeners saw it, for a call that is expected to be refused. */
function observed(outcome: Outcome, keys: string[], sinks: { target: Sink; proxy: Sink }, topLevelCode: boolean) {
  const error = outcome.settled && outcome.rejected ? outcome.error : undefined;
  const found = topLevelCode ? ((error as { code?: unknown } | undefined)?.code === CODE ? error : undefined) : withCode(error, CODE);
  return {
    settled: outcome.settled,
    rejected: outcome.settled && outcome.rejected,
    isError: error instanceof Error,
    code: (found as { code?: unknown } | undefined)?.code,
    targetConnections: sinks.target.connections,
    targetKeyBytes: sinks.target.count(keys),
    proxyConnections: sinks.proxy.connections,
    proxyKeyBytes: sinks.proxy.count(keys),
    elapsedMs: outcome.elapsedMs,
    errorText: error instanceof Error ? `${error.name}: ${error.message}` : undefined,
  };
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
  elapsedMs: expect.any(Number),
  errorText: expect.any(String),
};

/** The outcome of a call that is expected to reach its host: one connection carrying the keys, none at the proxy. */
function reached(outcome: Outcome, keys: string[], sinks: { target: Sink; proxy: Sink }) {
  const summary = {
    settled: outcome.settled,
    rejected: outcome.settled && outcome.rejected,
    errorText: outcome.settled && outcome.rejected ? String(outcome.error) : undefined,
    targetConnections: sinks.target.connections,
    targetCarriesKeys: sinks.target.count(keys) > 0,
    proxyConnections: sinks.proxy.connections,
    elapsedMs: outcome.elapsedMs,
  };
  if (process.env.FI_TEST_TRACE) console.log(JSON.stringify({ ...summary, targetKeyBytes: sinks.target.count(keys) }));
  return summary;
}

const REACHED = {
  settled: true,
  rejected: false,
  errorText: undefined,
  targetConnections: 1,
  targetCarriesKeys: true,
  proxyConnections: 0,
  elapsedMs: expect.any(Number),
};

const KB_REPLY = JSON.stringify({ status: true, result: { table_data: [] } });
const LABELS_REPLY = JSON.stringify({ status: true, result: [] });
const API_KEYS_REPLY = JSON.stringify({ results: [] });
const TEMPLATE_REPLY = JSON.stringify({
  id: "tpl-found",
  name: "tpl-named",
  version: "v1",
  prompt_config: [{ messages: [{ role: "user", content: "Hello {{who}}" }], configuration: { model: "gpt-4o-mini" } }],
});

// --- the clients ----------------------------------------------------------------------------------------------

function knowledgeBase(apiKey: string, secretKey: string, baseUrl: string, extra: Record<string, unknown>): KnowledgeBase {
  const client = new KnowledgeBase(undefined, { fiApiKey: apiKey, fiSecretKey: secretKey, fiBaseUrl: baseUrl, timeout: 3_000, ...extra } as any);
  closers.push(() => client.close());
  return client;
}

function annotation(apiKey: string, secretKey: string, baseUrl: string, extra: Record<string, unknown>): Annotation {
  const client = new Annotation({ fiApiKey: apiKey, fiSecretKey: secretKey, fiBaseUrl: baseUrl, timeout: 3_000, ...extra } as any);
  closers.push(() => client.close());
  return client;
}

function providerClient(apiKey: string, secretKey: string, baseUrl: string, options?: Record<string, unknown>): ProviderAPIKeyClient {
  const args: unknown[] = [{ provider: ModelProvider.OPENAI }, apiKey, secretKey, baseUrl];
  if (options !== undefined) args.push(options);
  const client = new (ProviderAPIKeyClient as any)(...args) as ProviderAPIKeyClient;
  closers.push(() => client.close());
  return client;
}

function prompt(apiKey: string, secretKey: string, baseUrl: string, extra: { allowInsecureHttp?: boolean }): Prompt {
  const template = new PromptTemplate({ name: "tpl-named", messages: [{ role: "user", content: "Hello {{who}}" } as any] });
  const client = new Prompt(template, { fiApiKey: apiKey, fiSecretKey: secretKey, fiBaseUrl: baseUrl, timeout: 3_000, ...extra } as any);
  closers.push(() => client.close());
  return client;
}

function managerFromEnv(apiKey: string, secretKey: string, baseUrl: string, options?: Record<string, unknown>): APIKeyManager {
  process.env.FI_API_KEY = apiKey;
  process.env.FI_SECRET_KEY = secretKey;
  process.env.FI_BASE_URL = baseUrl;
  return options === undefined ? APIKeyManager.getInstance() : (APIKeyManager as any).getInstance(options);
}

// --- explicit false with the variable set ---------------------------------------------------------------------

describe("allowInsecureHttp: false takes precedence over FI_ALLOW_INSECURE_HTTP=1 for a plain-http host that is not loopback", () => {
  test("KnowledgeBase: listKbs is refused with code insecure_http_origin and no connection is made", async () => {
    const sinks = await setUp(KB_REPLY);
    const keys = [marker("kbk"), marker("kbs")];
    const client = knowledgeBase(keys[0], keys[1], sinks.baseUrl, { allowInsecureHttp: false });
    const outcome = await settleWithin(client.listKbs(), BOUND_MS);
    expect(observed(outcome, keys, sinks, false)).toEqual(REFUSED);
  });

  test("Annotation: getLabels is refused and the error it surfaces carries code insecure_http_origin, with no connection made", async () => {
    const sinks = await setUp(LABELS_REPLY);
    const keys = [marker("ank"), marker("ans")];
    const client = annotation(keys[0], keys[1], sinks.baseUrl, { allowInsecureHttp: false });
    const outcome = await settleWithin(client.getLabels(), BOUND_MS);
    expect(observed(outcome, keys, sinks, true)).toEqual(REFUSED);
  });

  test("ProviderAPIKeyClient: get with the options argument after fiBaseUrl is refused with code insecure_http_origin and no connection is made", async () => {
    const sinks = await setUp(API_KEYS_REPLY);
    const keys = [marker("pkk"), marker("pks")];
    const client = providerClient(keys[0], keys[1], sinks.baseUrl, { allowInsecureHttp: false });
    const outcome = await settleWithin(client.get(), BOUND_MS);
    expect(observed(outcome, keys, sinks, true)).toEqual(REFUSED);
  });

  test("APIKeyManager: an instance first created by getInstance with the option refuses listProviderApiKeys with code insecure_http_origin and makes no connection", async () => {
    const sinks = await setUp(API_KEYS_REPLY);
    const keys = [marker("mgk"), marker("mgs")];
    const manager = managerFromEnv(keys[0], keys[1], sinks.baseUrl, { allowInsecureHttp: false });
    const outcome = await settleWithin(manager.listProviderApiKeys(), BOUND_MS);
    expect(observed(outcome, keys, sinks, true)).toEqual(REFUSED);
  });

  test("Prompt: open() for a template with a name is refused at the lookup with code insecure_http_origin and no connection is made", async () => {
    const sinks = await setUp(TEMPLATE_REPLY);
    const keys = [marker("prk"), marker("prs")];
    const client = prompt(keys[0], keys[1], sinks.baseUrl, { allowInsecureHttp: false });
    const outcome = await settleWithin(client.open(), BOUND_MS);
    expect(observed(outcome, keys, sinks, true)).toEqual(REFUSED);
  });
});

// --- the refusal as Annotation surfaces it --------------------------------------------------------------------

describe("Annotation surfaces a refusal with its code", () => {
  test("getLabels to a plain-http host that is not loopback, with neither the option nor the variable, rejects with an Error whose code is insecure_http_origin", async () => {
    const sinks = await setUp(LABELS_REPLY, false);
    const keys = [marker("ank"), marker("ans")];
    const client = annotation(keys[0], keys[1], sinks.baseUrl, {});
    const outcome = await settleWithin(client.getLabels(), BOUND_MS);
    expect(observed(outcome, keys, sinks, true)).toEqual(REFUSED);
  });
});

// --- the variable alone ---------------------------------------------------------------------------------------

describe("without the option, FI_ALLOW_INSECURE_HTTP=1 lets a keyed request reach a plain-http host that is not loopback", () => {
  test("KnowledgeBase: listKbs reaches the host directly with the keys", async () => {
    const sinks = await setUp(KB_REPLY);
    const keys = [marker("kbk"), marker("kbs")];
    const client = knowledgeBase(keys[0], keys[1], sinks.baseUrl, {});
    const outcome = await settleWithin(client.listKbs(), BOUND_MS);
    expect(reached(outcome, keys, sinks)).toEqual(REACHED);
  });

  test("Annotation: getLabels reaches the host directly with the keys", async () => {
    const sinks = await setUp(LABELS_REPLY);
    const keys = [marker("ank"), marker("ans")];
    const client = annotation(keys[0], keys[1], sinks.baseUrl, {});
    const outcome = await settleWithin(client.getLabels(), BOUND_MS);
    expect(reached(outcome, keys, sinks)).toEqual(REACHED);
  });

  test("ProviderAPIKeyClient: get reaches the host directly with the keys", async () => {
    const sinks = await setUp(API_KEYS_REPLY);
    const keys = [marker("pkk"), marker("pks")];
    const client = providerClient(keys[0], keys[1], sinks.baseUrl);
    const outcome = await settleWithin(client.get(), BOUND_MS);
    expect(reached(outcome, keys, sinks)).toEqual(REACHED);
  });

  test("APIKeyManager: listProviderApiKeys reaches the host directly with the keys of the environment", async () => {
    const sinks = await setUp(API_KEYS_REPLY);
    const keys = [marker("mgk"), marker("mgs")];
    const manager = managerFromEnv(keys[0], keys[1], sinks.baseUrl);
    const outcome = await settleWithin(manager.listProviderApiKeys(), BOUND_MS);
    expect(reached(outcome, keys, sinks)).toEqual(REACHED);
  });
});
