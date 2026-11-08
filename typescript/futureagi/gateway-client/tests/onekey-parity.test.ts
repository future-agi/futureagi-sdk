import { afterEach, beforeEach, describe, expect, it, jest } from "@jest/globals";
import * as gateway from "../src/index.js";
import * as requestParts from "../src/request-parts.js";
import { details, envelope, errorClass, FULL, HEADERS, IN_FLIGHT, NO_CODE_REMEDY, refusal, setup } from "./onekey-test-helpers.js";

import { CONTRACT_ROWS } from "./onekey-contract-fixtures.js";
const remedyFor = (code: string) => CONTRACT_ROWS.find((row) => row.code === code)!.remedy;
const TOP_UP = remedyFor("managed_credits_exhausted");
const SMALLER = remedyFor("managed_credits_insufficient");
const CAP = remedyFor("agent_budget_exhausted");
const ENABLE = remedyFor("future_agi_credits_off");
const REQUEST = { method: "POST", path: "/v1/chat/completions", body: { model: "example/model", messages: [] } };
const PATHS = ["request", "requestWithResponse", "requestRaw", "requestStream"] as const;
const SETTINGS = [
  { label: "flat", options: { maxRetries: 5 } },
  { label: "policy", options: { retryPolicy: new gateway.RetryPolicy({ rateLimitRetries: 5, serviceUnavailableRetries: 5 }) } },
];
const ROWS = [
  { status: 402, code: "managed_credits_exhausted", name: "InsufficientCreditsError", category: "out_of_credits", remedy: TOP_UP, attempts: 1 },
  { status: 402, code: "managed_credits_insufficient", name: "InsufficientCreditsError", category: "out_of_credits", remedy: SMALLER, attempts: 1 },
  { status: 402, code: "agent_budget_exhausted", name: "AgentBudgetExhaustedError", category: "agent_budget", remedy: CAP, attempts: 1 },
  { status: 429, code: "budget_exceeded", name: "BudgetExceededError", category: "budget_limit", remedy: CAP, attempts: 1 },
  { status: 429, code: "org_budget_exceeded", name: "BudgetExceededError", category: "budget_limit", remedy: CAP, attempts: 1 },
  { status: 429, code: "managed_spend_velocity", name: "RateLimitError", category: "rate_limit", remedy: null, attempts: 1 },
  { status: 429, code: "rate_limit_exceeded", name: "RateLimitError", category: "rate_limit", remedy: null, attempts: 6 },
  { status: 503, code: "managed_billing_unavailable", name: "ServiceUnavailableError", category: "billing_unavailable", remedy: null, attempts: 6 },
  { status: 403, code: "permission_denied", name: "PermissionDeniedError", category: "permission", remedy: null, attempts: 1 },
  { status: 403, code: "future_agi_credits_off", name: "FutureAGICreditsOffError", category: "permission", remedy: ENABLE, attempts: 1 },
  { status: 401, code: "invalid_api_key", name: "AuthenticationError", category: "invalid_key", remedy: null, attempts: 1 },
  { status: 403, code: "key_scope_denied", name: "PermissionDeniedError", category: "permission", remedy: null, attempts: 1 },
].map((row) => ({ ...row, remedy: remedyFor(row.code) }));
const REASONS = ["future_agi_api_key", "not_a_gateway_key", "missing_api_key", "unknown_api_key", "future_reason", "", null, undefined];
let sleep: jest.SpiedFunction<typeof requestParts.sleep>;
beforeEach(() => { sleep = jest.spyOn(requestParts, "sleep").mockResolvedValue(undefined); });
afterEach(() => jest.restoreAllMocks());

