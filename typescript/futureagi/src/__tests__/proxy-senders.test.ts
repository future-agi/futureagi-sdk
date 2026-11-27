// Every axios-based sender of the SDK under a proxy named in the environment, and two cases of the CONNECT tunnel.
//
// Census: each class built on HttpClient or APIKeyAuth sends one keyed request to an https target whose name a lookup
// shim resolves to the loopback address, with HTTPS_PROXY naming a loopback proxy by the same shim name. The proxy is
// expected to hold no key bytes and no request in absolute form; whether the request reached the target through a
// CONNECT tunnel is recorded per sender.
//
// Tunnel cases: an https target addressed by an IP literal whose certificate names only the proxy host (the keyed
// request is expected to fail on the certificate), and a proxy that accepts the TCP connection and does not answer the
// CONNECT request (the keyed request is expected to settle with an error within a bound).

/* eslint-disable @typescript-eslint/no-explicit-any */
import { spawnSync } from "node:child_process";
import { randomBytes } from "node:crypto";
import * as fs from "node:fs";
import * as net from "node:net";
import * as os from "node:os";
import * as path from "node:path";
import * as nodeTls from "node:tls";

import { APIKeyAuth, HttpClient } from "../api/auth";
import { APIKeyManager, ModelProvider, ProviderAPIKeyClient } from "../api/apikeys";
import { Annotation } from "../annotations/annotation";
import { Dataset } from "../datasets/dataset";
import { KnowledgeBase } from "../kb/client";
import { Client } from "../platform/client";
import { Prompt } from "../prompt/client";
import { AnnotationQueue } from "../queues/client";

/** node:tls with the CA functions of Node 22.19+ and 24.5+ (the installed @types/node does not declare them). */
const tls = nodeTls as typeof nodeTls & {
  getCACertificates(kind?: string): string[];
  setDefaultCACertificates(certificates: string[]): void;
};

// eslint-disable-next-line @typescript-eslint/no-var-requires
const fx = require("./support/proxy-sinks.cjs");

jest.setTimeout(30_000);

const SHIM_HOST: string = fx.SHIM_HOST;

const ENV_NAMES = [
  "HTTP_PROXY",
  "http_proxy",
  "HTTPS_PROXY",
  "https_proxy",
  "ALL_PROXY",
  "all_proxy",
  "NO_PROXY",
  "no_proxy",
  "npm_config_https_proxy",
  "npm_config_http_proxy",
  "npm_config_proxy",
  "npm_config_no_proxy",
  "FI_ALLOW_INSECURE_HTTP",
  "FI_API_KEY",
  "FI_SECRET_KEY",
  "FI_BASE_URL",
];

/** Run `run` with every variable of ENV_NAMES cleared except `vars`, then restore the environment. */
async function withEnv<T>(vars: Record<string, string>, run: () => Promise<T>): Promise<T> {
  const saved = new Map(ENV_NAMES.map((name) => [name, process.env[name]]));
  for (const name of ENV_NAMES) delete process.env[name];
  Object.assign(process.env, vars);
  try {
    return await run();
  } finally {
    for (const [name, value] of saved) {
      if (value === undefined) delete process.env[name];
      else process.env[name] = value;
    }
  }
}

const marker = (tag: string) => `fitest_${tag}_${randomBytes(8).toString("hex")}`;

const clock = () => {
  const [seconds, nanos] = process.hrtime();
  return Math.round(seconds * 1000 + nanos / 1e6);
};

type Settled = { settled: false; ms: number } | { settled: true; ms: number; ok: true; value: any } | { settled: true; ms: number; ok: false; error: any };

/** Race `promise` against `ms`: `{settled: false}` when the bound passes first. The promise's rejection is handled. */
function settleWithin(promise: Promise<any>, ms: number): Promise<Settled> {
  const started = clock();
  return new Promise<Settled>((resolve) => {
    const timer = setTimeout(() => resolve({ settled: false, ms: clock() - started }), ms);
    promise.then(
      (value) => {
        clearTimeout(timer);
        resolve({ settled: true, ms: clock() - started, ok: true, value });
      },
      (error) => {
        clearTimeout(timer);
        resolve({ settled: true, ms: clock() - started, ok: false, error });
      },
    );
  });
}

/** Error code and message of an error and its causes, for the record. */
function describeError(error: any): { codes: string[]; text: string } {
  const codes: string[] = [];
  const texts: string[] = [];
  const seen = new Set<any>();
  for (let current = error; current && typeof current === "object" && !seen.has(current); current = current.cause) {
    seen.add(current);
    if (current.code !== undefined) codes.push(String(current.code));
    if (current.message) texts.push(String(current.message));
  }
  return { codes, text: texts.join(" | ") };
}

