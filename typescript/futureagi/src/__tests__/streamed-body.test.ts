// Streamed request bodies sent by HttpClient and Dataset.
//
// A POST body that is a Node stream (a form-data object over fs.createReadStream of a temporary file, or a plain
// Readable) is read by the client so that a 307 or 308 hop can send it again. These cases cover how such a request
// settles: after a server error with retries left, when the source fails, stalls, is aborted or was read before the
// call, and when the body is larger than an explicit maxBodyLength or than the copy kept for a resend.
//
// Every sink is a loopback plain-http listener (http://127.0.0.1:port, where a keyed request is sent directly). Each
// settling check races the request against an explicit bound (settleWithin), so a request that does not settle shows
// as { settled: false } in the assertion. Cases that read an error code or a body limit go through the client's
// axios instance (the client's adapter, without the retry loop of HttpClient.request).

/* eslint-disable @typescript-eslint/no-explicit-any */
import { randomBytes } from "node:crypto";
import * as fs from "node:fs";
import * as http from "node:http";
import type * as net from "node:net";
import * as os from "node:os";
import * as path from "node:path";
import { Readable } from "node:stream";

import { HttpClient } from "../api/auth";
import { Dataset } from "../datasets/dataset";
import { ModelTypes } from "../datasets/types";

// eslint-disable-next-line @typescript-eslint/no-var-requires
const FormDataStream = require("form-data");

jest.setTimeout(60_000);

const KiB = 1024;
const MiB = 1024 * KiB;

// --- environment ---------------------------------------------------------------------------------------------

const ENV_NAMES = [
  "HTTP_PROXY",
  "HTTPS_PROXY",
  "ALL_PROXY",
  "NO_PROXY",
  "http_proxy",
  "https_proxy",
  "all_proxy",
  "no_proxy",
  "FI_ALLOW_INSECURE_HTTP",
];
let savedEnv = new Map<string, string | undefined>();

// --- per-test resources ----------------------------------------------------------------------------------------

const marker = (tag: string) => `fitest_${tag}_${randomBytes(8).toString("hex")}`;

let scratchDir: string;
const cleanups: Array<() => void | Promise<void>> = [];

/** A stream (or anything with destroy) destroyed after the test. */
function track<T extends { destroy(error?: Error): unknown }>(stream: T): T {
  cleanups.push(() => {
    stream.destroy();
  });
  return stream;
}

/** A timer cleared after the test. */
function later(ms: number, run: () => void): void {
  const timer = setTimeout(run, ms);
  cleanups.push(() => clearTimeout(timer));
}

/** A temporary file of `bytes` bytes: random content with a marker string at its start. */
function scratchFile(name: string, bytes: number): { file: string; content: Buffer; tag: string } {
  const tag = marker("rows");
  const content = Buffer.concat([Buffer.from(`${tag}\n`, "latin1"), randomBytes(Math.max(0, bytes - tag.length - 1))]);
  const file = path.join(scratchDir, `${name}-${randomBytes(4).toString("hex")}.bin`);
  fs.writeFileSync(file, content);
  return { file, content, tag };
}

/** A form-data body over fs.createReadStream of `file`; the file stream is destroyed after the test. */
function formOver(file: string): any {
  const form = new FormDataStream();
  form.append("file", track(fs.createReadStream(file)));
  form.append("name", "rows");
  cleanups.push(() => {
    if (typeof form.destroy === "function") form.destroy();
  });
  return form;
}

beforeAll(() => {
  scratchDir = fs.mkdtempSync(path.join(os.tmpdir(), "fi-streamed-body-"));
});
afterAll(() => {
  fs.rmSync(scratchDir, { recursive: true, force: true });
});

beforeEach(() => {
  savedEnv = new Map(ENV_NAMES.map((name) => [name, process.env[name]]));
  for (const name of ENV_NAMES) delete process.env[name];
});
afterEach(async () => {
  while (cleanups.length > 0) {
    const cleanup = cleanups.pop()!;
    try {
      await cleanup();
    } catch {
      /* continue with the others */
    }
  }
  for (const [name, value] of savedEnv) {
    if (value === undefined) delete process.env[name];
    else process.env[name] = value;
  }
});

// --- loopback sink -----------------------------------------------------------------------------------------------

interface Received {
  method: string;
  path: string;
  body: Buffer;
}

interface Site {
  origin: string;
  requests: Received[];
}

