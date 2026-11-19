import { FutureAGIClient } from "../../futureagi-client";
import { BadRequestError } from "../errors";

const cases = [200, 400].flatMap(status => ["argument", "environment"].flatMap(source =>
  [false, true].flatMap(raw => [false, true].map(copy => ({ status, source, raw, copy })))));

it.each(cases)("scrubs captured headers: HTTP $status source=$source raw=$raw copy=$copy", async ({ status, source, raw, copy }) => {
  const token = "proxy-identity-fixture-value", value = `Bearer ${token}`;
  const refreshed = "refreshed-fixture-value";
  const prior = process.env.FI_EXTRA_HEADERS;
  process.env.FI_EXTRA_HEADERS = source === "environment" ? `Proxy-Authorization=${value};X-Diagnostic=diagnostic` : "";
  try {
    const transport = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const request = new Request(input, init);
      expect(request.headers.get("proxy-authorization")).toBe(value);
      expect(request.headers.get("x-diagnostic")).toBe("diagnostic");
      // Refresh the setting while the response to the previous credentials is in flight.
      process.env.FI_EXTRA_HEADERS = `Proxy-Authorization=Bearer ${refreshed}`;
      const message = [value, token, "diagnostic", refreshed].join(" | ");
      return Response.json({ status: false, result: {
        error_code: "validation_failed", message, diagnostic: message, details: [{ [token]: token }],
      } }, { status, headers: { "X-Request-Id": "trace-fixture-id", "Retry-After": "9" } });
    });
    const client = new FutureAGIClient({ apiKey: "api-fixture", secretKey: "secret-fixture", baseUrl: "http://localhost:9012",
      retries: 0, fetch: transport as typeof fetch,
      ...(source === "argument" ? { extraHeaders: { "Proxy-Authorization": value, "X-Diagnostic": "diagnostic" } } : {}),
    });
    const target = copy ? client.withOptions({ retries: 0 }) : client;
    const call = target.gateway.config.getActive();
    const error = await (raw ? call.withResponse() : call).then(
      () => { throw new Error("Expected typed error"); }, (e: unknown) => e,
    );
    expect(transport).toHaveBeenCalledTimes(1);
    expect(error).toBeInstanceOf(BadRequestError);
    const typed = error as BadRequestError;
    const safe = `[redacted] | [redacted] | [redacted] | ${refreshed}`;
    expect(typed.payload).toEqual({ status: false, result: {
      error_code: "validation_failed", message: safe, diagnostic: safe, details: [{ [token]: "[redacted]" }],
    } });
    expect(String(typed)).not.toContain(token);
    expect(typed.requestId).toBe("trace-fixture-id");
    expect(typed.retryAfter).toBe(9);
    expect(typed.code).toBe("validation_failed");
    expect(typed.statusCode).toBe(400);
  } finally {
    if (prior === undefined) delete process.env.FI_EXTRA_HEADERS;
    else process.env.FI_EXTRA_HEADERS = prior;
  }
});

it("keeps header secrets request-scoped across overlapping envelopes", async () => {
  const prior = process.env.FI_EXTRA_HEADERS;
  const first = "first-proxy-fixture", second = "second-proxy-fixture";
  let markFirst!: () => void, markSecond!: () => void;
  const firstSent = new Promise<void>(resolve => { markFirst = resolve; });
  const secondSent = new Promise<void>(resolve => { markSecond = resolve; });
  const calls: string[] = [];
  const client = new FutureAGIClient({ apiKey: "api-fixture", secretKey: "secret-fixture",
    baseUrl: "http://localhost:9012", retries: 0, fetch: (async (input: RequestInfo | URL, init?: RequestInit) => {
      const token = new Request(input, init).headers.get("proxy-authorization")!.split(" ")[1]!;
      calls.push(token);
      if (token === first) { markFirst(); await secondSent; } else { markSecond(); }
      return Response.json({ status: false, result: { error_code: "validation_failed", message: token, diagnostic: token } });
    }) as typeof fetch });
  try {
    process.env.FI_EXTRA_HEADERS = `Proxy-Authorization=Bearer ${first}`;
    const pending = client.gateway.config.getActive();
    await firstSent;
    process.env.FI_EXTRA_HEADERS = `Proxy-Authorization=Bearer ${second}`;
    const results = await Promise.allSettled([pending, client.withOptions({ retries: 0 }).gateway.config.getActive()]);
    expect(calls).toEqual([first, second]);
    for (const result of results) {
      expect(result.status).toBe("rejected");
      if (result.status !== "rejected") throw new Error("Expected typed error");
      expect(result.reason).toBeInstanceOf(BadRequestError);
      expect(result.reason.payload.result.diagnostic).toBe("[redacted]");
    }
  } finally {
    if (prior === undefined) delete process.env.FI_EXTRA_HEADERS;
    else process.env.FI_EXTRA_HEADERS = prior;
  }
});
