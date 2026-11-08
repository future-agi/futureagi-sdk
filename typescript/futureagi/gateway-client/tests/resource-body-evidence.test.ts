import { afterEach, expect, it, jest } from "@jest/globals";
import { AgentCC, CallbackHandler, RetryPolicy, getGatewayEvidence } from "../src/index.js";
import type { CallbackRequest, GatewayEvidence } from "../src/index.js";
import * as parts from "../src/request-parts.js";

const ID = "01ARZ3NDEKTSV4RRFFQ69G5FAV";
const HEADERS = { "x-agentcc-request-id": ID, "x-agentcc-dispatched": "true", "x-agentcc-client-request-id": "correlation" };
const calls: Array<[string, (client: AgentCC) => Promise<unknown>]> = [
  ["chat", (client) => client.chat.completions.create({ model: "example/model", messages: [] })],
  ["completions", (client) => client.completions.create({ model: "example/model", prompt: "example" })],
  ["embeddings", (client) => client.embeddings.create({ model: "example/model", input: "example" })],
  ["images", (client) => client.images.generate({ model: "example/model", prompt: "example" })],
  ["rerank", (client) => client.rerank.rank({ model: "example/model", query: "example", documents: ["example"] })],
  ["models", (client) => client.models.list()],
  ["transcriptions", (client) => client.audio.transcriptions.create({ model: "example/model", file: new Blob(["audio"]) })],
  ["translations", (client) => client.audio.translations.create({ model: "example/model", file: new Blob(["audio"]) })],
];
afterEach(() => { jest.restoreAllMocks(); });

for (const [name, invoke] of calls) {
  for (const perErrorPolicy of [false, true]) {
    it.each(["timeout", "connection"])(`${name} policy=${perErrorPolicy} preserves evidence on body %s without replay`, async (kind) => {
      const response = new Response("{}", { headers: HEADERS });
      const original = kind === "timeout" ? new DOMException("body timed out", "TimeoutError") : new TypeError("body closed");
      Object.assign(original, { request: { authorization: "synthetic-sensitive-value" } });
      jest.spyOn(response, "json").mockImplementation(async () => {
        response.headers.set("x-agentcc-request-id", "changed");
        throw original;
      });
      const errors: Error[] = [];
      const callback = new class extends CallbackHandler {
        override onError(_request: CallbackRequest, error: Error) { errors.push(error); }
      }();
      const fetch = jest.fn<typeof globalThis.fetch>(async () => response);
      const sleep = jest.spyOn(parts, "sleep").mockResolvedValue(undefined);
      const client = new AgentCC({ apiKey: "offline-test", baseUrl: "https://gateway.test", maxRetries: 5, fetch, callbacks: [callback],
        ...(perErrorPolicy ? { retryPolicy: new RetryPolicy({ timeoutRetries: 5, connectionErrorRetries: 5 }) } : {}),
      });
      let caught: unknown;
      try { await invoke(client); } catch (error) { caught = error; }
      const error = caught as Error & { gatewayEvidence?: GatewayEvidence };
      expect(error?.gatewayEvidence).toEqual({ dispatched: true, gatewayRequestId: ID, clientRequestId: "correlation" });
      expect(error.gatewayEvidence).toBe(getGatewayEvidence(response));
      expect(Object.isFrozen(error.gatewayEvidence)).toBe(true);
      expect(errors).toHaveLength(1);
      expect(errors[0]).toBe(error);
      expect(fetch).toHaveBeenCalledTimes(1);
      expect(sleep).not.toHaveBeenCalled();
      expect(JSON.stringify(error)).not.toContain("synthetic-sensitive-value");
    });
  }
  it(`${name} keeps validated success metadata`, async () => {
    const response = new Response('{"choices":[],"data":[]}', { headers: HEADERS });
    const fetch = jest.fn<typeof globalThis.fetch>(async () => response);
    const client = new AgentCC({ apiKey: "offline-test", baseUrl: "https://gateway.test", fetch });
    const result = await invoke(client);
    expect(result).toMatchObject({ agentcc: { requestId: ID, gatewayEvidence: { dispatched: true, gatewayRequestId: ID, clientRequestId: "correlation" } } });
    expect(fetch).toHaveBeenCalledTimes(1);
  });
}