/** A plain-http loopback listener that reads each request body to its end and answers with `answer(method, path)`
 * as [status, headers]. It is closed (every connection with it) after the test. */
async function site(answer: (method: string, requestPath: string) => [number, Record<string, string>]): Promise<Site> {
  const requests: Received[] = [];
  const server = http.createServer((req, res) => {
    const chunks: Buffer[] = [];
    req.on("error", () => undefined);
    res.on("error", () => undefined);
    req.on("data", (chunk: Buffer) => chunks.push(chunk));
    req.on("end", () => {
      requests.push({ method: req.method ?? "", path: req.url ?? "", body: Buffer.concat(chunks) });
      const [status, headers] = answer(req.method ?? "", req.url ?? "");
      const reply =
        status === 200
          ? JSON.stringify({ status: true, result: { dataset_id: "ds-1", dataset_name: "rows", dataset_model_type: "GenerativeLLM" } })
          : JSON.stringify({ message: `status ${status}` });
      res.writeHead(status, { "Content-Type": "application/json", "Content-Length": String(Buffer.byteLength(reply)), Connection: "close", ...headers });
      res.end(reply);
    });
  });
  server.on("clientError", (_error, socket) => socket.destroy());
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  cleanups.push(
    () =>
      new Promise<void>((resolve) => {
        server.closeAllConnections();
        server.close(() => resolve());
      }),
  );
  return { origin: `http://127.0.0.1:${(server.address() as net.AddressInfo).port}`, requests };
}

/** The requests whose body holds `content`. */
const carrying = (requests: Received[], content: Buffer | string) =>
  requests.filter((request) => request.body.indexOf(typeof content === "string" ? Buffer.from(content, "latin1") : content) >= 0);

// --- settling ----------------------------------------------------------------------------------------------------

type Settled = { settled: false; bound: number } | { settled: true; ok: boolean; value?: unknown; error?: any; ms: number };

/** `promise` raced against a bound of `ms`: { settled: false } when the bound passes first. */
async function settleWithin(promise: Promise<unknown>, ms: number): Promise<Settled> {
  const start = process.hrtime();
  const elapsed = () => {
    const [seconds, nanos] = process.hrtime(start);
    return Math.round(seconds * 1000 + nanos / 1e6);
  };
  let timer: NodeJS.Timeout | undefined;
  const bound = new Promise<Settled>((resolve) => {
    timer = setTimeout(() => resolve({ settled: false, bound: ms }), ms);
  });
  const outcome = promise.then(
    (value): Settled => ({ settled: true, ok: true, value, ms: elapsed() }),
    (error): Settled => ({ settled: true, ok: false, error, ms: elapsed() }),
  );
  try {
    return await Promise.race([outcome, bound]);
  } finally {
    clearTimeout(timer);
  }
}

const codeOf = (outcome: Settled) =>
  !outcome.settled ? "(not settled)" : outcome.ok ? "(resolved)" : ((outcome.error as { code?: string } | undefined)?.code ?? "(no code)");

/** Whether the request settled and whether it rejected. */
function ending(outcome: Settled): { settled: boolean; rejected: boolean } {
  return { settled: outcome.settled, rejected: outcome.settled && !outcome.ok };
}

/** Whether the request settled, whether it rejected, and its error code. */
function rejection(outcome: Settled): { settled: boolean; rejected: boolean; code: string } {
  return { ...ending(outcome), code: codeOf(outcome) };
}

// --- senders -----------------------------------------------------------------------------------------------------

type Make = (baseUrl: string, config?: Record<string, unknown>) => HttpClient;

/** The default http adapter, with a key (a keyed loopback request is sent directly by the http adapter). */
const httpAdapterClient: Make = (baseUrl, config = {}) =>
  new HttpClient({ baseUrl, retryAttempts: 1, timeout: 10_000, defaultHeaders: { "X-Api-Key": marker("key") }, ...config } as any);

/** The axios fetch adapter, without a key (a keyed loopback request would go through the http adapter instead). */
const fetchAdapterClient: Make = (baseUrl, config = {}) => {
  const client = new HttpClient({ baseUrl, retryAttempts: 1, timeout: 10_000, ...config } as any);
  (client as any)._axiosInstance.defaults.adapter = "fetch";
  return client;
};

const senders: Array<[string, Make]> = [
  ["default http adapter", httpAdapterClient],
  ["fetch adapter", fetchAdapterClient],
];

