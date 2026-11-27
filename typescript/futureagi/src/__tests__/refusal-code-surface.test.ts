// How KnowledgeBase and APIKeyManager surface a refused keyed request.
//
// A keyed request to a plain-http host that is not loopback, without the opt-in, is refused with code
// insecure_http_origin before any connection is made. Every public entry point of KnowledgeBase, and
// APIKeyManager.validateRequiredProviders, rejects with an Error whose own `code` is insecure_http_origin (the code is
// on the error the caller receives, not only somewhere in its chain of causes). A KnowledgeBase made with a name
// produces no unhandled rejection when the lookup of that name is refused.
//
// Every listener here is on the loopback address. The host name below resolves to 127.0.0.1 through a lookup shim of
// this file, so a request to it counts as a request to a host that is not loopback while its bytes land in a listener
// of this file. The proxy variables point at a second listener (with no exemptions), which records any request that
// goes through a proxy. Keys are random marker strings made per test, and each test counts their bytes at both
// listeners.

/* eslint-disable @typescript-eslint/no-explicit-any */
import { randomBytes } from "node:crypto";
import * as fs from "node:fs";
import * as net from "node:net";
import * as os from "node:os";
import * as path from "node:path";

import { KnowledgeBase } from "../kb/client";
import { APIKeyManager, getAPIKeyManager } from "../api/apikeys";
import { ModelProvider } from "../api/types";

/** Milliseconds from a monotonic clock. */
const clockMs = (): number => Number(process.hrtime.bigint()) / 1e6;

// eslint-disable-next-line @typescript-eslint/no-var-requires
const dns: typeof import("node:dns") = require("node:dns");

jest.setTimeout(30_000);

const SHIM_HOST = "guard-target.futureagi.com";
const CODE = "insecure_http_origin";
const BOUND_MS = 5_000;
const UNHANDLED_WAIT_MS = 500;

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
  for (const dir of scratchDirs.splice(0)) fs.rmSync(dir, { recursive: true, force: true });
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

const marker = (tag: string) => `fi-marker-${tag}-${randomBytes(8).toString("hex")}`;

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

/** Whether `error` or an error in its chain of causes carries `code`. */
function codeInChain(error: unknown, code: string): boolean {
  const seen = new Set<unknown>();
  for (let current = error; typeof current === "object" && current !== null && !seen.has(current); current = (current as { cause?: unknown }).cause) {
    seen.add(current);
    if ((current as { code?: unknown }).code === code) return true;
  }
  return false;
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
  "npm_config_proxy",
  "npm_config_http_proxy",
  "npm_config_https_proxy",
  "npm_config_no_proxy",
  "FI_ALLOW_INSECURE_HTTP",
  "FI_API_KEY",
  "FI_SECRET_KEY",
  "FI_BASE_URL",
];

let savedEnv: Map<string, string | undefined>;
let target: Sink | undefined;
let proxy: Sink | undefined;
let scratchDir: string | undefined;
/** Scratch directories, removed after the last test: a file stream the SDK opened for a refused request may open its file
 * after its test ends. */
const scratchDirs: string[] = [];
const closers: Array<() => Promise<void> | void> = [];

/** The listeners for one test, with the proxy variables set to the proxy listener and no exemptions. The opt-in
 * variable is not set. */
async function setUp(body: string): Promise<{ target: Sink; proxy: Sink; baseUrl: string }> {
  target = await sink(body);
  proxy = await sink(JSON.stringify({}));
  const proxyUrl = `http://127.0.0.1:${proxy.port}`;
  for (const name of ["HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy"]) process.env[name] = proxyUrl;
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
  jest.restoreAllMocks();
  const manager = (APIKeyManager as any)._instance as { close?: () => Promise<void> } | undefined;
  resetManager();
  if (manager && typeof manager.close === "function") await manager.close();
  for (const close of closers.splice(0)) await close();
  if (target) await target.close();
  if (proxy) await proxy.close();
  target = undefined;
  proxy = undefined;
  if (scratchDir) scratchDirs.push(scratchDir);
  scratchDir = undefined;
  for (const [name, value] of savedEnv) {
    if (value === undefined) delete process.env[name];
    else process.env[name] = value;
  }
});

