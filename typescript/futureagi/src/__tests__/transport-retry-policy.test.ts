import { RetryClass, RetryPolicy, resilientFetch, retryClassFor } from "../transport";

const status = (code: number) => new Response(JSON.stringify({ code }), { status: code });

async function attempt(
  statuses: Array<number | Error>,
  retryPolicy: RetryPolicy | undefined,
  method = "POST",
): Promise<{ status: number | "threw"; calls: number }> {
  let calls = 0;
  const fetchMock = jest.fn(async () => {
    const next = statuses[Math.min(calls, statuses.length - 1)];
    calls += 1;
    if (next instanceof Error) throw next;
    return status(next);
  });
  const wrapped = resilientFetch({
    fetch: fetchMock as unknown as typeof fetch,
    sleep: async () => undefined,
    resolveCredentials: () => ({ apiKey: "k", secretKey: "s" }),
    retryPolicy,
  });
  const init = method === "GET" ? { method } : { method, body: "{}" };
  try {
    return { status: (await wrapped("http://api.test/x", init)).status, calls };
  } catch {
    return { status: "threw", calls };
  }
}

const netError = (code?: string) =>
  Object.assign(new TypeError("fetch failed"), code ? { cause: Object.assign(new Error(code), { code }) } : {});

describe("per-request retry classes", () => {
  it.each(["unsafe", "keyed-not-durable"] as RetryClass[])("%s never retries a 5xx", async (cls) => {
    for (const code of [500, 502, 503, 504]) {
      expect(await attempt([code, 200], cls)).toEqual({ status: code, calls: 1 });
    }
    expect(await attempt([429, 200], cls)).toEqual({ status: 200, calls: 2 });
  });

  it.each(["keyed", "http-idempotent"] as RetryClass[])("%s retries 429/502/503/504 on POST", async (cls) => {
    for (const code of [429, 502, 503, 504]) {
      expect(await attempt([code, 200], cls)).toEqual({ status: 200, calls: 2 });
    }
    expect(await attempt([500, 200], cls)).toEqual({ status: 500, calls: 1 });
  });

  it("network errors: pre-send in every class, any for keyed/idempotent (same table as Python)", async () => {
    for (const cls of [undefined, "unsafe", "keyed-not-durable", "keyed", "http-idempotent"] as const) {
      expect(await attempt([netError("UND_ERR_CONNECT_TIMEOUT"), 200], cls)).toEqual({ status: 200, calls: 2 });
    }
    expect(await attempt([netError("ECONNRESET"), 200], undefined, "POST")).toEqual({ status: "threw", calls: 1 });
    expect(await attempt([netError("ECONNRESET"), 200], undefined, "GET")).toEqual({ status: 200, calls: 2 });
    expect(await attempt([netError("ECONNRESET"), 200], "unsafe")).toEqual({ status: "threw", calls: 1 });
    expect(await attempt([netError("ECONNRESET"), 200], "keyed-not-durable", "GET")).toEqual({
      status: "threw",
      calls: 1,
    });
    expect(await attempt([netError("ECONNREFUSED"), 200], "unsafe")).toEqual({ status: 200, calls: 2 });
    expect(await attempt([netError("ECONNRESET"), 200], "keyed")).toEqual({ status: 200, calls: 2 });
    expect(await attempt([netError(), 200], "http-idempotent")).toEqual({ status: 200, calls: 2 });
  });

  it("no policy: a 5xx is retried only on idempotent methods (M1); 429 on every method", async () => {
    for (const code of [502, 503, 504]) {
      expect(await attempt([code, 200], undefined, "POST")).toEqual({ status: code, calls: 1 });
      expect(await attempt([code, 200], undefined, "PATCH")).toEqual({ status: code, calls: 1 });
      for (const method of ["GET", "PUT", "DELETE"]) {
        expect(await attempt([code, 200], undefined, method)).toEqual({ status: 200, calls: 2 });
      }
    }
    expect(await attempt([429, 200], undefined, "POST")).toEqual({ status: 200, calls: 2 });
    expect(await attempt([500, 200], undefined, "GET")).toEqual({ status: 500, calls: 1 });
  });

  it("a function picks the class per request", async () => {
    const byPath: RetryPolicy = (request) => (new URL(request.url).pathname === "/x" ? "keyed" : undefined);
    expect(await attempt([503, 200], byPath)).toEqual({ status: 200, calls: 2 });
    const unsafe: RetryPolicy = () => "unsafe";
    expect(await attempt([503, 200], unsafe, "GET")).toEqual({ status: 503, calls: 1 });
  });

  it("{ class, retries } overrides the count for one request (Python's {class, retries}, S7)", async () => {
    expect(await attempt([429, 429, 429, 200], { class: "unsafe", retries: 1 })).toEqual({ status: 429, calls: 2 });
    expect(await attempt([503, 200], { retries: 0 }, "GET")).toEqual({ status: 503, calls: 1 });
    expect(await attempt([503, 503, 200], { retries: 1 }, "GET")).toEqual({ status: 503, calls: 2 });
    expect(await attempt([503, 200], () => ({ class: "keyed", retries: 2 }))).toEqual({ status: 200, calls: 2 });
    expect(await attempt([503, 200], { class: "unsafe", retries: -1 })).toEqual({ status: "threw", calls: 0 });
    expect(await attempt([503, 200], { class: "Unsafe" as RetryClass })).toEqual({ status: "threw", calls: 0 });
  });

  it("an unknown class throws instead of retrying silently", async () => {
    const request = new Request("http://api.test/x");
    expect(() => retryClassFor("Unsafe" as RetryClass, request)).toThrow(/unknown retry class/);
    expect(await attempt([503, 200], "idempotent" as RetryClass)).toEqual({ status: "threw", calls: 0 });
  });
});
