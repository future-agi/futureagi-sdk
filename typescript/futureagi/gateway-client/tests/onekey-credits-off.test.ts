import { afterEach, beforeEach, describe, expect, it, jest } from "@jest/globals";
import * as gateway from "../src/index.js";
import * as requestParts from "../src/request-parts.js";
import { classifyRefusal } from "../src/refusal-policy.js";
import { routeStream, routeText } from "../src/react/route.js";
import { details, errorClass, HEADERS, IN_FLIGHT, NO_CODE_REMEDY, refusal, setup } from "./onekey-test-helpers.js";

const CODE = "future_agi_credits_off";
const NAME = "FutureAGICreditsOffError";
import { CONTRACT_ROWS } from "./onekey-contract-fixtures.js";
const REMEDY = CONTRACT_ROWS.find((row) => row.code === CODE)!.remedy;
const BODY = { error: { code: CODE, type: "permission", message: "Credits are off for this organization." } };
const PARAMS = { model: "example/model", messages: [] };
const REQUEST = { method: "POST", path: "/v1/chat/completions", body: PARAMS };
class EveryStatusPolicy extends gateway.RetryPolicy {
  override getRetriesForStatus(): number { return 5; }
}
const SETTINGS = [
  { label: "zero", options: { maxRetries: 0 } },
  { label: "five", options: { maxRetries: 5 } },
  { label: "rate-limit-policy", options: { retryPolicy: new gateway.RetryPolicy({ rateLimitRetries: 5 }) } },
  { label: "every-status-policy", options: { maxRetries: 5, retryPolicy: new EveryStatusPolicy() } },
];
const PATHS: Record<string, (client: gateway.AgentCC) => Promise<unknown>> = {
  json: (client) => client.request(REQUEST),
  withResponse: (client) => client.requestWithResponse(REQUEST),
  raw: (client) => client.requestRaw(REQUEST),
  stream: (client) => client.requestStream(REQUEST),
  chat: (client) => client.chat.completions.create(PARAMS),
  chatStream: (client) => client.chat.completions.create({ ...PARAMS, stream: true }),
  streamHelper: (client) => client.chat.completions.stream(PARAMS),
  toolsHelper: (client) => client.chat.completions.runTools({ ...PARAMS, tools: [], maxSteps: 5 }),
  copiedClient: (client) => client.withOptions({ maxRetries: 5 }).chat.completions.create(PARAMS),
  sessionClient: (client) => client.session().client.chat.completions.create(PARAMS),
};
let sleep: jest.SpiedFunction<typeof requestParts.sleep>;
beforeEach(() => { sleep = jest.spyOn(requestParts, "sleep").mockResolvedValue(undefined); });
afterEach(() => jest.restoreAllMocks());

function check(error: gateway.APIStatusError) {
  expect(error).toBeInstanceOf(gateway.PermissionDeniedError);
  expect(error).toMatchObject({ statusCode: 403, message: BODY.error.message, requestId: null, body: BODY });
  expect(error.constructor).toBe(errorClass(NAME));
  expect(error.name).toBe(NAME);
  expect(details(error).remedy).toBe(REMEDY);
  expect(details(error).metadata).toBeNull();
}

for (const [path, send] of Object.entries(PATHS)) {
  describe(`credits off via ${path}`, () => {
    it.each(SETTINGS)("is terminal with $label retries", async ({ options }) => {
      const { client, fetch } = setup(403, BODY, options);
      const error = await refusal(send(client));
      expect(fetch).toHaveBeenCalledTimes(1);
      expect(sleep).not.toHaveBeenCalled();
      check(error);
    });
  });
}

for (const path of ["request", "requestWithResponse", "requestRaw", "requestStream"] as const) {
  describe(`credits off request override via ${path}`, () => {
    it.each([0, 1, 5])("is terminal with maxRetries %i", async (maxRetries) => {
      const { client, fetch } = setup(403, BODY, { maxRetries: 5, retryPolicy: new EveryStatusPolicy() });
      const error = await refusal(client[path]({ ...REQUEST, maxRetries }));
      expect(fetch).toHaveBeenCalledTimes(1);
      expect(sleep).not.toHaveBeenCalled();
      check(error);
    });
  });
}

it.each([routeStream, routeText])("propagates the typed error through route helper %#", async (send) => {
  const { fetch } = setup(403, BODY);
  const error = await refusal(send({ api: "https://gateway.test/api/chat", fetch }, PARAMS));
  expect(fetch).toHaveBeenCalledTimes(1);
  check(error);
});

it("keeps health-check failure terminal", async () => {
  const onError = jest.fn();
  const { client, fetch } = setup(403, BODY, { maxRetries: 5, callbacks: [{ onError }] });
  expect(await client.healthCheck()).toBe(false);
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(sleep).not.toHaveBeenCalled();
  expect(onError).toHaveBeenCalledTimes(1);
  check(onError.mock.calls[0][1] as gateway.APIStatusError);
});

it("exports a directly constructible class with a read-only remedy", () => {
  const error = new (errorClass(NAME))(BODY, new Headers(HEADERS));
  check(error);
  expect(error.body).toBe(BODY);
  expect(Reflect.set(error, "remedy", "retry")).toBe(false);
  expect(Object.getOwnPropertyDescriptor(Object.getPrototypeOf(error), "remedy")?.set).toBeUndefined();
  expect(details(error).remedy).toBe(REMEDY);
});

it.each([undefined, null, "permission", "rate_limit_error"])("ignores error.type %p", (type) => {
  const body = { error: { ...BODY.error, type } };
  expect(gateway.APIStatusError.from(403, body, new Headers()).constructor).toBe(errorClass(NAME));
});

it.each([undefined, null, IN_FLIGHT])("never enables in-flight retries for metadata %p", (metadata) => {
  expect(classifyRefusal(403, { error: { ...BODY.error, metadata } })).toEqual({ name: NAME, retry: "never" });
});

it.each(["permission_denied", "unknown"])("leaves 403 %s unchanged", async (code) => {
  const { client, fetch } = setup(403, { error: { ...BODY.error, code } }, { maxRetries: 5, retryPolicy: new EveryStatusPolicy() });
  const error = await refusal(client.request(REQUEST));
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(sleep).not.toHaveBeenCalled();
  expect(error.constructor).toBe(gateway.PermissionDeniedError);
  // Explicit contract remedies win; otherwise unknown gateway dispatch needs guidance.
  expect(details(error).remedy).toBe(code === "permission_denied" ? CONTRACT_ROWS.find((row) => row.code === code)!.remedy : NO_CODE_REMEDY);
});

it.each([400, 401, 402, 404, 408, 418, 422, 429, 446, 500, 502, 503, 504])("does not specialize credits-off on status %i", (status) => {
  expect(classifyRefusal(status, BODY)).toBeNull();
  expect(gateway.APIStatusError.from(status, BODY, new Headers()).constructor)
    .toBe(gateway.APIStatusError.from(status, {}, new Headers()).constructor);
});