/** A request sent by the client's axios instance (its adapter, without the retry loop of HttpClient.request). */
const viaInstance = (client: HttpClient, config: Record<string, unknown>) => (client as any)._axiosInstance.request({ method: "POST", url: "/v1/upload", ...config }) as Promise<unknown>;

// --- sources -----------------------------------------------------------------------------------------------------

/** A Readable that gives one 16 KiB chunk and then fails with `message`. */
function failingSource(message: string): Readable {
  let reads = 0;
  return track(
    new Readable({
      read() {
        reads++;
        if (reads === 1) {
          this.push(Buffer.alloc(16 * KiB, 0x61));
        } else if (reads === 2) {
          later(50, () => this.destroy(new Error(message)));
        }
      },
    }),
  );
}

/** A Readable that gives one 16 KiB chunk and then gives nothing more and does not end. */
function stalledSource(): Readable {
  const source = new Readable({ read() {} });
  source.push(Buffer.alloc(16 * KiB, 0x62));
  return track(source);
}

// --- cases -------------------------------------------------------------------------------------------------------

describe("a streamed form body answered with 500 while retries are left", () => {
  test("Dataset.create with a file path (3 attempts, retryDelay 1000): settles with an error within 10 s and the file content reaches the sink in one request", async () => {
    const sink = await site(() => [500, {}]);
    const { file, tag } = scratchFile("dataset", 64 * KiB);
    const dataset = new Dataset({
      fiApiKey: marker("api"),
      fiSecretKey: marker("secret"),
      fiBaseUrl: sink.origin,
      datasetConfig: { name: "rows", model_type: ModelTypes.GENERATIVE_LLM },
    });
    const outcome = await settleWithin(dataset.create(file), 10_000);
    expect({
      ...ending(outcome),
      requestsWithContent: carrying(sink.requests, tag).length,
    }).toEqual({ settled: true, rejected: true, requestsWithContent: 1 });
  });

  test.each(senders.map(([name]) => [name]))(
    "HttpClient.request (%s, 3 attempts, retryDelay 50): settles with an error within 5 s and the file content reaches the sink in one request",
    async (name) => {
      const sink = await site(() => [500, {}]);
      const { file, tag } = scratchFile("client", 64 * KiB);
      const form = formOver(file);
      const client = senders.find(([n]) => n === name)![1](sink.origin, { retryAttempts: 3, retryDelay: 50, timeout: 5_000 });
      const outcome = await settleWithin(client.request({ method: "POST", url: "/v1/upload", data: form, headers: form.getHeaders() } as any), 5_000);
      expect({
        ...ending(outcome),
        requestsWithContent: carrying(sink.requests, tag).length,
      }).toEqual({ settled: true, rejected: true, requestsWithContent: 1 });
    },
  );
});

