import { FutureAGIClient } from "../futureagi-client";
import { APITimeoutError } from "../_core/errors";

describe("dataset response deadlines", () => {
  it("aborts a stalled JSON body after headers without retrying", async () => {
    jest.useFakeTimers();
    let stream!: ReadableStreamDefaultController<Uint8Array>;
    let signal!: AbortSignal;
    const fetchMock = jest.fn(async (request: Request) => {
      signal = request.signal;
      return new Response(new ReadableStream<Uint8Array>({
        start(controller) {
          stream = controller;
          controller.enqueue(new TextEncoder().encode('{"results":'));
          signal.addEventListener("abort", () => controller.error(new DOMException("The operation was aborted", "AbortError")), { once: true });
        },
      }), { headers: { "Content-Type": "application/json" } });
    });
    const client = new FutureAGIClient({
      baseUrl: "https://api.example.test", apiKey: "synthetic-key", secretKey: "synthetic-secret",
      timeoutMs: 20, retries: 3, fetch: fetchMock as unknown as typeof fetch,
    });
    let outcome: unknown;
    const pending = client.datasets.list().then(value => { outcome = value; }, error => { outcome = error; });
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
});
