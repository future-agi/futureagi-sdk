/**
 * The jest environment this suite needs: the client streams
 * through the runtime's own web streams and fetch types, so each test context
 * must expose them, and bytes made in the test's realm must read back through
 * the runtime's decoder and Response.
 */
import { describe, it, expect } from "@jest/globals";

describe("jest node environment", () => {
  it.each(["fetch", "Response", "Headers", "ReadableStream", "TextDecoderStream", "TextEncoder", "TextDecoder", "AbortController", "FormData", "Blob"])(
    "exposes %s",
    (name) => {
      expect(typeof (globalThis as Record<string, unknown>)[name]).toBe("function");
    },
  );

  it("reads test-realm bytes through a Response body and a TextDecoderStream", async () => {
    const bytes = new TextEncoder().encode("data: {\"a\":1}\n\n");
    const body = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(bytes);
        controller.close();
      },
    });
    const text = await new Response(body).text();
    expect(text).toBe("data: {\"a\":1}\n\n");

    const reader = new Response(new Uint8Array(bytes)).body!.pipeThrough(new TextDecoderStream()).getReader();
    let out = "";
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      out += value;
    }
    expect(out).toBe(text);
  });
});
