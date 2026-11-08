import { describe, expect, it, jest } from "@jest/globals";
import { BaseClient } from "../src/base-client.js";
import { AgentCCError, APIConnectionError, ResponseBodyError, StreamError } from "../src/errors.js";
import { AgentCCError as BaseError } from "../src/error-base.js";
import { ResponseBodyError as BodyError, StreamError as BodyStreamError } from "../src/body-errors.js";
import { fetchWithScrub, requestInit } from "../src/request-transport.js";

const OPTIONS = { method: "POST" as const, path: "/test", body: { model: "test-model" } };

describe("request transport extraction", () => {
  it("preserves error constructor identity through the existing error module", () => {
    expect(AgentCCError).toBe(BaseError);
    expect(ResponseBodyError).toBe(BodyError);
    expect(StreamError).toBe(BodyStreamError);
    expect(new StreamError("test")).toBeInstanceOf(AgentCCError);
  });

  it("keeps JSON, FormData and GET request bodies unchanged", () => {
    const headers = { Authorization: "Bearer synthetic-token" };
    const json = requestInit(OPTIONS, headers, 1000);
    expect(json.headers).toBe(headers);
    expect(json.method).toBe("POST");
    expect(json.body).toBe(JSON.stringify(OPTIONS.body));
    const form = new FormData();
    form.set("field", "value");
    expect(requestInit({ ...OPTIONS, body: form }, headers, 1000).body).toBe(form);
    expect(requestInit({ ...OPTIONS, method: "GET" }, headers, 1000).body).toBeUndefined();
  });

  it("keeps serialization failures outside the connection-error boundary", async () => {
    const failure = new Error("synthetic serialization failure");
    const body = { toJSON: () => { throw failure; } };
    const fetch = jest.fn<typeof globalThis.fetch>();
    const client = new BaseClient({ apiKey: "synthetic-token", fetch });
    await expect(client.request({ ...OPTIONS, body })).rejects.toBe(failure);
    expect(fetch).not.toHaveBeenCalled();
  });

  it("keeps custom fetch bound to the client and scrubs after a successful send", async () => {
    let receiver: unknown;
    let sent: Record<string, string> | undefined;
    const fetch = jest.fn<typeof globalThis.fetch>(function (this: unknown, _url, init) {
      receiver = this;
      sent = init!.headers as Record<string, string>;
      expect(sent.Authorization).toBe("Bearer synthetic-token");
      return Promise.resolve(new Response("{}"));
    });
    const client = new BaseClient({ apiKey: "synthetic-token", fetch });
    await client.request(OPTIONS);
    expect(receiver).toBe(client);
    expect(sent!.Authorization).toBe("[REDACTED]");
  });

  it.each(["synchronous", "asynchronous"])("scrubs before a %s failure exits", async (mode) => {
    const headers = { Authorization: "Bearer synthetic-token" };
    const failure = new TypeError("synthetic transport failure");
    const send = () => {
      expect(headers.Authorization).toBe("Bearer synthetic-token");
      if (mode === "synchronous") throw failure;
      return Promise.reject(failure);
    };
    await expect(fetchWithScrub(send, headers)).rejects.toBe(failure);
    expect(headers.Authorization).toBe("[REDACTED]");
  });

  it("does not replay an unknown transport outcome after extraction", async () => {
    const fetch = jest.fn<typeof globalThis.fetch>(() => Promise.reject(new TypeError("synthetic failure")));
    const client = new BaseClient({ apiKey: "synthetic-token", maxRetries: 3, fetch });
    await expect(client.request(OPTIONS)).rejects.toBeInstanceOf(APIConnectionError);
    expect(fetch).toHaveBeenCalledTimes(1);
  });
});
