import { afterEach, beforeEach, describe, expect, it, jest } from "@jest/globals";
import * as gateway from "../src/index.js";
import * as requestParts from "../src/request-parts.js";
import { CONTRACT_ROWS } from "./onekey-contract-fixtures.js";
import { details, HEADERS, IN_FLIGHT, refusal, setup } from "./onekey-test-helpers.js";

const REQUEST = { method: "POST", path: "/v1/chat/completions", body: { model: "example/model", messages: [] } };
const PATHS = ["request", "requestWithResponse", "requestRaw", "requestStream"] as const;
const FLAT_CODES = new Set(["managed_credits_exhausted", "managed_credits_insufficient", "agent_budget_exhausted", "budget_exceeded",
  "org_budget_exceeded", "managed_spend_velocity", "rate_limit_exceeded", "managed_billing_unavailable"]);
const AFTER = [
  { status: 429, code: "managed_spend_velocity", metadata: { remedy_hint: "retry" }, max: 6 },
  { status: 429, code: "budget_throttled", metadata: {}, max: 6 },
  { status: 409, code: "idempotency_in_progress", metadata: {}, max: 6 },
  { status: 503, code: "provider_busy", metadata: {}, max: 6 },
  { status: 402, code: "managed_credits_insufficient", metadata: IN_FLIGHT, max: 2 },
];
let sleep: jest.SpiedFunction<typeof requestParts.sleep>;
beforeEach(() => {
  sleep = jest.spyOn(requestParts, "sleep").mockResolvedValue(undefined);
  jest.spyOn(Math, "random").mockReturnValue(0.5);
});
afterEach(() => jest.restoreAllMocks());

function withHeader(status: number, body: unknown, retryAfter: string | null, options: gateway.ClientOptions = { maxRetries: 5 }) {
  const result = setup(status, body, options);
  const headers = new Headers(HEADERS);
  headers.delete("retry-after");
  if (retryAfter !== null) headers.set("Retry-After", retryAfter);
  result.fetch.mockImplementation(async () => new Response(JSON.stringify(body), { status, headers }));
  return result;
}

