// The platform Client in a runtime without Node's http module: a keyed request to a loopback plain-http host is passed
// to the runtime's fetch, and a Proxy-Authorization the caller sets is dropped from it, as on the direct route.
//
// `node:http` is made to fail to load for this file, so the SDK cannot send the request with its own agent. The global
// fetch is a recorder that answers each call itself; no connection is made. Keys and the Proxy-Authorization value are
// planted markers.

/* eslint-disable @typescript-eslint/no-explicit-any */
jest.mock("node:http", () => {
  throw new Error("node:http is not available in this runtime");
});

import { Client } from "../platform/client";

const realFetch = globalThis.fetch;
afterEach(() => {
  globalThis.fetch = realFetch;
});

const marker = (tag: string) => `FIMARK-rtf-${tag}-${Math.floor(Math.random() * 1e9).toString(16)}`;

function recorder(): { calls: Array<{ url: string; headers: Record<string, string> }>; fetch: typeof fetch } {
  const calls: Array<{ url: string; headers: Record<string, string> }> = [];
  const fake = async (url: any, init?: any) => {
    const headers: Record<string, string> = {};
    new Headers(init?.headers).forEach((value, name) => (headers[name] = value));
    calls.push({ url: String(url), headers });
    return new Response(JSON.stringify({ status: true, result: { ok: true } }), { status: 200, headers: { "content-type": "application/json" } });
  };
  return { calls, fetch: fake as unknown as typeof fetch };
}

describe("the platform Client without Node's http module, to a loopback plain-http host", () => {
  test.each([
    ["the default headers", (value: string) => ({ defaultHeaders: { "Proxy-Authorization": value } }), undefined],
    ["the headers of the call", () => ({}), (value: string) => ({ headers: { "proxy-authorization": value } })],
  ])("a Proxy-Authorization the caller sets in %s is not passed to the runtime's fetch, and the keys are", async (_where, config, options) => {
    const [apiKey, secretKey, proxyAuth] = [marker("ak"), marker("sk"), marker("pa")];
    const seen = recorder();
    globalThis.fetch = seen.fetch;
    const client = new Client({ apiKey, secretKey, baseUrl: "http://127.0.0.1:9", maxRetries: 0, timeout: 5000, ...config(proxyAuth) } as any);
    await client.request("GET", "/v1/probe/", {}, (options ? options(proxyAuth) : undefined) as any);
    expect(seen.calls).toHaveLength(1);
    const sent = JSON.stringify(seen.calls[0].headers);
    expect({ proxyAuthBytes: sent.split(proxyAuth).length - 1, proxyAuthHeader: "proxy-authorization" in seen.calls[0].headers }).toEqual({ proxyAuthBytes: 0, proxyAuthHeader: false });
    expect([seen.calls[0].headers["x-api-key"], seen.calls[0].headers["x-secret-key"]]).toEqual([apiKey, secretKey]);
  });
});
