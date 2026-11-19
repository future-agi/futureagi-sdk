/**
 * Query parameters reach the wire. The TypeScript client's equivalents of
 * Python's default_query / with_options(extra_query=) are the `defaultQuery`
 * option (constructor and withOptions) and a request's own `query`
 * (BaseClient.request / requestWithResponse / requestRaw / requestStream /
 * buildRequest). Both are sent as URL query parameters, the request's keys
 * winning over the client's. @agentcc/client 1.0.1 has no per-call
 * `extra_query` on the resource methods (chat.completions.create and the
 * others), and none is added; withOptions({ defaultQuery }) sets the new
 * client's whole map, as withOptions({ defaultHeaders }) does.
 */
import { describe, it, expect, jest } from "@jest/globals";
import { AgentCC } from "../../src/index.js";

function wire() {
  const urls: URL[] = [];
  const fetch = jest.fn<typeof globalThis.fetch>(async (url) => {
    urls.push(new URL(String(url)));
    return new Response(JSON.stringify({ object: "list", data: [] }), { status: 200, headers: { "content-type": "application/json" } });
  });
  return { fetch, urls };
}

const query = (url: URL) => Object.fromEntries(url.searchParams.entries());

describe("query parameters", () => {
  it("defaultQuery is sent on every resource request", async () => {
    const { fetch, urls } = wire();
    const client = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, defaultQuery: { tenant: "t1", region: "eu" } });
    await client.chat.completions.create({ model: "m", messages: [{ role: "user", content: "hi" }] });
    await client.models.list();
    await client.embeddings.create({ model: "m", input: "x" });
    expect(urls.map((u) => [u.pathname, query(u)])).toEqual([
      ["/v1/chat/completions", { tenant: "t1", region: "eu" }],
      ["/v1/models", { tenant: "t1", region: "eu" }],
      ["/v1/embeddings", { tenant: "t1", region: "eu" }],
    ]);
  });

  it("defaultQuery is sent on a stream request", async () => {
    const urls: URL[] = [];
    const fetch = jest.fn<typeof globalThis.fetch>(async (url) => {
      urls.push(new URL(String(url)));
      return new Response("data: [DONE]\n\n", { status: 200, headers: { "content-type": "text/event-stream" } });
    });
    const client = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, defaultQuery: { tenant: "t1" } });
    for await (const _ of await client.chat.completions.create({ model: "m", messages: [{ role: "user", content: "hi" }], stream: true })) void _;
    expect(query(urls[0])).toEqual({ tenant: "t1" });
  });

  it("a request's query is sent and its keys win over defaultQuery", async () => {
    const { fetch, urls } = wire();
    const client = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, defaultQuery: { tenant: "t1", region: "eu" } });
    await client.request({ method: "GET", path: "/v1/models", query: { region: "us", limit: "5" } });
    expect(urls[0].pathname).toBe("/v1/models");
    expect(query(urls[0])).toEqual({ tenant: "t1", region: "us", limit: "5" });
  });

  it("requestWithResponse, requestRaw and buildRequest send the same merged query", async () => {
    const { fetch, urls } = wire();
    const client = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test/v1", fetch, defaultQuery: { a: "1", b: "1" } });
    await client.requestWithResponse({ method: "GET", path: "/v1/models", query: { b: "2" } });
    await client.requestRaw({ method: "GET", path: "/v1/models", query: { b: "3" } });
    const built = client.buildRequest({ method: "GET", path: "/v1/models", query: { b: "4" } });
    expect(urls.map(query)).toEqual([
      { a: "1", b: "2" },
      { a: "1", b: "3" },
    ]);
    expect(built.url).toBe("http://gw.test/v1/models?a=1&b=4");
  });

  it("withOptions({ defaultQuery }) is sent by the new client; the original is unchanged", async () => {
    const { fetch, urls } = wire();
    const client = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, defaultQuery: { tenant: "t1" } });
    const derived = client.withOptions({ defaultQuery: { tenant: "t2", q: "1" } });
    await derived.models.list();
    await client.models.list();
    expect(urls.map(query)).toEqual([{ tenant: "t2", q: "1" }, { tenant: "t1" }]);
  });

  it("withOptions without defaultQuery keeps the client's query", async () => {
    const { fetch, urls } = wire();
    const derived = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, defaultQuery: { tenant: "t1" } }).withOptions({ timeout: 5000 });
    await derived.models.list();
    expect(query(urls[0])).toEqual({ tenant: "t1" });
  });

  it("values are URL-encoded", async () => {
    const { fetch, urls } = wire();
    await new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, defaultQuery: { q: "a b&c=d" } }).models.list();
    expect(urls[0].search).toBe("?q=a+b%26c%3Dd");
    expect(query(urls[0])).toEqual({ q: "a b&c=d" });
  });

  it("no query anywhere: no '?' on the URL", async () => {
    const { fetch, urls } = wire();
    await new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch }).models.list();
    expect(urls[0].href).toBe("http://gw.test/v1/models");
  });
});
