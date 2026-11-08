import { afterEach, beforeEach, describe, expect, it, jest } from "@jest/globals";
import * as gateway from "../src/index.js";
import * as requestParts from "../src/request-parts.js";
import { CONTRACT_ROWS, CONTRACT_VARIANTS } from "./onekey-contract-fixtures.js";
import type { ContractRow } from "./onekey-contract-fixtures.js";
import { details, HEADERS, refusal, setup } from "./onekey-test-helpers.js";

const REQUEST = { method: "POST", path: "/v1/chat/completions", body: { model: "example/model", messages: [] } };
const PATHS = ["request", "requestWithResponse", "requestRaw", "requestStream"] as const;
const SETTINGS = [
  { label: "flat", options: { maxRetries: 5 } },
  { label: "policy", options: { retryPolicy: new gateway.RetryPolicy({ rateLimitRetries: 5, serviceUnavailableRetries: 5, gatewayTimeoutRetries: 5 }) } },
];
const FIELDS: Record<string, string> = {
  requiredUsd: "required_usd", availableUsd: "available_usd", limitSource: "limit_source", remedyHint: "remedy_hint",
  scope: "scope", resetsAt: "resets_at", reason: "reason", capScope: "cap_scope", capRef: "cap_ref",
  capKind: "cap_kind", policyRevision: "policy_revision", suggestions: "suggestions",
};
let sleep: jest.SpiedFunction<typeof requestParts.sleep>;
beforeEach(() => { sleep = jest.spyOn(requestParts, "sleep").mockResolvedValue(undefined); });
afterEach(() => jest.restoreAllMocks());

function body(row: ContractRow) {
  return { error: { code: row.code, type: row.type, message: "contract refusal", ...(row.metadata === null ? {} : { metadata: row.metadata }) } };
}
function check(error: gateway.APIStatusError, row: ContractRow) {
  expect(error.constructor).toBe((gateway as unknown as Record<string, unknown>)[row.name]);
  expect(error.category).toBe(row.category);
  expect(error.remedy).toBe(row.remedy);
  expect(error.body).toEqual(body(row));
  expect(error.requestId).toBe("req-refusal");
  expect(details(error).metadata).toEqual(row.metadata);
  const metadata = row.metadata as Record<string, unknown> | null;
  for (const [getter, field] of Object.entries(FIELDS)) {
    expect(details(error)[getter]).toEqual(metadata?.[field] ?? null);
    expect(Reflect.set(error, getter, "changed")).toBe(false);
  }
  expect(Reflect.set(error, "category", "changed")).toBe(false);
  expect(Reflect.set(error, "remedy", "changed")).toBe(false);
}

for (const path of PATHS) {
  for (const { label, options } of SETTINGS) {
    describe(`contract r2 ${path} ${label}`, () => {
      it.each(CONTRACT_ROWS)("classifies $status $code with its exact remedy and attempts", async (row) => {
        const { client, fetch } = setup(row.status, body(row), options);
        const error = await refusal(client[path](REQUEST));
        const attempts = row.retry === "never" ? 1 : row.retry === "once" ? 2 : 6;
        expect(fetch).toHaveBeenCalledTimes(attempts);
        expect(sleep.mock.calls).toEqual(Array.from({ length: attempts - 1 }, () => [2000]));
        check(error, row);
      });
      it.each(CONTRACT_VARIANTS)("honors $code variant $label", async (row) => {
        const { client, fetch } = setup(row.status, body(row), options);
        const error = await refusal(client[path](REQUEST));
        expect(fetch).toHaveBeenCalledTimes(row.retry === "never" ? 1 : row.retry === "once" ? 2 : 6);
        check(error, row);
      });
    });
  }
}

it.each(CONTRACT_ROWS)("does not classify $code on the wrong status", (row) => {
  for (const status of [400, 401, 402, 403, 404, 409, 422, 429, 503, 504]) {
    if (status === row.status) continue;
    const error = gateway.APIStatusError.from(status, body(row), new Headers());
    expect(error.constructor).toBe(gateway.APIStatusError.from(status, {}, new Headers()).constructor);
    expect(error.category).toBe("generic");
    expect(error.remedy).toBeNull();
  }
});

it.each([null, [], "bad", { cap_scope: 3, cap_ref: [], cap_kind: false, policy_revision: "7", suggestions: ["model", 1] }])(
  "validates administrative and suggestion metadata without coercion: %p", (metadata) => {
    const error = gateway.APIStatusError.from(404, { error: { code: "model_not_found", metadata } }, new Headers(HEADERS));
    for (const getter of ["capScope", "capRef", "capKind", "policyRevision", "suggestions"]) expect(details(error)[getter]).toBeNull();
  },
);

it("preserves unknown metadata keys without treating body-level metadata as wire metadata", () => {
  const metadata = { future_field: { kept: true }, reason: "new_reason" };
  const error = gateway.APIStatusError.from(403, { error: { code: "model_not_permitted", metadata } }, new Headers());
  expect(details(error).metadata).toBe(metadata);
  expect(details(error).reason).toBe("new_reason");
  const outside = gateway.APIStatusError.from(403, { error: { code: "model_not_permitted" }, metadata }, new Headers());
  expect(details(outside).metadata).toBeNull();
});
