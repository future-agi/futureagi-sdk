import { FutureAGIClient } from "../futureagi-client";
import { APIConnectionError, APITimeoutError, BadRequestError } from "../_core/errors";

const options = { baseUrl: "https://api.example.test", apiKey: "synthetic-key", secretKey: "synthetic-secret", timeoutMs: 20, retries: 0 };

function client(answer: (request: Request) => Response | Promise<Response>) {
  return new FutureAGIClient({ ...options, fetch: answer as typeof fetch });
}

describe("buffered response deadline lifecycle", () => {
  beforeEach(() => { jest.useFakeTimers(); });
  afterEach(() => { jest.useRealTimers(); });

  it("uses the remaining attempt budget after delayed headers, not a fresh body timeout", async () => {
    let stream!: ReadableStreamDefaultController<Uint8Array>;
    const c = client(async request => {
      await new Promise(resolve => setTimeout(resolve, 15));
      return new Response(new ReadableStream<Uint8Array>({
        start(controller) {
          stream = controller;
          request.signal.addEventListener("abort", () => controller.error(new DOMException("Aborted", "AbortError")), { once: true });
        },
      }), { headers: { "Content-Type": "application/json" } });
    });
    let outcome: unknown;
    const pending = c.datasets.list().then(value => { outcome = value; }, error => { outcome = error; });
    try {
      await jest.advanceTimersByTimeAsync(16);
      expect(outcome).toBeUndefined();
      await jest.advanceTimersByTimeAsync(5);
      expect(outcome).toBeInstanceOf(APITimeoutError);
      expect(jest.getTimerCount()).toBe(0);
    } finally {
      stream.error(new Error("fixture cleanup"));
      await pending;
    }
  });

  it.each([200, 204, 400])("cleans the deadline after a complete %i response", async status => {
    let signal!: AbortSignal;
    const c = client(request => {
      signal = request.signal;
      return new Response(status === 204 ? null : "{}", { status, headers: { "Content-Type": "application/json" } });
    });
    const outcome = await c.annotationQueues.list().then(value => value, error => error);
    if (status === 400) expect(outcome).toBeInstanceOf(BadRequestError);
    else expect(outcome).toEqual({});
    expect(jest.getTimerCount()).toBe(0);
    await jest.advanceTimersByTimeAsync(30);
    expect(signal.aborted).toBe(false);
  });

  it("cleans the deadline after a body failure", async () => {
    let signal!: AbortSignal;
    const cause = new Error("body closed early");
    const c = client(request => {
      signal = request.signal;
      return new Response(new ReadableStream({ start(controller) { controller.error(cause); } }), {
        headers: { "Content-Type": "application/json" },
      });
    });
    const error = await c.annotationQueues.list().then(() => undefined, value => value);
    expect(error).toBeInstanceOf(APIConnectionError);
    expect(error.cause).toBe(cause);
    expect(jest.getTimerCount()).toBe(0);
    await jest.advanceTimersByTimeAsync(30);
    expect(signal.aborted).toBe(false);
  });

  it("hands raw streams to their caller without a buffered-body deadline", async () => {
    let signal!: AbortSignal;
    let stream!: ReadableStreamDefaultController<Uint8Array>;
    const cancel = jest.fn();
    const c = client(request => {
      signal = request.signal;
      return new Response(new ReadableStream<Uint8Array>({ start(controller) { stream = controller; }, cancel }));
    });
    const body = await c.generatedClient.get<ReadableStream<Uint8Array>, unknown, true, "data">({
      url: "/stream", parseAs: "stream", responseStyle: "data", throwOnError: true,
    });
    expect(jest.getTimerCount()).toBe(0);
    await jest.advanceTimersByTimeAsync(30);
    expect(signal.aborted).toBe(false);
    stream.enqueue(new Uint8Array([1]));
    const reader = body.getReader();
    expect((await reader.read()).value).toEqual(new Uint8Array([1]));
    await reader.cancel();
    expect(cancel).toHaveBeenCalledTimes(1);
  });

  it("does not let a completed concurrent request clear another request's deadline", async () => {
    let count = 0;
    let stream!: ReadableStreamDefaultController<Uint8Array>;
    const c = client(request => {
      if (count++ === 0) return new Response("{}", { headers: { "Content-Type": "application/json" } });
      return new Response(new ReadableStream<Uint8Array>({
        start(controller) {
          stream = controller;
          request.signal.addEventListener("abort", () => controller.error(request.signal.reason), { once: true });
        },
      }), { headers: { "Content-Type": "application/json" } });
    });
    const first = c.annotationQueues.list();
    let outcome: unknown;
    const second = c.datasets.list().then(value => { outcome = value; }, error => { outcome = error; });
    try {
      await expect(first).resolves.toEqual({});
      await jest.advanceTimersByTimeAsync(21);
      expect(outcome).toBeInstanceOf(APITimeoutError);
      expect(jest.getTimerCount()).toBe(0);
    } finally {
      stream.error(new Error("fixture cleanup"));
      await second;
    }
  });
});
