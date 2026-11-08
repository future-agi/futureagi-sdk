import { afterEach, beforeEach, describe, expect, it, jest } from "@jest/globals";
import * as gateway from "../src/index.js";
import * as requestParts from "../src/request-parts.js";
import { details, envelope, errorClass, FIELDS, FULL, HEADERS, refusal, send, setup } from "./onekey-test-helpers.js";
import type { RequestPath } from "./onekey-test-helpers.js";

const ROWS = [
  { status: 402, code: "managed_credits_exhausted", name: "InsufficientCreditsError", attempts: 1 },
  { status: 402, code: "managed_credits_insufficient", name: "InsufficientCreditsError", attempts: 1 },
  { status: 402, code: "agent_budget_exhausted", name: "AgentBudgetExhaustedError", attempts: 1 },
  { status: 429, code: "budget_exceeded", name: "BudgetExceededError", attempts: 1 },
  { status: 429, code: "org_budget_exceeded", name: "BudgetExceededError", attempts: 1 },
  { status: 429, code: "managed_spend_velocity", name: "RateLimitError", attempts: 1 },
  { status: 429, code: "rate_limit_exceeded", name: "RateLimitError", attempts: 3 },
  { status: 503, code: "managed_billing_unavailable", name: "ServiceUnavailableError", attempts: 3 },
  { status: 403, code: "permission_denied", name: "PermissionDeniedError", attempts: 1 },
];
const TYPED = ROWS.slice(0, 5);
let sleep: jest.SpiedFunction<typeof requestParts.sleep>;
beforeEach(() => { sleep = jest.spyOn(requestParts, "sleep").mockResolvedValue(undefined); });
afterEach(() => jest.restoreAllMocks());

for (const path of ["json", "raw", "stream"] as RequestPath[]) {
  describe(`billing refusals via ${path}`, () => {
    it.each(ROWS)("$status $code raises $name with its retry contract", async (row) => {
      const body = envelope(row.code);
      const { client, fetch } = setup(row.status, body, { maxRetries: 2 });
      const error = await refusal(send(client, path));
      expect(fetch).toHaveBeenCalledTimes(row.attempts);
      expect(sleep.mock.calls).toEqual(Array.from({ length: row.attempts - 1 }, () => [2000]));
      expect(error.constructor).toBe(errorClass(row.name));
      expect(error.name).toBe(row.name);
      expect(error.statusCode).toBe(row.status);
      expect(error).toBeInstanceOf(gateway.APIStatusError);
      expect(error).toBeInstanceOf(gateway.AgentCCError);
      expect(error).toBeInstanceOf(Error);
      expect(error instanceof gateway.RateLimitError).toBe(row.status === 429);
      expect(error.message).toBe("refused");
      expect(error.requestId).toBe("req-refusal");
      expect(error.body).toEqual(body);
      if (row.status === 429) {
        expect(error).toMatchObject({ ratelimitLimit: 100, ratelimitRemaining: 0, ratelimitReset: 12 });
      }
      if (TYPED.includes(row)) {
        expect(details(error).metadata).toEqual(FULL);
        for (const [getter, field] of Object.entries(FIELDS)) {
          expect(details(error)[getter]).toEqual(FULL[field as keyof typeof FULL]);
        }
      } else {
        expect(details(error).metadata).toEqual(FULL);
      }
    });

    for (const options of [{ maxRetries: 5 }, { retryPolicy: new gateway.RetryPolicy({ rateLimitRetries: 5 }) }]) {
      it.each(["budget_exceeded", "org_budget_exceeded"])(`%s never retries with ${"maxRetries" in options ? "flat" : "policy"} limits`, async (code) => {
        const { client, fetch } = setup(429, envelope(code), options);
        const error = await refusal(send(client, path));
        expect(fetch).toHaveBeenCalledTimes(1);
        expect(sleep).not.toHaveBeenCalled();
        expect(error.constructor).toBe(errorClass("BudgetExceededError"));
      });
    }
  });
}