/** The outcome of a call as the caller and the listeners saw it, for a call that is expected to be refused. */
function observed(outcome: Outcome, keys: string[], sinks: { target: Sink; proxy: Sink }) {
  const error = outcome.settled && outcome.rejected ? outcome.error : undefined;
  const summary = {
    settled: outcome.settled,
    rejected: outcome.settled && outcome.rejected,
    isError: error instanceof Error,
    topLevelCode: (error as { code?: unknown } | undefined)?.code,
    targetConnections: sinks.target.connections,
    targetKeyBytes: sinks.target.count(keys),
    proxyConnections: sinks.proxy.connections,
    proxyKeyBytes: sinks.proxy.count(keys),
    elapsedMs: outcome.elapsedMs,
    errorText: error instanceof Error ? `${error.name}: ${error.message}` : undefined,
    codeInChain: codeInChain(error, CODE),
  };
  if (process.env.FI_TEST_TRACE) console.log(JSON.stringify(summary));
  return summary;
}

const REFUSED = {
  settled: true,
  rejected: true,
  isError: true,
  topLevelCode: CODE,
  targetConnections: 0,
  targetKeyBytes: 0,
  proxyConnections: 0,
  proxyKeyBytes: 0,
  elapsedMs: expect.any(Number),
  errorText: expect.any(String),
  codeInChain: true,
};

const KB_REPLY = JSON.stringify({ status: true, result: { table_data: [{ id: "kb-1", name: "docs", status: "ok", files: [] }] } });
const API_KEYS_REPLY = JSON.stringify({ results: [] });

// --- the clients ----------------------------------------------------------------------------------------------

function knowledgeBase(keys: string[], baseUrl: string, kbName?: string): KnowledgeBase {
  const client = new KnowledgeBase(kbName, { fiApiKey: keys[0], fiSecretKey: keys[1], fiBaseUrl: baseUrl, timeout: 3_000 });
  closers.push(() => client.close());
  return client;
}

/** A KnowledgeBase whose cached `kb` names `name`, so the call goes straight to its own request. */
function knowledgeBaseWithCachedKb(keys: string[], baseUrl: string, name: string): KnowledgeBase {
  const client = knowledgeBase(keys, baseUrl);
  client.kb = { id: "kb-cached-1", name, files: [] } as any;
  return client;
}

function scratchFile(name: string, text: string): string {
  scratchDir = scratchDir ?? fs.mkdtempSync(path.join(os.tmpdir(), "fi-kb-refusal-"));
  const file = path.join(scratchDir, name);
  fs.writeFileSync(file, text);
  return file;
}

function managerEnv(keys: string[], baseUrl: string): void {
  process.env.FI_API_KEY = keys[0];
  process.env.FI_SECRET_KEY = keys[1];
  process.env.FI_BASE_URL = baseUrl;
}

const warnSpy = () => jest.spyOn(console, "warn").mockImplementation(() => undefined);

// --- KnowledgeBase --------------------------------------------------------------------------------------------

