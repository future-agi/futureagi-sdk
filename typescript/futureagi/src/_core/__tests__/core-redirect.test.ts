/**
 * The root client never follows a 3xx on any namespace.
 * Real loopback sockets and Node's own fetch (a mocked fetch does not exercise `redirect` at all):
 * server A answers a redirect to server B, and B must never see a request. A core and a platform call
 * throw the same `UnexpectedRedirectError`, naming the target host only.
 */
import { createServer, type IncomingMessage, type Server } from "node:http";
import type { AddressInfo } from "node:net";

import { FutureAGIClient } from "../../futureagi-client";
import * as E from "../errors";

const KEYS = { apiKey: "k-redir-aaaa", secretKey: "s-redir-aaaa", retries: 0 };

type Seen = { method: string; url: string; headers: IncomingMessage["headers"] };

function serve(
  answer: (req: IncomingMessage, res: import("node:http").ServerResponse) => void,
): Promise<{ server: Server; port: number; seen: Seen[] }> {
  const seen: Seen[] = [];
  const server = createServer((req, res) => {
    seen.push({ method: req.method ?? "", url: req.url ?? "", headers: req.headers });
    req.resume();
    req.on("end", () => answer(req, res));
  });
  return new Promise((resolve) =>
    server.listen(0, "127.0.0.1", () => resolve({ server, port: (server.address() as AddressInfo).port, seen })),
  );
}

const close = (server: Server) => new Promise<void>((resolve) => server.close(() => resolve()));

describe("redirects are never followed (real sockets)", () => {
  let a: Awaited<ReturnType<typeof serve>>;
  let b: Awaited<ReturnType<typeof serve>>;
  let status = 302;
  let sameOrigin = false;

  beforeAll(async () => {
    b = await serve((_req, res) => {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ stolen: true, count: 0, results: [] }));
    });
    a = await serve((req, res) => {
      const target = sameOrigin ? `${req.url ?? "/"}/` : `http://127.0.0.1:${b.port}/steal`;
      res.writeHead(status, { Location: target, "x-request-id": "req-redir-1" });
      res.end();
    });
  });

  afterAll(async () => {
    await close(a.server);
    await close(b.server);
  });

  beforeEach(() => {
    a.seen.length = 0;
    b.seen.length = 0;
    status = 302;
    sameOrigin = false;
  });

  const client = () => {
    const c = new FutureAGIClient({ ...KEYS, baseUrl: `http://127.0.0.1:${a.port}` });
    return c;
  };

  it.each([
    ["core", (c: FutureAGIClient) => c.annotationQueues.list({ limit: 1 })],
    ["core typed", (c: FutureAGIClient) => c.datasets.versions.list("d1")],
    ["core POST", (c: FutureAGIClient) => c.datasets.versions.create("d1", { items: [] } as never)],
    ["platform", (c: FutureAGIClient) => c._platform.call("platform.capabilities.get")],
  ] as const)("%s: a 302 to another origin is UnexpectedRedirectError and the target sees nothing", async (_path, call) => {
    const err = (await Promise.resolve(call(client())).then(
      () => undefined,
      (e: unknown) => e,
    )) as E.UnexpectedRedirectError;
    expect(err).toBeInstanceOf(E.UnexpectedRedirectError);
    expect([err.statusCode, err.targetHost, err.requestId]).toEqual([302, `127.0.0.1:${b.port}`, "req-redir-1"]);
    expect(String(err.message)).not.toMatch(/k-redir|s-redir|\/steal/u);
    expect(a.seen).toHaveLength(1);
    expect(a.seen[0]!.headers["x-api-key"]).toBe("k-redir-aaaa"); // the keys went to the configured origin only
    expect(b.seen).toHaveLength(0);
  });

  it.each([301, 303, 307, 308])("a %i is not followed either", async (code) => {
    status = code;
    await expect(client().annotationQueues.list({ limit: 1 })).rejects.toBeInstanceOf(E.UnexpectedRedirectError);
    expect(b.seen).toHaveLength(0);
  });

  it("a same-origin redirect (a trailing slash) is not followed on a core call: one request, a typed error", async () => {
    sameOrigin = true;
    const err = (await client()
      .annotationQueues.list({ limit: 1 })
      .then(undefined, (e: unknown) => e)) as E.UnexpectedRedirectError;
    expect(err).toBeInstanceOf(E.UnexpectedRedirectError);
    expect(err.targetHost).toBe(`127.0.0.1:${a.port}`);
    expect(a.seen).toHaveLength(1);
  });
});
