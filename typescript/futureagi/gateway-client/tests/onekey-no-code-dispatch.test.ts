import { afterEach, beforeEach, describe, expect, it, jest } from "@jest/globals";
import * as gateway from "../src/index.js";
import * as requestParts from "../src/request-parts.js";
import { CONTRACT_ROWS } from "./onekey-contract-fixtures.js";
import { NO_CODE_REMEDY, refusal } from "./onekey-test-helpers.js";

const REQUEST = { method: "POST", path: "/v1/chat/completions", body: { model: "example/model", messages: [] } };
const PATHS = ["request", "requestWithResponse", "requestRaw", "requestStream"] as const;
const STATUSES = [408, 429, 500, 502, 503, 504];
const SETTINGS = [
  { label: "flat", options: { maxRetries: 5 } },
  { label: "policy", options: { maxRetries: 5, retryPolicy: new gateway.RetryPolicy({
    rateLimitRetries: 5, internalServerErrorRetries: 5, badGatewayRetries: 5,
    serviceUnavailableRetries: 5, gatewayTimeoutRetries: 5, connectionErrorRetries: 5, timeoutRetries: 5,
  }) } },
];
const CONDITIONS: Array<{ label: string; headers: Record<string, string>; safe: boolean }> = [
  { label: "no request-id", headers: {}, safe: true },
  { label: "dispatched false", headers: { "X-AgentCC-Request-ID": "offline", "X-AgentCC-Dispatched": "false" }, safe: true },
  { label: "dispatched true", headers: { "x-agentcc-request-id": "offline", "x-agentcc-dispatched": "TrUe" }, safe: false },
  { label: "dispatched missing", headers: { "x-agentcc-request-id": "offline" }, safe: false },
  { label: "dispatched unparseable", headers: { "x-agentcc-request-id": "offline", "x-agentcc-dispatched": "unknown" }, safe: false },
];
let sleep: jest.SpiedFunction<typeof requestParts.sleep>;
beforeEach(() => { sleep = jest.spyOn(requestParts, "sleep").mockResolvedValue(undefined); });
afterEach(() => jest.restoreAllMocks());

function setup(status: number, body: unknown, headers: Record<string, string>, options: gateway.ClientOptions = { maxRetries: 5 }) {
  const fetch = jest.fn<typeof globalThis.fetch>(async () => new Response(
    typeof body === "string" ? body : JSON.stringify(body),
    { status, headers: { "retry-after": "2", ...headers } },
  ));
  const client = new gateway.AgentCC({ apiKey: "test-only", baseUrl: "https://gateway.test", ...options, fetch });
  return { client, fetch };
}