describe("KnowledgeBase rejects a refused keyed request to a plain-http host that is not loopback with an Error whose own code is insecure_http_origin", () => {
  test("listKbs without a search text", async () => {
    const sinks = await setUp(KB_REPLY);
    const keys = [marker("kbk"), marker("kbs")];
    const outcome = await settleWithin(knowledgeBase(keys, sinks.baseUrl).listKbs(), BOUND_MS);
    expect(observed(outcome, keys, sinks)).toEqual(REFUSED);
  });

  test("listKbs with a search text", async () => {
    const sinks = await setUp(KB_REPLY);
    const keys = [marker("kbk"), marker("kbs")];
    const outcome = await settleWithin(knowledgeBase(keys, sinks.baseUrl).listKbs("docs"), BOUND_MS);
    expect(observed(outcome, keys, sinks)).toEqual(REFUSED);
  });

  test("createKb with a file", async () => {
    const sinks = await setUp(KB_REPLY);
    const keys = [marker("kbk"), marker("kbs")];
    const file = scratchFile("notes.txt", "some notes for the knowledge base\n");
    const outcome = await settleWithin(knowledgeBase(keys, sinks.baseUrl).createKb("docs", [file]), BOUND_MS);
    expect(observed(outcome, keys, sinks)).toEqual(REFUSED);
  });

  test("createKb with a name and no files", async () => {
    const sinks = await setUp(KB_REPLY);
    const keys = [marker("kbk"), marker("kbs")];
    const outcome = await settleWithin(knowledgeBase(keys, sinks.baseUrl).createKb("docs"), BOUND_MS);
    expect(observed(outcome, keys, sinks)).toEqual(REFUSED);
  });

  test("updateKb that looks up the knowledge base by its name", async () => {
    const sinks = await setUp(KB_REPLY);
    const keys = [marker("kbk"), marker("kbs")];
    const outcome = await settleWithin(knowledgeBase(keys, sinks.baseUrl).updateKb({ kbName: "docs", newName: "docs-2" }), BOUND_MS);
    expect(observed(outcome, keys, sinks)).toEqual(REFUSED);
  });

  test("updateKb with a file on a client that holds the knowledge base", async () => {
    const sinks = await setUp(KB_REPLY);
    const keys = [marker("kbk"), marker("kbs")];
    const file = scratchFile("more.txt", "more notes\n");
    const client = knowledgeBaseWithCachedKb(keys, sinks.baseUrl, "docs");
    const outcome = await settleWithin(client.updateKb({ kbName: "docs", filePaths: [file] }), BOUND_MS);
    expect(observed(outcome, keys, sinks)).toEqual(REFUSED);
  });

  test("deleteFilesFromKb that looks up the knowledge base by its name", async () => {
    const sinks = await setUp(KB_REPLY);
    const keys = [marker("kbk"), marker("kbs")];
    const outcome = await settleWithin(knowledgeBase(keys, sinks.baseUrl).deleteFilesFromKb({ kbName: "docs", fileNames: ["notes.txt"] }), BOUND_MS);
    expect(observed(outcome, keys, sinks)).toEqual(REFUSED);
  });

  test("deleteFilesFromKb on a client that holds the knowledge base", async () => {
    const sinks = await setUp(KB_REPLY);
    const keys = [marker("kbk"), marker("kbs")];
    const client = knowledgeBaseWithCachedKb(keys, sinks.baseUrl, "docs");
    const outcome = await settleWithin(client.deleteFilesFromKb({ kbName: "docs", fileNames: ["notes.txt"] }), BOUND_MS);
    expect(observed(outcome, keys, sinks)).toEqual(REFUSED);
  });

  test("deleteKb by ids", async () => {
    const sinks = await setUp(KB_REPLY);
    const keys = [marker("kbk"), marker("kbs")];
    const outcome = await settleWithin(knowledgeBase(keys, sinks.baseUrl).deleteKb({ kbIds: ["kb-1"] }), BOUND_MS);
    expect(observed(outcome, keys, sinks)).toEqual(REFUSED);
  });

  test("deleteKb by names (the refused lookup of a name is not taken as a name that was not found)", async () => {
    const sinks = await setUp(KB_REPLY);
    const keys = [marker("kbk"), marker("kbs")];
    const outcome = await settleWithin(knowledgeBase(keys, sinks.baseUrl).deleteKb({ kbNames: ["docs", "other"] }), BOUND_MS);
    expect(observed(outcome, keys, sinks)).toEqual(REFUSED);
  });

  test("deleteKb with no arguments on a client that holds the knowledge base", async () => {
    const sinks = await setUp(KB_REPLY);
    const keys = [marker("kbk"), marker("kbs")];
    const client = knowledgeBaseWithCachedKb(keys, sinks.baseUrl, "docs");
    const outcome = await settleWithin(client.deleteKb(), BOUND_MS);
    expect(observed(outcome, keys, sinks)).toEqual(REFUSED);
  });
});

