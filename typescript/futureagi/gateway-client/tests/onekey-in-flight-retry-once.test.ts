import { afterEach, beforeEach, describe, expect, it, jest } from "@jest/globals";
import { CallbackHandler, RetryPolicy } from "../src/index.js";
import type { ClientOptions } from "../src/index.js";
import { RETRYABLE_STATUS_CODES } from "../src/constants.js";
import * as requestParts from "../src/request-parts.js";
import { envelope, errorClass, HEADERS, IN_FLIGHT, refusal, send, setup } from "./onekey-test-helpers.js";
import type { RequestPath } from "./onekey-test-helpers.js";

let sleep: jest.SpiedFunction<typeof requestParts.sleep>;
beforeEach(() => { sleep = jest.spyOn(requestParts, "sleep").mockResolvedValue(undefined); });
afterEach(() => jest.restoreAllMocks());
const LIMITS: Array<{ label: string; options: ClientOptions; attempts: number }> = [
  { label: "flat zero", options: { maxRetries: 0 }, attempts: 1 },
  { label: "flat one", options: { maxRetries: 1 }, attempts: 2 },
  { label: "flat five", options: { maxRetries: 5 }, attempts: 2 },
  { label: "policy zero", options: { retryPolicy: new RetryPolicy({ rateLimitRetries: 0 }) }, attempts: 1 },
  { label: "policy one", options: { retryPolicy: new RetryPolicy({ rateLimitRetries: 1 }) }, attempts: 2 },
  { label: "policy five", options: { retryPolicy: new RetryPolicy({ rateLimitRetries: 5 }) }, attempts: 2 },
  { label: "policy takes precedence", options: { maxRetries: 0, retryPolicy: new RetryPolicy({ rateLimitRetries: 5 }) }, attempts: 2 },
  { label: "zero policy takes precedence", options: { maxRetries: 5, retryPolicy: new RetryPolicy({ rateLimitRetries: 0 }) }, attempts: 1 },
];

for (const path of ["json", "raw", "stream"] as RequestPath[]) {
  describe(`in-flight credit refusals via ${path}`, () => {
    it.each(LIMITS)("retries at most once with $label", async ({ options, attempts }) => {
      const { client, fetch } = setup(402, envelope("managed_credits_insufficient", IN_FLIGHT), options);
      const error = await refusal(send(client, path));
      expect(fetch).toHaveBeenCalledTimes(attempts);
      expect(sleep.mock.calls).toEqual(attempts === 2 ? [[2000]] : []);
      expect(error.constructor).toBe(errorClass("InsufficientCreditsError"));
      expect(error.statusCode).toBe(402);
    });

    it.each([
      { limit_source: "agentcc_in_flight" },
      { remedy_hint: "retry" },
      { limit_source: "agentcc_in_flight", remedy_hint: "fund" },
      { limit_source: "credits", remedy_hint: "retry" },
      { limit_source: ["agentcc_in_flight"], remedy_hint: "retry" },
      { limit_source: "agentcc_in_flight", remedy_hint: ["retry"] },
      {}, null, [], "retry",
    ])("requires both exact metadata values: %p", async (metadata) => {
      const { client, fetch } = setup(402, envelope("managed_credits_insufficient", metadata), { maxRetries: 5 });
      const error = await refusal(send(client, path));
      expect(fetch).toHaveBeenCalledTimes(1);
      expect(sleep).not.toHaveBeenCalled();
      expect(error.constructor).toBe(errorClass("InsufficientCreditsError"));
    });
  });
}

describe("in-flight retry boundaries", () => {
  it("keeps 402 out of the general retryable status set", () => {
    expect(RETRYABLE_STATUS_CODES.has(402)).toBe(false);
  });

  it.each(["managed_credits_exhausted", "agent_budget_exhausted"])("in-flight metadata never enables retries for %s", async (code) => {
    const { client, fetch } = setup(402, envelope(code, IN_FLIGHT), { retryPolicy: new RetryPolicy({ rateLimitRetries: 5 }) });
    await refusal(send(client));
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(sleep).not.toHaveBeenCalled();
  });

  it.each([0, 1, 5])("respects request-level maxRetries %i", async (maxRetries) => {
    const { client, fetch } = setup(402, envelope("managed_credits_insufficient", IN_FLIGHT), { maxRetries: 5 });
    await refusal(client.request({ method: "GET", path: "/v1/models", maxRetries }));
    expect(fetch).toHaveBeenCalledTimes(maxRetries === 0 ? 1 : 2);
  });

  it("succeeds after one retry and passes Retry-After through onRetry", async () => {
    const onRetry = jest.fn<() => void>();
    class Recorder extends CallbackHandler { override onRetry = onRetry; }
    const { client, fetch } = setup(402, envelope("managed_credits_insufficient", IN_FLIGHT), { maxRetries: 5, callbacks: [new Recorder()] });
    fetch.mockImplementationOnce(async () => new Response(JSON.stringify(envelope("managed_credits_insufficient", IN_FLIGHT)), { status: 402, headers: HEADERS }));
    fetch.mockImplementationOnce(async () => new Response(JSON.stringify({ id: "completed" }), { status: 200 }));
    expect(await send(client)).toMatchObject({ id: "completed" });
    expect(fetch).toHaveBeenCalledTimes(2);
    expect(sleep.mock.calls).toEqual([[2000]]);
    expect(onRetry).toHaveBeenCalledTimes(1);
    expect(onRetry).toHaveBeenCalledWith(expect.anything(), expect.objectContaining({ name: "InsufficientCreditsError" }), 0, 2000);
  });

  it("waits for Retry-After before sending the retry", async () => {
    let release!: () => void;
    sleep.mockImplementation(() => new Promise<void>((resolve) => { release = resolve; }));
    const { client, fetch } = setup(402, envelope("managed_credits_insufficient", IN_FLIGHT), { maxRetries: 5 });
    const pending = refusal(send(client));
    // Flush promise work without real timers or a real network request.
    for (let i = 0; i < 30; i++) await Promise.resolve();
    const before = fetch.mock.calls.length;
    const delays = [...sleep.mock.calls];
    if (release) release();
    await pending;
    expect(before).toBe(1);
    expect(delays).toEqual([[2000]]);
    expect(fetch).toHaveBeenCalledTimes(2);
  });

  it.each([false, true])("does not extend the two-attempt cap after a different error (policy %p)", async (policy) => {
    const { client, fetch } = setup(503, envelope("managed_billing_unavailable"), {
      maxRetries: 5, ...(policy ? { retryPolicy: new RetryPolicy({ rateLimitRetries: 5, serviceUnavailableRetries: 5 }) } : {}),
    });
    fetch.mockImplementationOnce(async () => new Response(JSON.stringify(envelope("managed_credits_insufficient", IN_FLIGHT)), { status: 402, headers: HEADERS }));
    const error = await refusal(send(client));
    expect(fetch).toHaveBeenCalledTimes(2);
    expect(error.name).toBe("ServiceUnavailableError");
    expect(sleep.mock.calls).toEqual([[2000]]);
  });

  it("does not retry a late in-flight refusal after an earlier ordinary retry", async () => {
    const { client, fetch } = setup(402, envelope("managed_credits_insufficient", IN_FLIGHT), { maxRetries: 5 });
    fetch.mockImplementationOnce(async () => new Response(JSON.stringify(envelope("rate_limit_exceeded")), { status: 429, headers: HEADERS }));
    await refusal(send(client));
    expect(fetch).toHaveBeenCalledTimes(2);
    expect(sleep.mock.calls).toEqual([[2000]]);
  });
});