for (const path of PATHS) {
  for (const { label, options } of SETTINGS) {
    describe(`no-code dispatch ${path} ${label}`, () => {
      for (const status of STATUSES) {
        it.each(CONDITIONS)(`${status} $label uses only trusted response headers`, async ({ headers, safe }) => {
          const { client, fetch } = setup(status, { error: { message: "refused" } }, headers, options);
          const error = await refusal(client[path](REQUEST));
          // RetryPolicy has no 408 allowance; retain that existing caller limit.
          const attempts = safe && !(status === 408 && label === "policy") ? 6 : 1;
          expect(fetch).toHaveBeenCalledTimes(attempts);
          expect(sleep.mock.calls).toEqual(Array.from({ length: attempts - 1 }, () => [2000]));
          expect(error.category).toBe("generic");
          expect(error.remedy).toBe(safe ? null : NO_CODE_REMEDY);
        });
      }
    });
  }

  describe(`no-code envelope and header boundaries ${path}`, () => {
    for (const condition of CONDITIONS) {
      it.each([
        { label: "null code", body: { error: { code: null } } },
        { label: "no envelope", body: {} },
        { label: "null body", body: null },
        { label: "malformed JSON", body: "<html>upstream unavailable</html>" },
        { label: "malformed envelope", body: { error: "unavailable" } },
        { label: "array envelope", body: { error: [] } },
        { label: "unadmitted flat code", body: { code: "gateway_timeout" } },
        { label: "unknown flat code", body: { code: "future_code" } },
        { label: "code-less envelope overrides flat r1 code", body: { error: {}, code: "managed_billing_unavailable" } },
      ])(`${condition.label} with $label`, async ({ body }) => {
        const { client, fetch } = setup(504, body, condition.headers);
        const error = await refusal(client[path](REQUEST));
        expect(fetch).toHaveBeenCalledTimes(condition.safe ? 6 : 1);
        expect(error.category).toBe("generic");
        expect(error.remedy).toBe(condition.safe ? null : NO_CODE_REMEDY);
      });
    }

    it.each([true, false])("headers override conflicting body dispatch %p", async (dispatched) => {
      const body = { dispatched, metadata: { dispatched }, error: { metadata: { dispatched } } };
      const { client, fetch } = setup(503, body, {
        "x-agentcc-request-id": "offline", "x-agentcc-dispatched": String(!dispatched),
      });
      const error = await refusal(client[path](REQUEST));
      expect(fetch).toHaveBeenCalledTimes(dispatched ? 6 : 1);
      expect(error.category).toBe("generic");
      expect(error.remedy).toBe(dispatched ? null : NO_CODE_REMEDY);
    });

    it("body dispatched false cannot replace a missing response header", async () => {
      const { client, fetch } = setup(503, { error: { metadata: { dispatched: false } }, dispatched: false }, { "x-agentcc-request-id": "offline" });
      const error = await refusal(client[path](REQUEST));
      expect(fetch).toHaveBeenCalledTimes(1);
      expect(error.category).toBe("generic");
      expect(error.remedy).toBe(NO_CODE_REMEDY);
    });

    it.each(["", "0", "no", "false,true", "false, false"])("unparseable dispatched %p is terminal", async (value) => {
      const { client, fetch } = setup(429, {}, { "x-agentcc-request-id": "", "x-agentcc-dispatched": value });
      const error = await refusal(client[path](REQUEST));
      expect(fetch).toHaveBeenCalledTimes(1);
      expect(error.remedy).toBe(NO_CODE_REMEDY);
    });

    it("an unrelated request-id header does not identify a gateway response", async () => {
      const { client, fetch } = setup(503, { request_id: "body-id" }, { "x-request-id": "other", "x-agentcc-dispatched": "true" });
      await refusal(client[path](REQUEST));
      expect(fetch).toHaveBeenCalledTimes(6);
    });

    for (const headers of [{}, { "x-agentcc-request-id": "offline", "x-agentcc-dispatched": "false" }] as Record<string, string>[]) {
      it.each([0, 1, 3])(`safe response respects request limit %i with ${JSON.stringify(headers)}`, async (maxRetries) => {
        const { client, fetch } = setup(503, {}, headers);
        await refusal(client[path]({ ...REQUEST, maxRetries }));
        expect(fetch).toHaveBeenCalledTimes(maxRetries + 1);
      });
      it.each([0, 1, 3])(`safe response respects status policy %i with ${JSON.stringify(headers)}`, async (limit) => {
        const { client, fetch } = setup(503, {}, headers, { maxRetries: 5, retryPolicy: new gateway.RetryPolicy({ serviceUnavailableRetries: limit }) });
        await refusal(client[path](REQUEST));
        expect(fetch).toHaveBeenCalledTimes(limit + 1);
      });
    }

    it.each([
      { status: 429, code: "budget_exceeded", dispatched: "false", attempts: 1 },
      { status: 429, code: "rate_limit_exceeded", dispatched: "true", attempts: 6 },
      { status: 503, code: "managed_billing_unavailable", dispatched: "true", attempts: 6 },
      { status: 504, code: "gateway_timeout", dispatched: "false", attempts: 1 },
    ])("coded $code keeps its contract rule with dispatched $dispatched", async ({ status, code, dispatched, attempts }) => {
      const { client, fetch } = setup(status, { error: { code } }, { "x-agentcc-request-id": "offline", "x-agentcc-dispatched": dispatched });
      const error = await refusal(client[path](REQUEST));
      expect(fetch).toHaveBeenCalledTimes(attempts);
      expect(error.remedy).toBe(CONTRACT_ROWS.find((row) => row.code === code)!.remedy);
    });

    it.each([false, true])("response-free unknown transport failures are terminal (timeout %p)", async (timeout) => {
      const { client, fetch } = setup(503, {}, {});
      fetch.mockRejectedValue(timeout ? new DOMException("offline timeout", "TimeoutError") : new TypeError("offline connection failure"));
      await expect(client[path](REQUEST)).rejects.toBeInstanceOf(timeout ? gateway.APITimeoutError : gateway.APIConnectionError);
      // No pre-send evidence: a missing response does not make replay safe.
      expect(fetch).toHaveBeenCalledTimes(1);
      expect(sleep).not.toHaveBeenCalled();
    });
  });
}
