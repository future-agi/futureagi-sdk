/** @jest-environment ./tests/jsdom-with-fetch.environment.cjs */
import { it, expect, jest } from "@jest/globals";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useAgentCCChat } from "../../src/react/index.js";

const CHUNK = { id: "synthetic", object: "chat.completion.chunk", created: 0, model: "example/model", choices: [{ index: 0, delta: { content: "partial" }, finish_reason: null }] };

// A route that sends one chunk and then errors its body with the caller's abort reason.
function openRoute(headers: Record<string, string> = {}) {
  let opened!: () => void;
  const started = new Promise<void>((resolve) => { opened = resolve; });
  const routeFetch = jest.fn<typeof fetch>(async (_input, init) => {
    const signal = init?.signal as AbortSignal;
    let sent = false;
    return new Response(new ReadableStream({
      start(controller) { signal.addEventListener("abort", () => controller.error(signal.reason ?? Object.assign(new Error("aborted"), { name: "AbortError" }))); },
      pull(controller) {
        if (!sent) {
          sent = true;
          controller.enqueue(new TextEncoder().encode(`data: ${JSON.stringify(CHUNK)}\n\n`));
          opened();
        }
        // Stay open until the caller aborts.
        return new Promise<void>(() => {});
      },
    }), { headers: { "content-type": "text/event-stream", ...headers } });
  });
  return { routeFetch, started };
}

for (const route of ["plain route", "adapter route"]) {
  it(`stop() ends an open chat stream without onError or an error state (${route})`, async () => {
    const { routeFetch, started } = openRoute(route === "adapter route" ? { "x-futureagi-stream-format": "sdk-v1", "x-agentcc-dispatched": "true" } : {});
    const onError = jest.fn<(error: Error) => void>();
    const onFinish = jest.fn();
    const { result, unmount } = renderHook(() => useAgentCCChat({ model: "example/model", fetch: routeFetch, onError, onFinish }));
    try {
      await act(async () => { result.current.append({ role: "user", content: "synthetic" }); await started; });
      await waitFor(() => expect(result.current.messages[result.current.messages.length - 1]?.content).toBe("partial"));
      await act(async () => { result.current.stop(); });
      await waitFor(() => expect(result.current.isLoading).toBe(false));
      await act(async () => { await new Promise((resolve) => setTimeout(resolve, 20)); });
      expect(onError).not.toHaveBeenCalled();
      expect(onFinish).not.toHaveBeenCalled();
      expect(result.current.error).toBeNull();
      expect(routeFetch).toHaveBeenCalledTimes(1);
    } finally { unmount(); }
  });
}

it("a stream error before stop() still reaches onError", async () => {
  const routeFetch = jest.fn<typeof fetch>(async () => new Response(new ReadableStream({
    pull(controller) { controller.error(new Error("synthetic-reader-failure")); },
  }), { headers: { "content-type": "text/event-stream" } }));
  const onError = jest.fn<(error: Error) => void>();
  const { result, unmount } = renderHook(() => useAgentCCChat({ model: "example/model", fetch: routeFetch, onError }));
  try {
    await act(async () => { result.current.append({ role: "user", content: "synthetic" }); });
    await waitFor(() => expect(onError).toHaveBeenCalledTimes(1));
    expect(result.current.error).not.toBeNull();
  } finally { unmount(); }
});