let undoLookup: () => void;
let caBefore: string[];
beforeAll(() => {
  fx.certificates();
  caBefore = tls.getCACertificates("default");
  undoLookup = fx.shimLookup();
});
afterAll(() => {
  undoLookup();
  tls.setDefaultCACertificates(caBefore);
});

const closers: Array<() => Promise<void> | void> = [];
afterEach(async () => {
  while (closers.length > 0) {
    const close = closers.pop()!;
    await close();
  }
});

// --- census of senders ----------------------------------------------------------------------------------------

/** A sender: one keyed call against `base` with the keys given; the client made is returned through `made`. */
interface Sender {
  name: string;
  call(base: string, apiKey: string, secretKey: string, made: Array<{ close(): Promise<void> }>): Promise<any>;
}

const OPTIONS = { retryAttempts: 1, timeout: 5000 };

/** One attempt and a 5 s timeout for a client whose constructor does not take them. */
function tuned<T extends HttpClient>(client: T, made: Array<{ close(): Promise<void> }>): T {
  (client as any)._defaultRetryAttempts = 1;
  (client as any)._defaultTimeout = 5000;
  made.push(client);
  return client;
}

const SENDERS: Sender[] = [
  {
    name: "HttpClient.request with key headers",
    call: (base, apiKey, secretKey, made) => {
      const client = tuned(new HttpClient({ baseUrl: base, ...OPTIONS }), made);
      return client.request({ method: "GET", url: "/v1/probe", headers: { "X-Api-Key": apiKey, "X-Secret-Key": secretKey } } as any);
    },
  },
  {
    name: "APIKeyAuth.request",
    call: (base, apiKey, secretKey, made) => {
      const client = tuned(new APIKeyAuth({ fiApiKey: apiKey, fiSecretKey: secretKey, baseUrl: base, ...OPTIONS }), made);
      return client.request({ method: "GET", url: "/v1/probe" } as any);
    },
  },
  {
    name: "Dataset.getDatasetConfig",
    call: (base, apiKey, secretKey) => Dataset.getDatasetConfig("probe", { fiApiKey: apiKey, fiSecretKey: secretKey, fiBaseUrl: base, ...OPTIONS }),
  },
  {
    name: "kb client listKbs",
    call: (base, apiKey, secretKey, made) => {
      const client = tuned(new KnowledgeBase(undefined, { fiApiKey: apiKey, fiSecretKey: secretKey, fiBaseUrl: base, timeout: 5000 }), made);
      return client.listKbs();
    },
  },
  {
    name: "Annotation.listProjects",
    call: (base, apiKey, secretKey, made) => {
      const client = tuned(new Annotation({ fiApiKey: apiKey, fiSecretKey: secretKey, fiBaseUrl: base, timeout: 5000 }), made);
      return client.listProjects();
    },
  },
  {
    name: "AnnotationQueue.list",
    call: (base, apiKey, secretKey, made) => {
      const client = tuned(new AnnotationQueue({ fiApiKey: apiKey, fiSecretKey: secretKey, fiBaseUrl: base, ...OPTIONS }), made);
      return client.list();
    },
  },
  {
    name: "AnnotationQueue.listLabels",
    call: (base, apiKey, secretKey, made) => {
      const client = tuned(new AnnotationQueue({ fiApiKey: apiKey, fiSecretKey: secretKey, fiBaseUrl: base, ...OPTIONS }), made);
      return client.listLabels();
    },
  },
  {
    name: "Prompt.delete",
    call: (base, apiKey, secretKey, made) => {
      const client = tuned(new Prompt({ id: "tpl-probe", name: "probe" } as any, { fiApiKey: apiKey, fiSecretKey: secretKey, fiBaseUrl: base, ...OPTIONS }), made);
      return client.delete();
    },
  },
  {
    name: "Prompt.labels().list",
    call: (base, apiKey, secretKey, made) => {
      const client = tuned(new Prompt({ id: "tpl-probe", name: "probe" } as any, { fiApiKey: apiKey, fiSecretKey: secretKey, fiBaseUrl: base, ...OPTIONS }), made);
      return client.labels().list();
    },
  },
  {
    name: "Prompt.getTemplateLabels",
    call: (base, apiKey, secretKey) => Prompt.getTemplateLabels({ template_name: "probe", fiApiKey: apiKey, fiSecretKey: secretKey, fiBaseUrl: base, ...OPTIONS }),
  },
  {
    name: "Prompt.listTemplates",
    call: (base, apiKey, secretKey) => Prompt.listTemplates({ fiApiKey: apiKey, fiSecretKey: secretKey, fiBaseUrl: base, ...OPTIONS }),
  },
  {
    name: "ProviderAPIKeyClient.get",
    call: (base, apiKey, secretKey, made) => {
      const client = tuned(new ProviderAPIKeyClient({ provider: ModelProvider.OPENAI } as any, apiKey, secretKey, base), made);
      return client.get();
    },
  },
  {
    name: "APIKeyManager.request",
    call: async (base, apiKey, secretKey, made) => {
      // The manager reads its keys and base URL from the environment and is a singleton: a new one per call here.
      (APIKeyManager as any)._instance = undefined;
      Object.assign(process.env, { FI_API_KEY: apiKey, FI_SECRET_KEY: secretKey, FI_BASE_URL: base });
      const manager = tuned(APIKeyManager.getInstance(), made);
      (APIKeyManager as any)._instance = undefined;
      return manager.request({ method: "GET", url: manager.url } as any);
    },
  },
];

