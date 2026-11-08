import { afterEach, beforeEach, describe, expect, it, jest } from "@jest/globals";
import * as gateway from "../src/index.js";
import * as requestParts from "../src/request-parts.js";
import { CONTRACT_R3_ROWS } from "./onekey-contract-r3-fixtures.js";
import { details, refusal, setup } from "./onekey-test-helpers.js";

const REQUEST = { method: "POST", path: "/v1/chat/completions", body: { model: "example/model", messages: [] } };
const PATHS = ["request", "requestWithResponse", "requestRaw", "requestStream"] as const;
let sleep: jest.SpiedFunction<typeof requestParts.sleep>;
beforeEach(() => { sleep = jest.spyOn(requestParts, "sleep").mockResolvedValue(undefined); });
afterEach(() => jest.restoreAllMocks());

for (const path of PATHS) {
  for (const policy of [false, true]) {
    describe(`contract r3 ${path} policy=${policy}`, () => {
      it.each(CONTRACT_R3_ROWS)("classifies $status $code without replay", async (row) => {
        const body = { error: { code: row.code, type: row.type, message: "contract refusal", ...(row.metadata ? { metadata: row.metadata } : {}) } };
        const options = policy ? { retryPolicy: new gateway.RetryPolicy({ rateLimitRetries: 5, serviceUnavailableRetries: 5 }) } : { maxRetries: 5 };
        const { client, fetch } = setup(row.status, body, options);
        const error = await refusal(client[path](REQUEST));
        expect(error.constructor).toBe((gateway as unknown as Record<string, unknown>)[row.name]);
        expect(error.category).toBe("generic");
        expect(error.remedy).toBe(row.remedy);
        expect(error.body).toEqual(body);
        expect(error.statusCode).toBe(row.status);
        expect(error.requestId).toBe("req-refusal");
        expect(details(error).metadata).toEqual(row.metadata);
        if (row.metadata) {
          for (const [field, value] of Object.entries(row.metadata)) {
            const getter = field.replace(/_([a-z])/g, (_, letter: string) => letter.toUpperCase());
            expect(details(error)[getter]).toBe(value);
            expect(Reflect.set(error, getter, "changed")).toBe(false);
          }
        }
        expect(fetch).toHaveBeenCalledTimes(1);
        expect(sleep).not.toHaveBeenCalled();
      });
      it.each(CONTRACT_R3_ROWS)("ignores flat $code and never elevates it to a gateway refusal", async (row) => {
        const { client, fetch } = setup(row.status, row, { maxRetries: 5 });
        const error = await refusal(client[path](REQUEST));
        expect(error.category).toBe("generic");
        expect(error.remedy).toBeNull();
        expect(details(error).metadata).toBeNull();
        expect(fetch).toHaveBeenCalledTimes(1);
      });
      it.each(CONTRACT_R3_ROWS)("does not replay $code on a mismatched retryable status", async (row) => {
        for (const status of [429, 503, 504]) {
          const { client, fetch } = setup(status, { error: { code: row.code, metadata: { remedy_hint: "retry" } } }, { maxRetries: 5 });
          const error = await refusal(client[path](REQUEST));
          expect(error.constructor).toBe(gateway.APIStatusError.from(status, {}, new Headers()).constructor);
          expect(error.category).toBe("generic");
          expect(error.remedy).toBeNull();
          expect(fetch).toHaveBeenCalledTimes(1);
        }
      });
    });
  }
}

it("requires a string for model_alias_requested and ignores top-level metadata", () => {
  for (const metadata of [null, [], "bad", { model_alias_requested: 3 }]) {
    const error = gateway.APIStatusError.from(400, { error: { code: "omega_default_unroutable", metadata } }, new Headers());
    expect(details(error).modelAliasRequested).toBeNull();
  }
  const error = gateway.APIStatusError.from(400, { error: { code: "omega_default_unroutable" }, metadata: { model_alias_requested: "alias" } }, new Headers());
  expect(details(error).modelAliasRequested).toBeNull();
});
