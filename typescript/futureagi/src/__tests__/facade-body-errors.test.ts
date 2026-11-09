import { FutureAGIClient } from "../futureagi-client";
import { APIConnectionError, FutureAGIAPIError } from "../_core/errors";

const options = { baseUrl: "https://api.example.test", apiKey: "synthetic-key", secretKey: "synthetic-secret", retries: 3 };

describe("facade body read failures", () => {
  it.each([200, 400])("preserves a dropped %i response connection as the cause, without retrying", async status => {
    const cause = new TypeError("response connection terminated");
    const fetchMock = jest.fn(async () => new Response(new ReadableStream<Uint8Array>({
      start(controller) { controller.enqueue(new TextEncoder().encode('{"results":')); },
      pull(controller) { controller.error(cause); },
    }), { status, headers: { "Content-Type": "application/json" } }));
    const client = new FutureAGIClient({ ...options, fetch: fetchMock as unknown as typeof fetch });
    const error = await client.annotationQueues.list().then(() => undefined, value => value);
    expect(error).toBeInstanceOf(APIConnectionError);
    expect(error.cause).toBe(cause);
    expect(error.kind).toBe("connection");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("does not confuse a SyntaxError thrown by the body stream with invalid JSON", async () => {
    const cause = new SyntaxError("body decoder failed");
    const client = new FutureAGIClient({ ...options, fetch: (async () => new Response(new ReadableStream({
      start(controller) { controller.error(cause); },
    }), { headers: { "Content-Type": "application/json" } })) as typeof fetch });
    const error = await client.annotationQueues.list().then(() => undefined, value => value);
    expect(error).toBeInstanceOf(APIConnectionError);
    expect(error.cause).toBe(cause);
  });

  it("retains invalid_json for a fully read malformed document", async () => {
    const fetchMock = jest.fn(async () => new Response("{not json}", { headers: { "Content-Type": "application/json" } }));
    const client = new FutureAGIClient({ ...options, fetch: fetchMock as unknown as typeof fetch });
    const error = await client.annotationQueues.list().then(() => undefined, value => value);
    expect(error).toBeInstanceOf(FutureAGIAPIError);
    expect(error).not.toBeInstanceOf(APIConnectionError);
    expect(error.code).toBe("invalid_json");
    expect(error.statusCode).toBe(200);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