describe("a KnowledgeBase made with a name whose lookup is refused", () => {
  let unhandled: unknown[];
  const onUnhandled = (reason: unknown) => {
    unhandled.push(reason);
  };

  beforeEach(() => {
    unhandled = [];
    process.on("unhandledRejection", onUnhandled);
  });

  afterEach(() => {
    process.removeListener("unhandledRejection", onUnhandled);
  });

  test("produces no unhandled rejection, sends no key, and a later call on the client rejects with code insecure_http_origin", async () => {
    const sinks = await setUp(KB_REPLY);
    const keys = [marker("kbk"), marker("kbs")];
    const client = knowledgeBase(keys, sinks.baseUrl, "docs");
    await new Promise((resolve) => setTimeout(resolve, UNHANDLED_WAIT_MS));
    const afterConstruction = {
      unhandledRejections: unhandled.length,
      unhandledText: unhandled.map((reason) => (reason instanceof Error ? `${reason.name}: ${reason.message}` : String(reason))),
      targetKeyBytes: sinks.target.count(keys),
      proxyKeyBytes: sinks.proxy.count(keys),
    };
    if (process.env.FI_TEST_TRACE) console.log(JSON.stringify(afterConstruction));
    expect(afterConstruction).toEqual({ unhandledRejections: 0, unhandledText: [], targetKeyBytes: 0, proxyKeyBytes: 0 });

    const outcome = await settleWithin(client.listKbs(), BOUND_MS);
    expect(observed(outcome, keys, sinks)).toEqual(REFUSED);
    expect(unhandled).toEqual([]);
  });
});

// --- APIKeyManager --------------------------------------------------------------------------------------------

describe("APIKeyManager rejects a refused keyed request to a plain-http host that is not loopback with an Error whose own code is insecure_http_origin", () => {
  test("validateRequiredProviders with one provider, on the instance of APIKeyManager.getInstance", async () => {
    const sinks = await setUp(API_KEYS_REPLY);
    const keys = [marker("mgk"), marker("mgs")];
    managerEnv(keys, sinks.baseUrl);
    warnSpy();
    const manager = APIKeyManager.getInstance();
    const outcome = await settleWithin(manager.validateRequiredProviders([ModelProvider.OPENAI]), BOUND_MS);
    expect(observed(outcome, keys, sinks)).toEqual(REFUSED);
  });

  test("validateRequiredProviders with two providers, on the instance of getAPIKeyManager", async () => {
    const sinks = await setUp(API_KEYS_REPLY);
    const keys = [marker("mgk"), marker("mgs")];
    managerEnv(keys, sinks.baseUrl);
    warnSpy();
    const manager = getAPIKeyManager();
    const outcome = await settleWithin(manager.validateRequiredProviders([ModelProvider.OPENAI, ModelProvider.ANTHROPIC]), BOUND_MS);
    expect(observed(outcome, keys, sinks)).toEqual(REFUSED);
  });

  test("isProviderConfigured passes the refusal on to the caller", async () => {
    const sinks = await setUp(API_KEYS_REPLY);
    const keys = [marker("mgk"), marker("mgs")];
    managerEnv(keys, sinks.baseUrl);
    warnSpy();
    const manager = APIKeyManager.getInstance();
    const outcome = await settleWithin(manager.isProviderConfigured(ModelProvider.OPENAI), BOUND_MS);
    expect(observed(outcome, keys, sinks)).toEqual(REFUSED);
  });
});
