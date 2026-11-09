import { FutureAGIClient } from "../futureagi-client";
import { APITimeoutError } from "../_core/errors";

const options = { baseUrl: "https://api.example.test", apiKey: "synthetic-key", secretKey: "synthetic-secret", timeoutMs: 20 };

describe("facade response deadlines", () => {
  it.each([200, 400, 503])("bounds an unfinished %i body", async status => {
    jest.useFakeTimers();
    let stream!: ReadableStreamDefaultController<Uint8Array>;
    let signal!: AbortSignal;
    const fetchMock = jest.fn(async (request: Request) => {
      signal = request.signal;
      return new Response(new ReadableStream<Uint8Array>({
        start(controller) {
          stream = controller;
          signal.addEventListener("abort", () => controller.error(new DOMException("The operation was aborted", "AbortError")), { once: true });
        },
      }), { status, headers: { "Content-Type": "application/json" } });
    });
    const client = new FutureAGIClient({ ...options, retries: 0, fetch: fetchMock as unknown as typeof fetch });
    let outcome: unknown;
    const pending = client.annotationQueues.list().then(value => { outcome = value; }, error => { outcome = error; });
    try {
      await jest.advanceTimersByTimeAsync(21);
      expect(outcome).toBeInstanceOf(APITimeoutError);
      expect(signal.aborted).toBe(true);
      expect(fetchMock).toHaveBeenCalledTimes(1);
      expect(jest.getTimerCount()).toBe(0);
    } finally {
      stream.error(new Error("fixture cleanup"));
      await pending;
      jest.useRealTimers();
    }
  });

  it("bounds discarded-body cancellation and does not retry its timeout", async () => {
    jest.useFakeTimers();
    let release!: () => void;
    let signal!: AbortSignal;
    const cancel = jest.fn(() => new Promise<void>(resolve => { release = resolve; }));
    const fetchMock = jest.fn(async (request: Request) => {
      signal = request.signal;
      return new Response(new ReadableStream<Uint8Array>({ cancel }), {
        status: 503, headers: { "Content-Type": "application/json", "Retry-After": "0" },
      });
    });
    const client = new FutureAGIClient({ ...options, retries: 3, fetch: fetchMock as unknown as typeof fetch });
    let outcome: unknown;
    const pending = client.annotationQueues.list().then(value => { outcome = value; }, error => { outcome = error; });
    try {
      await jest.advanceTimersByTimeAsync(21);
      expect(cancel).toHaveBeenCalledTimes(1);
      expect(outcome).toBeInstanceOf(APITimeoutError);
      expect(signal.aborted).toBe(true);
      expect(fetchMock).toHaveBeenCalledTimes(1);
      expect(jest.getTimerCount()).toBe(0);
    } finally {
      // Releasing the fixture also lets the unrepaired implementation finish its retries.
      fetchMock.mockImplementation(async () => new Response("{}", { headers: { "Content-Type": "application/json" } }));
      release();
      await jest.runAllTimersAsync();
      await pending;
      jest.useRealTimers();
    }
  });
});
