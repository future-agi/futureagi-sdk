import { afterEach, describe, expect, it, jest } from "@jest/globals";
import * as gateway from "../src/index.js";
import * as parts from "../src/request-parts.js";

const ID = "01ARZ3NDEKTSV4RRFFQ69G5FAV";
const OTHER_ID = "01ARZ3NDEKTSV4RRFFQ69G5FAW";
const REQUEST = { method: "POST", path: "/v1/chat/completions", body: { model: "example/model", messages: [] } };
const HEADERS = { "x-agentcc-request-id": ID, "x-agentcc-dispatched": "true", "x-agentcc-client-request-id": "correlation" };
type EvidenceView = { gatewayEvidence?: gateway.GatewayEvidence };
const view = (value: unknown) => value as EvidenceView;
const failure = async (promise: Promise<unknown>): Promise<unknown> => {
  try { await promise; } catch (error) { return error; }
  throw new Error("Expected failure");
};
function client(fetch: typeof globalThis.fetch, extra: gateway.ClientOptions = {}) {
  return new gateway.AgentCC({ apiKey: "offline-test", baseUrl: "https://gateway.test", maxRetries: 5, ...extra, fetch });
}
afterEach(() => { jest.restoreAllMocks(); });

for (const path of ["request", "requestWithResponse"] as const) describe(`post-header failure ${path}`, () => {
  for (const dispatched of ["true", "false", "invalid"]) {
    it.each(["timeout", "connection", "json"])(`${dispatched} preserves evidence on %s failure without replay`, async (kind) => {
      const response = new Response("{}", { headers: { ...HEADERS, "x-agentcc-dispatched": dispatched } });
      const original = kind === "timeout" ? new DOMException("body timed out", "TimeoutError")
        : kind === "connection" ? new TypeError("reader failed") : new SyntaxError("invalid JSON");
      // The transport exception may carry request objects; never retain it as a cause.
      Object.assign(original, { request: { authorization: "synthetic-sensitive-value" } });
      jest.spyOn(response, "json").mockImplementation(async () => {
        response.headers.set("x-agentcc-request-id", OTHER_ID);
        response.headers.set("x-agentcc-dispatched", "false");
        throw original;
      });
      const errors: unknown[] = [];
      const callback = new class extends gateway.CallbackHandler {
        override onError(_request: gateway.CallbackRequest, error: Error) { errors.push(error); }
      }();
      const fetch = jest.fn<typeof globalThis.fetch>(async () => response);
      const sleep = jest.spyOn(parts, "sleep").mockResolvedValue(undefined);
      const error = await failure(client(fetch, { callbacks: [callback] })[path](REQUEST));
      expect(view(error).gatewayEvidence).toEqual({ dispatched: dispatched === "invalid" ? "unknown" : dispatched === "true", gatewayRequestId: ID, clientRequestId: "correlation" });
      expect(view(error).gatewayEvidence).toBe(gateway.getGatewayEvidence(response));
      expect(Object.isFrozen(view(error).gatewayEvidence)).toBe(true);
      expect(errors).toHaveLength(1);
      expect(errors[0]).toBe(error);
      expect(fetch).toHaveBeenCalledTimes(1);
      expect(sleep).not.toHaveBeenCalled();
      expect(JSON.stringify(error)).not.toContain("synthetic-sensitive-value");
      expect(error).not.toHaveProperty("cause", original);
    });
  }
});

for (const path of ["request", "requestWithResponse", "requestRaw", "requestStream"] as const) {
  it.each([403, 503])(`${path} keeps status evidence when its error body fails at %s`, async (status) => {
    const response = new Response("{}", { status, headers: HEADERS });
    jest.spyOn(response, "json").mockRejectedValue(new DOMException("timeout", "TimeoutError"));
    jest.spyOn(response, "text").mockRejectedValue(new TypeError("body closed"));
    const errors: unknown[] = [];
    const callback = new class extends gateway.CallbackHandler {
      override onError(_request: gateway.CallbackRequest, error: Error) { errors.push(error); }
    }();
    const fetch = jest.fn<typeof globalThis.fetch>(async () => response);
    const error = await failure(client(fetch, { callbacks: [callback] })[path](REQUEST));
    expect(view(error).gatewayEvidence).toEqual({ dispatched: true, gatewayRequestId: ID, clientRequestId: "correlation" });
    expect(errors[0]).toBe(error);
    expect(fetch).toHaveBeenCalledTimes(1);
  });
}

