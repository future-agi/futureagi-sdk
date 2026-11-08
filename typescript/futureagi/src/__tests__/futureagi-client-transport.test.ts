import { FutureAGIClient } from "../futureagi-client";
import { isPreSendError, resilientFetch, retryAfterMs, shouldRetry } from "../transport";

const json = (body: unknown, status = 200, headers: Record<string, string> = {}) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...headers },
  });

describe("FutureAGIClient transport", () => {
  const saved = { ...process.env };
  afterEach(() => {
    process.env = { ...saved };
  });

  it("does not throw without keys until the first request", async () => {
    delete process.env.FI_API_KEY;
    delete process.env.FI_SECRET_KEY;
    const fetchMock = jest.fn(async () => json({ results: [] }));
    const client = new FutureAGIClient({
      baseUrl: "http://api.test",
      fetch: fetchMock as unknown as typeof fetch,
    });
    await expect(client.annotationQueues.list({ limit: 1 })).rejects.toThrow(/requires credentials/);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("resolves keys from the environment on the first request", async () => {
    delete process.env.FI_API_KEY;
    delete process.env.FI_SECRET_KEY;
    const seen: Array<[string | null, string | null]> = [];
    const fetchMock = jest.fn(async (request: Request) => {
      seen.push([request.headers.get("X-Api-Key"), request.headers.get("X-Secret-Key")]);
      return json({ count: 0, results: [] });
    });
    const client = new FutureAGIClient({
      baseUrl: "http://api.test",
      fetch: fetchMock as unknown as typeof fetch,
    });
    process.env.FI_API_KEY = "k-env";
    process.env.FI_SECRET_KEY = "s-env";
    await client.annotationQueues.list({ limit: 1 });
    expect(seen).toEqual([["k-env", "s-env"]]);
  });

  it("datasets.versions.create makes one attempt on a 503 (M1); a GET on the same client retries", async () => {
    const calls: string[] = [];
    const fetchMock = jest.fn(async (request: Request) => {
      calls.push(`${request.method} ${new URL(request.url).pathname}`);
      return json({ detail: "busy" }, 503);
    });
    const client = new FutureAGIClient({
      baseUrl: "http://api.test",
      apiKey: "k-test-1234",
      secretKey: "s-test-1234",
      fetch: fetchMock as unknown as typeof fetch,
      retries: 1, // one real 0.5 s backoff for the GET below
    });
    const dataset = "3f2c1d7e-0000-4000-8000-000000000001";
    await expect(client.datasets.versions.create(dataset, { items: [] })).rejects.toBeDefined();
    expect(calls).toEqual([`POST /model-hub/datasets/${dataset}/versions/`]);
    calls.length = 0;
    await expect(client.datasets.versions.list(dataset)).rejects.toBeDefined();
    expect(calls).toEqual(Array(2).fill(`GET /model-hub/datasets/${dataset}/versions/`));
  });

  it("retries a 503 on an idempotent method honouring Retry-After and resends the same body", async () => {
    const bodies: string[] = [];
    const sleeps: number[] = [];
    const fetchMock = jest.fn(async (request: Request) => {
      bodies.push(await request.text());
      return bodies.length === 1 ? json({}, 503, { "Retry-After": "2" }) : json({ ok: true });
    });
    const wrapped = resilientFetch({
      fetch: fetchMock as unknown as typeof fetch,
      sleep: async (ms) => {
        sleeps.push(ms);
      },
      resolveCredentials: () => ({ apiKey: "k", secretKey: "s" }),
    });
    const response = await wrapped("http://api.test/x", { method: "PUT", body: '{"a":1}' });
    expect(response.status).toBe(200);
    expect(bodies).toEqual(['{"a":1}', '{"a":1}']);
    expect(sleeps).toEqual([2000]);
  });

  it("retries 502 only for idempotent methods", async () => {
    const sleeps: number[] = [];
    const fetchMock = jest.fn(async () => json({}, 502));
    const wrapped = resilientFetch({
      fetch: fetchMock as unknown as typeof fetch,
      retries: 2,
      sleep: async (ms) => {
        sleeps.push(ms);
      },
      resolveCredentials: () => ({ apiKey: "k", secretKey: "s" }),
    });
    expect((await wrapped("http://api.test/x", { method: "POST", body: "{}" })).status).toBe(502);
    expect(sleeps).toEqual([]);
    expect((await wrapped("http://api.test/x")).status).toBe(502);
    expect(sleeps).toEqual([500, 1000]);
    expect(shouldRetry("GET", 504)).toBe(true);
    expect(shouldRetry("POST", 429)).toBe(true);
    expect(shouldRetry("POST", 503)).toBe(false);
    expect(shouldRetry("PUT", 503)).toBe(true);
  });

  it("times out a hung request", async () => {
    const fetchMock = jest.fn(
      (request: Request) =>
        new Promise<Response>((_, reject) => {
          request.signal.addEventListener("abort", () => reject(request.signal.reason));
        }),
    );
    const wrapped = resilientFetch({
      fetch: fetchMock as unknown as typeof fetch,
      timeoutMs: 50,
      resolveCredentials: () => ({ apiKey: "k", secretKey: "s" }),
    });
    await expect(wrapped("http://api.test/x")).rejects.toThrow(/timed out after 50 ms/);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("retries a network error for POST only when nothing was sent", async () => {
    const fetchError = (code?: string) =>
      Object.assign(new TypeError("fetch failed"), code ? { cause: Object.assign(new Error(code), { code }) } : {});
    const run = async (method: string, code?: string) => {
      const sleeps: number[] = [];
      let calls = 0;
      const fetchMock = jest.fn(async () => {
        calls += 1;
        if (calls === 1) throw fetchError(code);
        return json({ ok: true });
      });
      const wrapped = resilientFetch({
        fetch: fetchMock as unknown as typeof fetch,
        sleep: async (ms) => {
          sleeps.push(ms);
        },
        resolveCredentials: () => ({ apiKey: "k", secretKey: "s" }),
      });
      const init = method === "GET" ? { method } : { method, body: "{}" };
      try {
        const response = await wrapped("http://api.test/x", init);
        return { status: response.status, calls, sleeps };
      } catch {
        return { status: "threw", calls, sleeps };
      }
    };
    // a reset after the body may have been sent: a POST is not repeated (no duplicate create/ingest)
    expect(await run("POST", "ECONNRESET")).toEqual({ status: "threw", calls: 1, sleeps: [] });
    expect(await run("POST")).toEqual({ status: "threw", calls: 1, sleeps: [] });
    // nothing left the machine: safe to retry any method
    expect(await run("POST", "ECONNREFUSED")).toEqual({ status: 200, calls: 2, sleeps: [500] });
    expect(await run("POST", "ENOTFOUND")).toEqual({ status: 200, calls: 2, sleeps: [500] });
    // idempotent methods retry any network error
    expect(await run("GET", "ECONNRESET")).toEqual({ status: 200, calls: 2, sleeps: [500] });
    expect(isPreSendError(fetchError("EAI_AGAIN"))).toBe(true);
    expect(isPreSendError(new Error("x"))).toBe(false);
  });

  it("parses Retry-After seconds and dates", () => {
    expect(retryAfterMs(new Response(null, { headers: { "Retry-After": "3" } }))).toBe(3000);
    expect(retryAfterMs(new Response(null))).toBeUndefined();
  });

  it("keeps experiments as a deprecated alias of experimentsV2", () => {
    const client = new FutureAGIClient({ baseUrl: "http://api.test", apiKey: "k", secretKey: "s" });
    expect(client.experiments).toBe(client.experimentsV2);
  });
});