for (const path of PATHS) {
  describe(`contract boundaries ${path}`, () => {
    for (const row of AFTER) {
      it.each([null, "0", "-1", "invalid", "2seconds", "Infinity", "NaN", "", "2"])(
        `${row.code} retries only after a positive valid Retry-After %p`, async (header) => {
          const { client, fetch } = withHeader(row.status, { error: row }, header);
          await refusal(client[path](REQUEST));
          expect(fetch).toHaveBeenCalledTimes(header === "2" ? row.max : 1);
          expect(sleep.mock.calls).toEqual(Array.from({ length: header === "2" ? row.max - 1 : 0 }, () => [2000]));
        },
      );
      it.each([0, 1, 3])(`${row.code} uses its status policy (429-equivalent for 409/402) with %i retries`, async (limit) => {
        const retryPolicy = new gateway.RetryPolicy({ rateLimitRetries: limit, serviceUnavailableRetries: limit });
        const { client, fetch } = withHeader(row.status, { error: row }, "2", { maxRetries: 5, retryPolicy });
        await refusal(client[path](REQUEST));
        expect(fetch).toHaveBeenCalledTimes(Math.min(limit + 1, row.max));
      });
      it.each([0, 1, 3])(`${row.code} respects request maxRetries %i`, async (maxRetries) => {
        const { client, fetch } = withHeader(row.status, { error: row }, "2");
        await refusal(client[path]({ ...REQUEST, maxRetries }));
        expect(fetch).toHaveBeenCalledTimes(Math.min(maxRetries + 1, row.max));
      });
    }

    it.each(["request_exceeds_minute_cap", "request_exceeds_hour_cap", "new_org_daily_cap", "future_reason"])(
      "never replays spend reason %s even with misleading retry hints and headers", async (reason) => {
        const { client, fetch } = withHeader(429, { error: { code: "managed_spend_velocity", metadata: { reason, remedy_hint: "retry" } } }, "2");
        const error = await refusal(client[path](REQUEST));
        expect(fetch).toHaveBeenCalledTimes(1);
        expect(sleep).not.toHaveBeenCalled();
        expect(error.remedy).toBe(CONTRACT_ROWS.find((r) => r.code === "managed_spend_velocity")!.remedy);
      },
    );
    it.each([undefined, null, {}, { remedy_hint: "lower_max_tokens" }, { remedy_hint: ["retry"] }])(
      "requires filled-window metadata for spend velocity %p", async (metadata) => {
        const { client, fetch } = withHeader(429, { error: { code: "managed_spend_velocity", metadata } }, "2");
        await refusal(client[path](REQUEST));
        expect(fetch).toHaveBeenCalledTimes(1);
      },
    );

    for (const row of CONTRACT_ROWS.filter((r) => r.retry === "backoff")) {
      it.each([null, "2"])(`${row.code} uses bounded backoff honoring Retry-After %p`, async (header) => {
        const { client, fetch } = withHeader(row.status, { error: row }, header);
        await refusal(client[path](REQUEST));
        expect(fetch).toHaveBeenCalledTimes(6);
        expect(sleep.mock.calls).toEqual((header ? [2000, 2000, 2000, 2000, 2000] : [500, 1000, 2000, 4000, 8000]).map((ms) => [ms]));
      });
    }

    it.each(CONTRACT_ROWS)("flat $code follows only the eight-code compatibility allowlist", async (row) => {
      const { client, fetch } = withHeader(row.status, row, "2");
      const error = await refusal(client[path](REQUEST));
      if (FLAT_CODES.has(row.code)) {
        expect(error.constructor).toBe((gateway as unknown as Record<string, unknown>)[row.name]);
        expect(error.category).toBe(row.category);
        expect(error.remedy).toBe(row.remedy);
        // Flat compatibility admits only the code, not body-level metadata.
        expect(details(error).metadata).toBeNull();
        expect(fetch).toHaveBeenCalledTimes(row.retry === "never" || row.code === "managed_spend_velocity" ? 1 : 6);
      } else {
        expect(error.constructor).toBe(gateway.APIStatusError.from(row.status, {}, new Headers()).constructor);
        expect(error.category).toBe("generic");
        expect(error.remedy).toBeNull();
        expect(details(error).metadata).toBeNull();
        expect(fetch).toHaveBeenCalledTimes([429, 503, 504].includes(row.status) ? 6 : 1);
      }
    });

    it.each([409, 429, 503, 504])("unknown and mismatched envelope codes at %i never replay", async (status) => {
      for (const code of ["future_code", "managed_resource_unsupported", "invalid_api_key", "", false, [], {}]) {
        const { client, fetch } = withHeader(status, { error: { code } }, "2");
        const error = await refusal(client[path](REQUEST));
        expect(fetch).toHaveBeenCalledTimes(1);
        expect(error.category).toBe("generic");
        expect(error.remedy).toBeNull();
      }
    });
    it.each([409, 429, 503, 504])("no error.code at %i keeps standard status retries", async (status) => {
      for (const body of [null, {}, { error: {} }, { error: { code: null } }, { code: "future_code" }]) {
        const { client, fetch } = withHeader(status, body, "2");
        await refusal(client[path](REQUEST));
        expect(fetch).toHaveBeenCalledTimes(status === 409 ? 1 : 6);
      }
    });
  });
}

it("never infers a flat r1 refusal from a malformed or code-less gateway envelope", () => {
  for (const error of [null, [], "bad", {}, { code: null }, { code: "model_not_found" }]) {
    const result = gateway.APIStatusError.from(402, { code: "managed_credits_exhausted", error }, new Headers());
    expect(result.constructor).toBe(gateway.APIStatusError);
    expect(result.category).toBe("generic");
  }
});