describe.each(senders)("a streamed body sent through the client's axios instance (%s)", (_name, make) => {
  test("a source that fails partway through: rejects within 3 s with the error of the source", async () => {
    const sink = await site(() => [200, {}]);
    const message = marker("source_failure");
    const source = failingSource(message);
    const outcome = await settleWithin(viaInstance(make(sink.origin), { data: source, headers: { "Content-Type": "application/octet-stream" } }), 3_000);
    expect({
      ...ending(outcome),
      carriesSourceMessage: outcome.settled && !outcome.ok && String(outcome.error?.message ?? "").includes(message),
    }).toEqual({ settled: true, rejected: true, carriesSourceMessage: true });
  });

  test("a source that stalls, with timeout 2000: rejects within 4 s with a timeout code and the source is destroyed", async () => {
    const sink = await site(() => [200, {}]);
    const source = stalledSource();
    const outcome = await settleWithin(viaInstance(make(sink.origin, { timeout: 2_000 }), { data: source, headers: { "Content-Type": "application/octet-stream" } }), 4_000);
    const code = codeOf(outcome);
    expect({
      settled: outcome.settled,
      isAxiosError: outcome.settled && !outcome.ok && outcome.error?.isAxiosError === true,
      timeoutCode: ["ECONNABORTED", "ETIMEDOUT"].includes(code) ? "ECONNABORTED or ETIMEDOUT" : code,
      sourceDestroyed: source.destroyed,
    }).toEqual({ settled: true, isAxiosError: true, timeoutCode: "ECONNABORTED or ETIMEDOUT", sourceDestroyed: true });
  });

  test("a source that stalls, with an AbortController aborted at 500 ms: rejects within 2 s with ERR_CANCELED and the source is destroyed", async () => {
    const sink = await site(() => [200, {}]);
    const source = stalledSource();
    const controller = new AbortController();
    later(500, () => controller.abort());
    const outcome = await settleWithin(
      viaInstance(make(sink.origin), { data: source, signal: controller.signal, headers: { "Content-Type": "application/octet-stream" } }),
      2_000,
    );
    expect({ ...rejection(outcome), sourceDestroyed: source.destroyed }).toEqual({ settled: true, rejected: true, code: "ERR_CANCELED", sourceDestroyed: true });
  });

  test("a source read to its end before the call: rejects within 1 s", async () => {
    const sink = await site(() => [200, {}]);
    const source = track(Readable.from([Buffer.from("rows\n")]));
    for await (const _chunk of source) {
      /* read to the end */
    }
    expect(source.readableEnded).toBe(true);
    const outcome = await settleWithin(viaInstance(make(sink.origin), { data: source, headers: { "Content-Type": "application/octet-stream" } }), 1_000);
    expect(ending(outcome)).toEqual({ settled: true, rejected: true });
  });

  test("maxBodyLength 64 KiB with a 1 MiB streamed form body: rejects with ERR_FR_MAX_BODY_LENGTH_EXCEEDED", async () => {
    const sink = await site(() => [200, {}]);
    const { file } = scratchFile("limit", 1 * MiB);
    const form = formOver(file);
    const outcome = await settleWithin(viaInstance(make(sink.origin), { data: form, headers: form.getHeaders(), maxBodyLength: 64 * KiB }), 5_000);
    expect(rejection(outcome)).toEqual({ settled: true, rejected: true, code: "ERR_FR_MAX_BODY_LENGTH_EXCEEDED" });
  });

  test("no maxBodyLength, a 12 MiB streamed form body answered 200: resolves and the sink receives every byte of the file", async () => {
    const sink = await site(() => [200, {}]);
    const { file, content } = scratchFile("large", 12 * MiB);
    const form = formOver(file);
    const outcome = await settleWithin(viaInstance(make(sink.origin, { timeout: 20_000 }), { data: form, headers: form.getHeaders() }), 15_000);
    expect({
      code: codeOf(outcome),
      requests: sink.requests.length,
      requestsWithFile: carrying(sink.requests, content).length,
    }).toEqual({ code: "(resolved)", requests: 1, requestsWithFile: 1 });
  });

  test("no maxBodyLength, a 12 MiB streamed form body answered 307 to the same origin: rejects with ERR_FR_MAX_BODY_LENGTH_EXCEEDED and the redirect target receives no POST", async () => {
    const sink = await site((_method, requestPath) => (requestPath.startsWith("/v1/upload") ? [307, { Location: "/v1/done" }] : [200, {}]));
    const { file } = scratchFile("large-307", 12 * MiB);
    const form = formOver(file);
    const outcome = await settleWithin(viaInstance(make(sink.origin, { timeout: 20_000 }), { data: form, headers: form.getHeaders() }), 15_000);
    expect({
      ...rejection(outcome),
      donePosts: sink.requests.filter((r) => r.path === "/v1/done" && r.method === "POST").length,
    }).toEqual({ settled: true, rejected: true, code: "ERR_FR_MAX_BODY_LENGTH_EXCEEDED", donePosts: 0 });
  });

  test("a 1 MiB streamed form body answered 307 to the same origin: resolves and the body is sent again in full", async () => {
    const sink = await site((_method, requestPath) => (requestPath.startsWith("/v1/upload") ? [307, { Location: "/v1/done" }] : [200, {}]));
    const { file, content } = scratchFile("resend", 1 * MiB);
    const form = formOver(file);
    const outcome = await settleWithin(viaInstance(make(sink.origin), { data: form, headers: form.getHeaders() }), 5_000);
    const upload = sink.requests.filter((r) => r.path === "/v1/upload");
    const done = sink.requests.filter((r) => r.path === "/v1/done" && r.method === "POST");
    expect({
      code: codeOf(outcome),
      uploadWithFile: carrying(upload, content).length,
      donePosts: done.length,
      doneWithFile: carrying(done, content).length,
      sameBody: upload.length === 1 && done.length === 1 && upload[0].body.equals(done[0].body),
    }).toEqual({ code: "(resolved)", uploadWithFile: 1, donePosts: 1, doneWithFile: 1, sameBody: true });
  });
});
