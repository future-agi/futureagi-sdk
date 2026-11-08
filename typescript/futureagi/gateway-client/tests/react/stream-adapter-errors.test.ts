/** @jest-environment ./tests/jsdom-with-fetch.environment.cjs */
import { it, expect, jest } from "@jest/globals";
import { renderHook, act, waitFor } from "@testing-library/react";
import { AgentCC, StreamError, RetryPolicy } from "../../src/index.js";
import { streamResponse } from "../../src/nextjs.js";
import { useAgentCCChat, useAgentCCCompletion, useAgentCCObject } from "../../src/react/index.js";

const { failureResponse, evidence, GUIDANCE } = require("../stream-adapter-boundary-cases.cjs") as {
  failureResponse(fixture: string, status: number, dispatch: string | null): Response;
  evidence(dispatch: string | null): StreamError["gatewayEvidence"];
  GUIDANCE: string;
};
for (const kind of ["chat", "completion", "object"] as const) {
  for (const fixture of ["sse-decode", "json-decode", "reader", "abort", "sse-shape"]) {
    for (const status of [200, 246]) for (const dispatch of [null, "invalid", "false", "true"]) {
      it(`${kind}: ${fixture} ${status} dispatch ${dispatch}`, async () => {
        const gatewayFetch = jest.fn<typeof fetch>(async () => failureResponse(fixture, status, dispatch));
        const client = new AgentCC({ apiKey: "synthetic-adapter-key", baseUrl: "https://gateway.test", fetch: gatewayFetch,
          dangerouslyAllowBrowser: true, retryPolicy: new RetryPolicy({ connectionErrorRetries: 3 }) });
        const routeFetch = jest.fn<typeof fetch>(async () => {
          const response = streamResponse(await client.chat.completions.stream({ model: "example/model", messages: [] }));
          return new Response(await response.text(), { headers: response.headers });
        });
        const onError = jest.fn<(error: Error) => void>();
        const onFinish = jest.fn();
        const options = { model: "example/model", fetch: routeFetch, onError };
        const { result, unmount } = renderHook(() => {
          if (kind === "chat") {
            const hook = useAgentCCChat({ ...options, onFinish });
            return { error: hook.error, run: () => hook.append({ role: "user", content: "synthetic" }) };
          }
          if (kind === "completion") {
            const hook = useAgentCCCompletion(options);
            return { error: hook.error, run: () => hook.complete("synthetic") };
          }
          const hook = useAgentCCObject({ ...options, schema: { type: "object" } });
          return { error: hook.error, run: () => hook.submit("synthetic") };
        });
        try {
          await act(async () => { await result.current.run(); });
          await waitFor(() => expect(onError).toHaveBeenCalledTimes(1));
          const error = result.current.error as StreamError;
          expect(error).toBeInstanceOf(StreamError);
          expect(error.gatewayEvidence).toEqual(evidence(dispatch));
          expect(onError).toHaveBeenCalledWith(error);
          const unknown = dispatch === null || dispatch === "invalid";
          expect(error.remedy).toBe(unknown ? GUIDANCE : null);
          expect(error.message.split(GUIDANCE).length - 1).toBe(unknown ? 1 : 0);
          expect(error.body).toBeNull();
          expect(error.message).not.toContain("synthetic-private");
          expect(onFinish).not.toHaveBeenCalled();
          expect(gatewayFetch).toHaveBeenCalledTimes(1);
          expect(routeFetch).toHaveBeenCalledTimes(1);
        } finally { unmount(); }
      });
    }
  }
}
