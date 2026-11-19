import { afterEach, beforeEach, describe, expect, it, jest } from "@jest/globals";
import * as gateway from "../src/index.js";
import * as parts from "../src/request-parts.js";
import { positiveRetryAfter } from "../src/refusal-policy.js";

const PATHS = ["request", "requestWithResponse", "requestRaw", "requestStream"] as const;
const REQUEST = { method: "POST", path: "/v1/chat/completions", body: { model: "example/model", messages: [] } };
const IN_FLIGHT = { limit_source: "agentcc_in_flight", remedy_hint: "retry" };
let sleep: jest.SpiedFunction<typeof parts.sleep>;
beforeEach(() => { sleep = jest.spyOn(parts, "sleep").mockResolvedValue(undefined); });
afterEach(() => { jest.restoreAllMocks(); });
function response(status: number, code: string, retryAfter: string, metadata: unknown = {}) {
  return new Response(JSON.stringify({ error: { code, metadata } }), { status, headers: { "retry-after": retryAfter } });
}
function client(fetch: typeof globalThis.fetch, policy: boolean = false) {
  return new gateway.AgentCC({ apiKey: "offline-test", baseUrl: "https://gateway.test", maxRetries: 5, fetch,
    retryPolicy: policy ? new gateway.RetryPolicy({ rateLimitRetries: 5, serviceUnavailableRetries: 5, connectionErrorRetries: 5, timeoutRetries: 5 }) : undefined });
}
for (const path of PATHS) describe(`retry delay contract ${path}`, () => {
  it.each([
    { status: 429, code: "rate_limit_exceeded" }, { status: 429, code: "token_rate_limit_exceeded" },
    { status: 503, code: "managed_billing_unavailable" }, { status: 503, code: "budget_state_unavailable" }, { status: 503, code: "key_list_not_loaded" },
  ])("honors 120-second backoff for $code", async ({ status, code }) => {
    const fetch = jest.fn<typeof globalThis.fetch>()
      .mockResolvedValueOnce(response(status, code, "120"))
      .mockResolvedValueOnce(new Response("{}"));
    await client(fetch)[path](REQUEST);
    expect(fetch).toHaveBeenCalledTimes(2);
    expect(sleep.mock.calls).toEqual([[120000]]);
  });
  it.each([".5", "+2", "2.0", "2e0", "1_0", "-2", "0", "NaN", "Infinity", "2junk", "2, 2", " 2", "2147484", "999999999999999999999"])("invalid in-flight delta %p is terminal", async (header) => {
    const fetch = jest.fn<typeof globalThis.fetch>()
      .mockResolvedValueOnce(response(402, "managed_credits_insufficient", header, IN_FLIGHT))
      .mockResolvedValueOnce(new Response("{}"));
    await expect(client(fetch)[path](REQUEST)).rejects.toBeInstanceOf(gateway.InsufficientCreditsError);
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(sleep).not.toHaveBeenCalled();
  });
  for (const policy of [false, true]) it.each(["billing", "connection", "timeout", "rate"])(`sticky two-attempt ceiling survives %s (policy ${policy})`, async (second) => {
    const fetch = jest.fn<typeof globalThis.fetch>().mockResolvedValueOnce(response(402, "managed_credits_insufficient", "2", IN_FLIGHT));
    if (second === "connection") fetch.mockRejectedValueOnce(new TypeError("offline connection"));
    else if (second === "timeout") fetch.mockRejectedValueOnce(new DOMException("offline timeout", "TimeoutError"));
    else fetch.mockResolvedValueOnce(response(second === "rate" ? 429 : 503, second === "rate" ? "rate_limit_exceeded" : "managed_billing_unavailable", "2"));
    fetch.mockResolvedValueOnce(new Response("{}"));
    await expect(client(fetch, policy)[path](REQUEST)).rejects.toBeInstanceOf(gateway.AgentCCError);
    expect(fetch).toHaveBeenCalledTimes(2);
    expect(sleep.mock.calls).toEqual([[2000]]);
  });
  it("a valid delay above the timer maximum refuses rather than replaying early", async () => {
    const fetch = jest.fn<typeof globalThis.fetch>().mockResolvedValueOnce(response(429, "rate_limit_exceeded", "2147484")).mockResolvedValueOnce(new Response("{}"));
    await expect(client(fetch)[path](REQUEST)).rejects.toBeInstanceOf(gateway.RateLimitError);
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(sleep).not.toHaveBeenCalled();
  });
});
it.each(["1", "2", "002", " \t2\t ", "2147483"])("accepts positive ASCII integer delta %p within timer range", (raw) => {
  expect(positiveRetryAfter(new Headers({ "retry-after": raw }))).toBe(Number(raw) * 1000);
});