describe.each(TYPED)("$name metadata for $code", (row) => {
  it("preserves the full raw object and exposes read-only typed getters", () => {
    const body = envelope(row.code);
    const error = gateway.APIStatusError.from(row.status, body, new Headers(HEADERS));
    expect(error.body).toBe(body);
    expect(details(error).metadata).toBe(FULL);
    for (const [getter, field] of Object.entries(FIELDS)) {
      expect(details(error)[getter]).toEqual(FULL[field as keyof typeof FULL]);
      expect(Reflect.set(error, getter, "replacement")).toBe(false);
    }
    expect(details(error).metadata).toBe(FULL);
  });

  it("supports direct construction with the same body and header signature", () => {
    const error = new (errorClass(row.name))(envelope(row.code), new Headers(HEADERS));
    expect(error).toMatchObject({ name: row.name, statusCode: row.status, requiredUsd: 0.02, availableUsd: 0 });
    expect(error instanceof gateway.RateLimitError).toBe(row.status === 429);
  });

  it.each([
    { label: "partial", metadata: { available_usd: 0, scope: "" }, expected: [null, 0, null, null, "", null, null] },
    { label: "wrong field types", metadata: { required_usd: "0.02", available_usd: false, limit_source: 1, remedy_hint: [], scope: {}, resets_at: true, reason: 2 }, expected: Array(7).fill(null) },
    { label: "empty object", metadata: {}, expected: Array(7).fill(null) },
    { label: "null", metadata: null, expected: Array(7).fill(null) },
    { label: "array", metadata: ["invalid"], expected: Array(7).fill(null) },
    { label: "string", metadata: "invalid", expected: Array(7).fill(null) },
    { label: "number", metadata: 4, expected: Array(7).fill(null) },
    { label: "boolean", metadata: true, expected: Array(7).fill(null) },
  ])("handles $label metadata without coercion", ({ metadata, expected }) => {
    const error = gateway.APIStatusError.from(row.status, envelope(row.code, metadata), new Headers());
    const valid = metadata !== null && typeof metadata === "object" && !Array.isArray(metadata);
    expect(details(error).metadata).toBe(valid ? metadata : null);
    expect(Object.keys(FIELDS).map((field) => details(error)[field])).toEqual(expected);
  });

  it("returns null for absent metadata", () => {
    const error = gateway.APIStatusError.from(row.status, { error: { code: row.code } }, new Headers());
    expect(details(error).metadata).toBeNull();
    expect(Object.keys(FIELDS).map((field) => details(error)[field])).toEqual(Array(7).fill(null));
  });
});

describe("classification uses the status and nested code only", () => {
  it.each([undefined, null, "budget_exceeded", "rate_limit_error", "unrelated", 42])("ignores error.type %p", (type) => {
    expect(gateway.APIStatusError.from(429, envelope("budget_exceeded", FULL, type), new Headers()).constructor)
      .toBe(errorClass("BudgetExceededError"));
    expect(gateway.APIStatusError.from(429, envelope("rate_limit_exceeded", FULL, type), new Headers()).constructor)
      .toBe(gateway.RateLimitError);
  });

  it.each([
    { status: 402, code: "unknown", name: "APIStatusError", attempts: 1 },
    { status: 402, code: "budget_exceeded", name: "APIStatusError", attempts: 1 },
    { status: 429, code: "managed_credits_exhausted", name: "RateLimitError", attempts: 1 },
    { status: 500, code: "budget_exceeded", name: "InternalServerError", attempts: 1 },
    { status: 503, code: "managed_credits_insufficient", name: "ServiceUnavailableError", attempts: 1 },
    { status: 403, code: "budget_exceeded", name: "PermissionDeniedError", attempts: 1 },
    { status: 429, code: null, name: "RateLimitError", attempts: 3 },
    { status: 429, code: ["budget_exceeded"], name: "RateLimitError", attempts: 1 },
    { status: 429, code: { toString: "budget_exceeded" }, name: "RateLimitError", attempts: 1 },
    { status: 429, code: "toString", name: "RateLimitError", attempts: 1 },
    { status: 429, code: "__proto__", name: "RateLimitError", attempts: 1 },
  ])("keeps the status class but retries only absent codes for $status / $code", async (row) => {
    const { client, fetch } = setup(row.status, envelope(row.code), { maxRetries: 2 });
    const error = await refusal(send(client));
    expect(fetch).toHaveBeenCalledTimes(row.attempts);
    expect(error.constructor).toBe((gateway as unknown as Record<string, unknown>)[row.name]);
    expect(details(error).metadata).toEqual(FULL);
  });

  it.each([null, "invalid", [], {}, { error: null }, { error: [] }, { error: "budget_exceeded" }])("keeps malformed or unwrapped bodies unchanged: %p", (body) => {
    const error = gateway.APIStatusError.from(429, body, new Headers());
    expect(error.constructor).toBe(gateway.RateLimitError);
    expect(error.body).toBe(body);
  });

  it.each(ROWS)("does not classify $code on any other status", (row) => {
    for (const status of [400, 401, 402, 403, 404, 408, 418, 422, 429, 446, 500, 502, 503, 504]) {
      if (status === row.status) continue;
      const actual = gateway.APIStatusError.from(status, envelope(row.code), new Headers());
      const original = gateway.APIStatusError.from(status, {}, new Headers());
      expect(actual.constructor).toBe(original.constructor);
    }
  });

  it.each(["managed_spend_velocity", "rate_limit_exceeded", "managed_billing_unavailable"])("keeps policy retry counts for %s", async (code) => {
    const status = code === "managed_billing_unavailable" ? 503 : 429;
    const { client, fetch } = setup(status, envelope(code, { remedy_hint: "retry" }), {
      maxRetries: 0, retryPolicy: new gateway.RetryPolicy({ rateLimitRetries: 5, serviceUnavailableRetries: 4 }),
    });
    await refusal(send(client));
    expect(fetch).toHaveBeenCalledTimes(status === 503 ? 5 : 6);
    expect(sleep.mock.calls.every(([ms]) => ms === 2000)).toBe(true);
  });
});
