/**
 * D-21: what @agentcc/client 1.x carried that the gateway never applied stays
 * in the 2.0 compatibility package, and this client says so instead of
 * dropping it without a word.
 */
import { describe, it, expect, jest } from "@jest/globals";
import { AgentCC, createHeaders } from "../../src/index.js";
import type { ClientOptions } from "../../src/index.js";

function okFetch() {
  const headersAtCall: Record<string, string>[] = [];
  const fetchMock = jest.fn<typeof fetch>(async (_url, init) => {
    // Observe the wire before the transport scrubs its attempt-owned headers.
    headersAtCall.push({ ...(init?.headers as Record<string, string>) });
    return new Response(JSON.stringify({ id: "c1", object: "chat.completion", created: 1, model: "m", choices: [] }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  });
  return Object.assign(fetchMock, { headersAtCall });
}

function sentHeaders(fetchMock: ReturnType<typeof okFetch>): Record<string, string> {
  return fetchMock.headersAtCall[0];
}

const PARAMS = { model: "m", messages: [{ role: "user" as const, content: "hi" }] };

describe("D-21 shim-only client options", () => {
  it.each([
    ["dropParams", true],
    ["modifyParams", (p: Record<string, unknown>) => p],
    ["preCallRules", [() => ({ allow: true })]],
  ])("new AgentCC({ %s }) raises TypeError naming the option", (name, value) => {
    const opts = { apiKey: "k", [name]: value } as unknown as ClientOptions;
    expect(() => new AgentCC(opts)).toThrow(TypeError);
    expect(() => new AgentCC(opts)).toThrow(new RegExp(`AgentCC option ${name} is not part of @future-agi/sdk/gateway`));
  });

  it("an undefined or null shim-only option is not given", () => {
    const opts = { apiKey: "k", dropParams: undefined, modifyParams: null, preCallRules: undefined } as unknown as ClientOptions;
    expect(() => new AgentCC(opts)).not.toThrow();
  });

  it("withOptions on a valid client builds a clone without re-raising", () => {
    const client = new AgentCC({ apiKey: "k", fetch: okFetch() });
    expect(() => client.withOptions({ timeout: 5 })).not.toThrow();
  });

  it("the client has no moderations, batches or use()", () => {
    const client = new AgentCC({ apiKey: "k" }) as unknown as Record<string, unknown>;
    expect(client.moderations).toBeUndefined();
    expect(client.batches).toBeUndefined();
    expect(client.use).toBeUndefined();
  });
});

describe("D-21 GatewayConfig: cache only", () => {
  it.each(["fallback", "load_balance", "guardrails", "routing", "mirror", "retry", "timeout"])(
    "config section %s raises TypeError (the gateway names it in X-Agentcc-Config-Ignored)",
    (section) => {
      const opts = { apiKey: "k", config: { [section]: { anything: 1 } } } as unknown as ClientOptions;
      expect(() => new AgentCC(opts)).toThrow(new RegExp(`GatewayConfig section "${section}" is not applied by the gateway`));
    },
  );

  it.each(["enabled", "strategy", "semantic_threshold", "cache_by_model", "ignore_keys"])(
    "cache.%s raises TypeError (the gateway reads ttl, namespace and force_refresh only)",
    (field) => {
      const opts = { apiKey: "k", config: { cache: { ttl: 1, [field]: true } } } as unknown as ClientOptions;
      expect(() => new AgentCC(opts)).toThrow(new RegExp(`GatewayConfig cache\\.${field} is not read by the gateway`));
    },
  );

  it("a key that is no section at all raises TypeError", () => {
    const opts = { apiKey: "k", config: { cacheConfig: { ttlSeconds: 1 } } } as unknown as ClientOptions;
    expect(() => new AgentCC(opts)).toThrow(/"cacheConfig" is not a GatewayConfig section/);
  });

  it("null and undefined sections and fields mean not set", () => {
    const opts = { apiKey: "k", config: { fallback: null, retry: undefined, cache: { ttl: 5, enabled: null } } } as unknown as ClientOptions;
    expect(() => new AgentCC(opts)).not.toThrow();
  });

  it("cache ttl, namespace and force_refresh go out as x-agentcc-config and the flat cache headers", async () => {
    const fetchMock = okFetch();
    const client = new AgentCC({ apiKey: "k", fetch: fetchMock, config: { cache: { ttl: 300, namespace: "prod", force_refresh: true } } });
    await client.chat.completions.create(PARAMS);
    const h = sentHeaders(fetchMock);
    expect(JSON.parse(h["x-agentcc-config"])).toEqual({ cache: { ttl: 300, namespace: "prod", force_refresh: true } });
    expect(h["x-agentcc-cache-ttl"]).toBe("300");
    expect(h["x-agentcc-cache-namespace"]).toBe("prod");
    expect(h["x-agentcc-cache-force-refresh"]).toBe("true");
  });

  it("createHeaders({ config }) applies the same rule", () => {
    expect(() => createHeaders({ config: { guardrails: { deny: true } } } as unknown as Parameters<typeof createHeaders>[0])).toThrow(
      /GatewayConfig section "guardrails" is not applied by the gateway/,
    );
    expect(createHeaders({ config: { cache: { ttl: 60 } } })["x-agentcc-cache-ttl"]).toBe("60");
  });
});
