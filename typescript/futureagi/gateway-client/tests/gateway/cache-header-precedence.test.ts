/**
 * Cache headers from two places: the client's GatewayConfig cache section, sent
 * on every request, and a request's own cache_ttl / cache_namespace /
 * cache_force_refresh. On a header both set, the request's value is sent; the
 * config's other cache headers and its x-agentcc-config still go out.
 *
 * This is the @agentcc/client 1.0.1 golden case header_merge.l6_over_l5, with the
 * config written in the fields the gateway reads: that case's camelCase
 * cache.forceRefresh now raises a TypeError before anything is sent.
 */
import { describe, it, expect, jest } from "@jest/globals";
import { AgentCC } from "../../src/index.js";
import type { ClientOptions } from "../../src/index.js";

function okFetch() {
  return jest.fn<typeof fetch>(async () =>
    new Response(JSON.stringify({ id: "c1", object: "chat.completion", created: 1, model: "m", choices: [] }), {
      status: 200,
      headers: { "content-type": "application/json" },
    }),
  );
}

function sentHeaders(fetchMock: ReturnType<typeof okFetch>, call = 0): Record<string, string> {
  const init = fetchMock.mock.calls[call][1] as RequestInit;
  return init.headers as Record<string, string>;
}

function sentBody(fetchMock: ReturnType<typeof okFetch>, call = 0): Record<string, unknown> {
  const init = fetchMock.mock.calls[call][1] as RequestInit;
  return JSON.parse(String(init.body));
}

const PARAMS = { model: "m", messages: [{ role: "user" as const, content: "hi" }] };
const CONFIG = { cache: { ttl: 300, namespace: "cfg", force_refresh: true } };

describe("cache headers: the client's config, then the request's own values", () => {
  it("the request's cache_ttl and cache_namespace win over the config's; its force_refresh still goes out", async () => {
    const fetchMock = okFetch();
    const client = new AgentCC({ apiKey: "k", fetch: fetchMock, maxRetries: 0, config: CONFIG });
    await client.chat.completions.create({ ...PARAMS, cache_ttl: 5, cache_namespace: "param" });
    const h = sentHeaders(fetchMock);
    expect(h["x-agentcc-cache-ttl"]).toBe("5");
    expect(h["x-agentcc-cache-namespace"]).toBe("param");
    expect(h["x-agentcc-cache-force-refresh"]).toBe("true");
    expect(JSON.parse(h["x-agentcc-config"])).toEqual(CONFIG);
    const body = sentBody(fetchMock);
    expect(Object.keys(body).filter((k) => k.startsWith("cache_"))).toEqual([]);
  });

  it("a request's cache_force_refresh false wins over the config's true", async () => {
    const fetchMock = okFetch();
    const client = new AgentCC({ apiKey: "k", fetch: fetchMock, maxRetries: 0, config: CONFIG });
    await client.chat.completions.create({ ...PARAMS, cache_force_refresh: false });
    const h = sentHeaders(fetchMock);
    expect(h["x-agentcc-cache-force-refresh"]).toBe("false");
    expect(h["x-agentcc-cache-ttl"]).toBe("300");
    expect(h["x-agentcc-cache-namespace"]).toBe("cfg");
  });

  it("without request values the config's cache headers go out, and a request's value applies to that request only", async () => {
    const fetchMock = okFetch();
    const client = new AgentCC({ apiKey: "k", fetch: fetchMock, maxRetries: 0, config: CONFIG });
    await client.chat.completions.create({ ...PARAMS, cache_ttl: 5 });
    await client.chat.completions.create(PARAMS);
    expect(sentHeaders(fetchMock, 0)["x-agentcc-cache-ttl"]).toBe("5");
    const second = sentHeaders(fetchMock, 1);
    expect(second["x-agentcc-cache-ttl"]).toBe("300");
    expect(second["x-agentcc-cache-namespace"]).toBe("cfg");
    expect(second["x-agentcc-cache-force-refresh"]).toBe("true");
  });

  it("a withOptions copy keeps the config, and the request's value still wins there", async () => {
    const fetchMock = okFetch();
    const client = new AgentCC({ apiKey: "k", fetch: fetchMock, maxRetries: 0, config: CONFIG }).withOptions({ timeout: 5000 });
    await client.chat.completions.create({ ...PARAMS, cache_ttl: 7 });
    const h = sentHeaders(fetchMock);
    expect(h["x-agentcc-cache-ttl"]).toBe("7");
    expect(h["x-agentcc-cache-namespace"]).toBe("cfg");
  });

  it("the golden case's camelCase cache.forceRefresh raises TypeError, so nothing is sent", () => {
    const fetchMock = okFetch();
    const opts = { apiKey: "k", fetch: fetchMock, config: { cache: { ttl: 300, namespace: "cfg", forceRefresh: true } } } as unknown as ClientOptions;
    expect(() => new AgentCC(opts)).toThrow(TypeError);
    expect(() => new AgentCC(opts)).toThrow(/GatewayConfig cache\.forceRefresh is not read by the gateway/);
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