for (const path of PATHS) {
  for (const { label, options } of SETTINGS) {
    describe(`one-key parity via ${path} with ${label}`, () => {
      it.each([
        { status: 429, code: "future_refusal" },
        { status: 503, code: "future_refusal" },
        { status: 429, code: "managed_billing_unavailable" },
        { status: 503, code: "rate_limit_exceeded" },
        { status: 429, code: "" },
        { status: 503, code: false },
        { status: 429, code: 0 },
        { status: 503, code: ["managed_billing_unavailable"] },
      ])("never replays unknown or mismatched $status / $code", async ({ status, code }) => {
        const body = envelope(code, IN_FLIGHT);
        const { client, fetch } = setup(status, body, options);
        const error = await refusal(client[path](REQUEST));
        expect(fetch).toHaveBeenCalledTimes(1);
        expect(sleep).not.toHaveBeenCalled();
        expect(error.constructor).toBe(status === 429 ? gateway.RateLimitError : gateway.ServiceUnavailableError);
        expect(details(error).category).toBe("generic");
        // Unknown codes still require guidance when the gateway did not confirm dispatch.
        expect(details(error).remedy).toBe(NO_CODE_REMEDY);
        expect(error.body).toEqual(body);
      });

      for (const status of [429, 503]) {
        it.each([
          { label: "null code", body: { error: { code: null } } },
          { label: "missing code", body: { error: { message: "busy" } } },
          { label: "unwrapped code", body: { code: "future_refusal" } },
          { label: "null envelope", body: null },
          { label: "non-JSON", body: "upstream unavailable" },
        ])(`never replays a gateway response with unknown dispatch at ${status} with $label`, async ({ body }) => {
          const { client, fetch } = setup(status, body, options);
          if (typeof body === "string") fetch.mockImplementation(async () => new Response(body, { status, headers: HEADERS }));
          const error = await refusal(client[path](REQUEST));
          expect(fetch).toHaveBeenCalledTimes(1);
          expect(sleep).not.toHaveBeenCalled();
          expect(error.category).toBe("generic");
          expect(error.remedy).toBe(NO_CODE_REMEDY);
        });
      }

      it.each(ROWS)("exposes $category and remedy for $status / $code", async (row) => {
        const { client, fetch } = setup(row.status, envelope(row.code), options);
        const error = await refusal(client[path](REQUEST));
        expect(fetch).toHaveBeenCalledTimes(row.attempts);
        expect(error.constructor).toBe(errorClass(row.name));
        expect(details(error).category).toBe(row.category);
        expect(details(error).remedy).toBe(row.remedy);
        expect(Reflect.set(error, "category", "changed")).toBe(false);
        expect(Reflect.set(error, "remedy", "changed")).toBe(false);
        expect(error).toMatchObject({ message: "refused", requestId: null });
      });

      it.each(REASONS)("keeps invalid_api_key reason %p without retry", async (reason) => {
        const { client, fetch } = setup(401, envelope("invalid_api_key", { reason }), options);
        const error = await refusal(client[path](REQUEST));
        expect(fetch).toHaveBeenCalledTimes(1);
        expect(error.constructor).toBe(gateway.AuthenticationError);
        expect(details(error).category).toBe("invalid_key");
        expect(details(error).remedy).toBe(remedyFor("invalid_api_key"));
        expect(details(error).reason).toBe(reason ?? null);
        expect(Reflect.set(error, "reason", "changed")).toBe(false);
      });

      it("retries in-flight credits only once with the contract's conditional remedy", async () => {
        const { client, fetch } = setup(402, envelope("managed_credits_insufficient", IN_FLIGHT), options);
        const error = await refusal(client[path](REQUEST));
        expect(fetch).toHaveBeenCalledTimes(2);
        expect(details(error).category).toBe("out_of_credits");
        expect(details(error).remedy).toBe(SMALLER);
      });
    });
  }
}

it.each([246, 400, 401, 402, 403, 404, 408, 418, 422, 429, 446, 500, 502, 503, 504, 599])(
  "every status class provides generic read-only details for unknown code at %i", (status) => {
    for (const code of ["future_refusal", "invalid_api_key", "key_scope_denied"]) {
      if ((status === 401 && code === "invalid_api_key") || (status === 403 && code === "key_scope_denied")) continue;
      const body = envelope(code, FULL);
      const error = gateway.APIStatusError.from(status, body, new Headers());
      expect(error.constructor).toBe(gateway.APIStatusError.from(status, {}, new Headers()).constructor);
      expect(details(error).category).toBe("generic");
      expect(details(error).remedy).toBeNull();
      expect(Reflect.set(error, "category", "changed")).toBe(false);
      expect(Reflect.set(error, "remedy", "changed")).toBe(false);
    }
  },
);

it.each(ROWS)("direct $name construction evaluates the $code details", (row) => {
  const error = new (errorClass(row.name))(envelope(row.code), new Headers());
  expect(details(error).category).toBe(row.category);
  expect(details(error).remedy).toBe(row.remedy);
});

it.each([undefined, null, [], "bad", { reason: 42 }, { reason: [] }])(
  "invalid-key malformed metadata %p exposes null reason", (metadata) => {
    const error = gateway.APIStatusError.from(401, { error: { code: "invalid_api_key", metadata } }, new Headers());
    expect(details(error).reason).toBeNull();
  },
);

it.each([undefined, null, { limit_source: "agentcc_in_flight" }, { remedy_hint: "retry" },
  { limit_source: "credits", remedy_hint: "retry" }, { limit_source: "agentcc_in_flight", remedy_hint: "fund" }])(
  "incomplete in-flight condition %p retains the smaller-request remedy", (metadata) => {
    const error = gateway.APIStatusError.from(402, { error: { code: "managed_credits_insufficient", metadata } }, new Headers());
    expect(details(error).remedy).toBe(SMALLER);
  },
);