const census: Record<string, any> = {};

describe("keyed requests of every axios-based sender with HTTPS_PROXY set", () => {
  afterAll(() => {
    // eslint-disable-next-line no-console
    console.log(`sender census: ${JSON.stringify(census, null, 1)}`);
  });

  test.each(SENDERS.map((sender) => [sender.name, sender] as const))("%s sends no key bytes and no absolute-form request to the proxy", async (_name, sender) => {
    const target = await fx.tlsTarget();
    closers.push(() => target.close());
    const proxy = await fx.proxySink();
    closers.push(() => proxy.close());
    const apiKey = marker("api");
    const secretKey = marker("secret");
    const base = `https://${SHIM_HOST}:${target.port}`;
    const made: Array<{ close(): Promise<void> }> = [];
    const outcome = await withEnv({ HTTPS_PROXY: `http://${SHIM_HOST}:${proxy.port}` }, () =>
      settleWithin(
        sender.call(base, apiKey, secretKey, made),
        10_000,
      ),
    );
    for (const client of made) await client.close();
    const record = {
      settled: outcome.settled,
      ms: outcome.ms,
      outcome: !outcome.settled ? "pending" : outcome.ok ? "resolved" : `rejected: ${describeError(outcome.error).text.slice(0, 120)}`,
      proxyKeyBytes: proxy.count([apiKey, secretKey]),
      absolute: proxy.absolute.length,
      connects: proxy.connects.length,
      targetKeyBytes: target.count([apiKey, secretKey]),
      reachedTargetThroughConnect: proxy.connects.length > 0 && target.count([apiKey, secretKey]) > 0,
    };
    census[sender.name] = record;
    expect({ settled: record.settled, proxyKeyBytes: record.proxyKeyBytes, absolute: record.absolute }).toEqual({ settled: true, proxyKeyBytes: 0, absolute: 0 });
  });
});

// --- an IP-literal target with a certificate for the proxy name -----------------------------------------------

interface IpTarget {
  port: number;
  count(markers: string[]): number;
  close(): Promise<void>;
}

let ipCert: { key: string; cert: string } | undefined;