for (const contentType of ["text/event-stream", "application/json"]) {
  it.each(["timeout", "connection"])(`${contentType} stream reader %s failure retains initial evidence`, async (kind) => {
    const original = kind === "timeout" ? new DOMException("body timed out", "TimeoutError") : new TypeError("reader failed");
    let reads = 0;
    const body = new ReadableStream<Uint8Array>({
      pull(controller) {
        if (reads++ === 0 && contentType === "text/event-stream") {
          controller.enqueue(new TextEncoder().encode('data: {"choices":[{"delta":{"content":"part"}}]}\n\n'));
        } else controller.error(original);
      },
    });
    const response = new Response(body, { headers: { ...HEADERS, "content-type": contentType } });
    const fetch = jest.fn<typeof globalThis.fetch>(async () => response);
    const stream = new gateway.Stream(await client(fetch).requestStream(REQUEST));
    const evidence = stream.gatewayEvidence;
    response.headers.set("x-agentcc-request-id", OTHER_ID);
    const iterator = stream[Symbol.asyncIterator]();
    if (contentType === "text/event-stream") expect((await iterator.next()).value).toMatchObject({ choices: [{ delta: { content: "part" } }] });
    const error = await failure(iterator.next());
    expect(view(error).gatewayEvidence).toBe(evidence);
    expect(view(error).gatewayEvidence).toEqual({ dispatched: true, gatewayRequestId: ID, clientRequestId: "correlation" });
    expect(fetch).toHaveBeenCalledTimes(1);
  });
}

it.each(["requestRaw", "requestStream"] as const)("%s keeps evidence on native response body failure", async (path) => {
  const body = new ReadableStream({ start(controller) { controller.error(new TypeError("body closed")); } });
  const response = new Response(body, { headers: HEADERS });
  const fetch = jest.fn<typeof globalThis.fetch>(async () => response);
  const raw = await client(fetch)[path](REQUEST);
  const evidence = gateway.getGatewayEvidence(raw);
  await expect(raw.arrayBuffer()).rejects.toThrow("body closed");
  expect(gateway.getGatewayEvidence(raw)).toBe(evidence);
  expect(evidence).toEqual({ dispatched: true, gatewayRequestId: ID, clientRequestId: "correlation" });
  expect(fetch).toHaveBeenCalledTimes(1);
});

for (const path of ["request", "requestWithResponse", "requestRaw", "requestStream"] as const) {
  it.each([undefined, "invalid", ID.toLowerCase(), `${ID}, ${ID}`, ID])(`${path} validates successful requestId alias %p`, async (id) => {
    const headers = new Headers({ "x-agentcc-client-request-id": OTHER_ID, "x-request-id": OTHER_ID });
    if (id !== undefined) headers.set("x-agentcc-request-id", id);
    const response = new Response("{}", { headers });
    const result = await client(jest.fn<typeof globalThis.fetch>(async () => response))[path](REQUEST);
    const metadata = path === "request" ? (result as { agentcc: gateway.AgentCCMetadata }).agentcc
      : path === "requestWithResponse" ? (result as gateway.WithResponseResult<unknown>).agentcc
      : new gateway.Stream(result as Response).agentcc;
    expect(metadata.requestId).toBe(id === ID ? ID : null);
    expect(metadata.gatewayEvidence?.gatewayRequestId).toBe(metadata.requestId);
    expect(JSON.parse(JSON.stringify(metadata)).requestId).toBe(metadata.requestId);
  });
}

it("a response-less timeout has unknown evidence and is terminal", async () => {
  const fetch = jest.fn<typeof globalThis.fetch>(async () => { throw new DOMException("timeout", "TimeoutError"); });
  const sleep = jest.spyOn(parts, "sleep").mockResolvedValue(undefined);
  const error = await failure(client(fetch, { maxRetries: 1 }).request(REQUEST));
  expect(error).toBeInstanceOf(gateway.APITimeoutError);
  expect(view(error).gatewayEvidence).toEqual({ dispatched: "unknown", gatewayRequestId: null, clientRequestId: null });
  // A timeout without proof of a pre-send failure must not replay the request.
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(sleep).not.toHaveBeenCalled();
});