/** A CA and a server certificate whose only subjectAltName is DNS:SHIM_HOST, the CA trusted by this process. */
function proxyNameCertificate(): { key: string; cert: string } {
  if (ipCert) return ipCert;
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "fi-ip-tls-"));
  try {
    const run = (args: string[]) => {
      const out = spawnSync("openssl", args, { cwd: dir, encoding: "utf8" });
      if (out.status !== 0) throw new Error(`openssl ${args[0]} failed: ${out.stderr}`);
    };
    fs.writeFileSync(path.join(dir, "ext.cnf"), `subjectAltName=DNS:${SHIM_HOST}\nbasicConstraints=CA:FALSE\n`);
    run(["req", "-x509", "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:prime256v1", "-nodes", "-keyout", "ca.key", "-out", "ca.pem", "-days", "2", "-subj", "/CN=fi-ip-test-ca"]);
    run(["req", "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:prime256v1", "-nodes", "-keyout", "server.key", "-out", "server.csr", "-subj", `/CN=${SHIM_HOST}`]);
    run(["x509", "-req", "-in", "server.csr", "-CA", "ca.pem", "-CAkey", "ca.key", "-CAcreateserial", "-out", "server.pem", "-days", "2", "-extfile", "ext.cnf"]);
    const ca = fs.readFileSync(path.join(dir, "ca.pem"), "utf8");
    ipCert = { key: fs.readFileSync(path.join(dir, "server.key"), "utf8"), cert: fs.readFileSync(path.join(dir, "server.pem"), "utf8") };
    tls.setDefaultCACertificates([...tls.getCACertificates("default"), ca]);
    return ipCert;
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

/** An https listener on 127.0.0.1 with the certificate above; records the bytes received after TLS. */
async function ipTarget(): Promise<IpTarget> {
  const { key, cert } = proxyNameCertificate();
  const chunks: string[] = [];
  const sockets = new Set<net.Socket>();
  const body = JSON.stringify({ status: true, result: {} });
  const server = tls.createServer({ key, cert }, (socket) => {
    sockets.add(socket);
    socket.on("close", () => sockets.delete(socket));
    socket.on("error", () => undefined);
    let head = "";
    socket.on("data", (data) => {
      chunks.push(data.toString("latin1"));
      head += data.toString("latin1");
      if (head.includes("\r\n\r\n")) {
        head = "";
        socket.end(`HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: ${body.length}\r\nConnection: close\r\n\r\n${body}`);
      }
    });
  });
  server.on("tlsClientError", () => undefined);
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const port = (server.address() as net.AddressInfo).port;
  return {
    port,
    count: (markers) => {
      const all = chunks.join("");
      return markers.reduce((total, item) => total + (all.split(item).length - 1) * item.length, 0);
    },
    close: () =>
      new Promise<void>((resolve) => {
        for (const socket of sockets) socket.destroy();
        server.close(() => resolve());
      }),
  };
}

const CERT_ERROR = /ERR_TLS_CERT_ALTNAME_INVALID|altname|certificate/i;

describe("an https target addressed by IP whose certificate names only the proxy host", () => {
  test("a keyed HttpClient request through that proxy fails on the certificate", async () => {
    const target = await ipTarget();
    closers.push(() => target.close());
    const proxy = await fx.proxySink();
    closers.push(() => proxy.close());
    const apiKey = marker("api");
    const secretKey = marker("secret");
    const client = new APIKeyAuth({ fiApiKey: apiKey, fiSecretKey: secretKey, baseUrl: `https://127.0.0.1:${target.port}`, ...OPTIONS });
    closers.unshift(() => settleWithin(client.close(), 3000).then(() => undefined));
    const outcome = await withEnv({ HTTPS_PROXY: `http://${SHIM_HOST}:${proxy.port}` }, () =>
      // The client's own axios instance, so the error code of the TLS failure is kept.
      settleWithin((client as any)._axiosInstance.get("/v1/probe"), 8000),
    );
    const error = outcome.settled && !outcome.ok ? describeError(outcome.error) : undefined;
    const record = {
      settled: outcome.settled,
      result: !outcome.settled ? "pending" : outcome.ok ? `resolved ${(outcome.value as any)?.status}` : "rejected",
      certificateError: error !== undefined && (error.codes.some((code) => CERT_ERROR.test(code)) || CERT_ERROR.test(error.text)),
      connects: proxy.connects.length,
      targetKeyBytes: target.count([apiKey, secretKey]),
      proxyKeyBytes: proxy.count([apiKey, secretKey]),
    };
    // eslint-disable-next-line no-console
    console.log(`IP target, HttpClient: ${JSON.stringify({ ...record, ms: outcome.ms, error })}`);
    expect(record).toEqual({ settled: true, result: "rejected", certificateError: true, connects: 1, targetKeyBytes: 0, proxyKeyBytes: 0 });
  });

  test("a keyed platform Client request through that proxy fails on the certificate", async () => {
    const target = await ipTarget();
    closers.push(() => target.close());
    const proxy = await fx.proxySink();
    closers.push(() => proxy.close());
    const apiKey = marker("api");
    const secretKey = marker("secret");
    const outcome = await withEnv({ HTTPS_PROXY: `http://${SHIM_HOST}:${proxy.port}` }, () => {
      const client = new Client({ apiKey, secretKey, baseUrl: `https://127.0.0.1:${target.port}`, timeout: 5000, maxRetries: 0 });
      return settleWithin(client.request("GET", "/v1/probe/", { unwrap: null }), 8000);
    });
    const error = outcome.settled && !outcome.ok ? describeError(outcome.error) : undefined;
    const record = {
      settled: outcome.settled,
      result: !outcome.settled ? "pending" : outcome.ok ? "resolved" : "rejected",
      certificateError: error !== undefined && (error.codes.some((code) => CERT_ERROR.test(code)) || CERT_ERROR.test(error.text)),
      connects: proxy.connects.length,
      targetKeyBytes: target.count([apiKey, secretKey]),
      proxyKeyBytes: proxy.count([apiKey, secretKey]),
    };
    // eslint-disable-next-line no-console
    console.log(`IP target, platform Client: ${JSON.stringify({ ...record, ms: outcome.ms, error })}`);
    expect(record).toEqual({ settled: true, result: "rejected", certificateError: true, connects: 1, targetKeyBytes: 0, proxyKeyBytes: 0 });
  });
});

// --- a proxy that accepts TCP and does not answer CONNECT ------------------------------------------------------

interface SilentProxy {
  port: number;
  connections: number;
  bytes(): string;
  close(): Promise<void>;
}

/** A TCP listener that accepts connections, records what it receives and sends nothing back. */
async function silentProxy(): Promise<SilentProxy> {
  const chunks: string[] = [];
  const sockets = new Set<net.Socket>();
  const state = { connections: 0 };
  const server = net.createServer((socket) => {
    state.connections++;
    sockets.add(socket);
    socket.on("close", () => sockets.delete(socket));
    socket.on("error", () => undefined);
    socket.on("data", (data) => chunks.push(data.toString("latin1")));
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  return {
    port: (server.address() as net.AddressInfo).port,
    get connections() {
      return state.connections;
    },
    bytes: () => chunks.join(""),
    close: () =>
      new Promise<void>((resolve) => {
        for (const socket of sockets) socket.destroy();
        server.close(() => resolve());
      }),
  };
}

const BOUND_MS = 4000;

describe("a proxy that accepts the connection and does not answer CONNECT", () => {
  test("a keyed HttpClient request with timeout 1500 settles with an error within 4 s", async () => {
    const apiKey = marker("api");
    const secretKey = marker("secret");
    const client = new APIKeyAuth({ fiApiKey: apiKey, fiSecretKey: secretKey, baseUrl: `https://${SHIM_HOST}:9443`, retryAttempts: 1, timeout: 1500 });
    // Closed after the proxy (closers run last-in first-out): the client waits for its pending request to end.
    closers.push(() => settleWithin(client.close(), 3000).then(() => undefined));
    const proxy = await silentProxy();
    closers.push(() => proxy.close());
    const outcome = await withEnv({ HTTPS_PROXY: `http://${SHIM_HOST}:${proxy.port}` }, () =>
      settleWithin(client.request({ method: "GET", url: "/v1/probe" } as any), BOUND_MS),
    );
    const sent = proxy.bytes();
    const record = {
      settled: outcome.settled,
      rejected: outcome.settled && !outcome.ok,
      connectSent: sent.startsWith(`CONNECT ${SHIM_HOST}:9443 `),
      proxyKeyBytes: [apiKey, secretKey].filter((item) => sent.includes(item)).length,
    };
    // eslint-disable-next-line no-console
    console.log(`silent proxy, HttpClient: ${JSON.stringify({ ...record, ms: outcome.ms, connections: proxy.connections, error: outcome.settled && !outcome.ok ? describeError(outcome.error) : undefined })}`);
    expect(record).toEqual({ settled: true, rejected: true, connectSent: true, proxyKeyBytes: 0 });
  });

  test("a keyed platform Client request with timeout 1500 and maxRetries 0 settles within 4 s", async () => {
    const proxy = await silentProxy();
    closers.push(() => proxy.close());
    const apiKey = marker("api");
    const secretKey = marker("secret");
    const outcome = await withEnv({ HTTPS_PROXY: `http://${SHIM_HOST}:${proxy.port}` }, () => {
      const client = new Client({ apiKey, secretKey, baseUrl: `https://${SHIM_HOST}:9443`, timeout: 1500, maxRetries: 0 });
      return settleWithin(client.request("GET", "/v1/probe/", { unwrap: null }), BOUND_MS);
    });
    const sent = proxy.bytes();
    const record = {
      settled: outcome.settled,
      rejected: outcome.settled && !outcome.ok,
      connectSent: sent.startsWith(`CONNECT ${SHIM_HOST}:9443 `),
      proxyKeyBytes: [apiKey, secretKey].filter((item) => sent.includes(item)).length,
    };
    // eslint-disable-next-line no-console
    console.log(`silent proxy, platform Client: ${JSON.stringify({ ...record, ms: outcome.ms, connections: proxy.connections, error: outcome.settled && !outcome.ok ? describeError(outcome.error) : undefined })}`);
    expect(record).toEqual({ settled: true, rejected: true, connectSent: true, proxyKeyBytes: 0 });
  });
});
