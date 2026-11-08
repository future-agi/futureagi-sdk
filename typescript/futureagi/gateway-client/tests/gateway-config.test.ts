import { describe, it, expect } from "@jest/globals";
import {
  createHeaders,
  gatewayConfigToHeaders,
  gatewayConfigToDict,
  type GatewayConfig,
} from "../src/gateway-config.js";

describe("GatewayConfig", () => {
  it("gatewayConfigToDict strips undefined values", () => {
    // 1.0.1 built this from cache.enabled and a fallback section; D-21 keeps
    // cache's ttl, namespace and force_refresh only (the gateway applies no
    // other), so the undefined value is a cache field.
    const config: GatewayConfig = {
      cache: { ttl: 300, namespace: undefined },
    };
    const dict = gatewayConfigToDict(config);
    expect(dict.cache).toEqual({ ttl: 300 });
    expect(dict.fallback).toBeUndefined();
    expect(dict.guardrails).toBeUndefined();
  });

  it("gatewayConfigToHeaders produces x-agentcc-config JSON", () => {
    const config: GatewayConfig = {
      cache: { ttl: 60, namespace: "prod" },
    };
    const headers = gatewayConfigToHeaders(config);
    expect(headers["x-agentcc-config"]).toBeDefined();
    const parsed = JSON.parse(headers["x-agentcc-config"]);
    expect(parsed.cache.ttl).toBe(60);
    // Backward-compat headers
    expect(headers["x-agentcc-cache-ttl"]).toBe("60");
    expect(headers["x-agentcc-cache-namespace"]).toBe("prod");
  });

  it("empty config produces no headers", () => {
    const headers = gatewayConfigToHeaders({});
    expect(Object.keys(headers)).toHaveLength(0);
  });
});

describe("createHeaders", () => {
  it("creates auth header", () => {
    const h = createHeaders({ apiKey: "sk-test" });
    expect(h["Authorization"]).toBe("Bearer sk-test");
  });

  it("creates session headers", () => {
    const h = createHeaders({
      sessionId: "sess-1",
      sessionName: "research",
      traceId: "tr-abc",
    });
    expect(h["x-agentcc-session-id"]).toBe("sess-1");
    expect(h["x-agentcc-session-name"]).toBe("research");
    expect(h["x-agentcc-trace-id"]).toBe("tr-abc");
  });

  it("creates metadata header as JSON", () => {
    const h = createHeaders({ metadata: { env: "prod", tier: "premium" } });
    expect(JSON.parse(h["x-agentcc-metadata"])).toEqual({ env: "prod", tier: "premium" });
  });

  it("creates cache headers", () => {
    const h = createHeaders({
      cacheTtl: 120,
      cacheNamespace: "test",
      cacheForceRefresh: true,
    });
    expect(h["x-agentcc-cache-ttl"]).toBe("120");
    expect(h["x-agentcc-cache-namespace"]).toBe("test");
    expect(h["x-agentcc-cache-force-refresh"]).toBe("true");
  });

  it("creates guardrail policy header", () => {
    const h = createHeaders({ guardrailPolicy: "strict" });
    expect(h["X-Guardrail-Policy"]).toBe("strict");
  });

  it("creates property headers", () => {
    const h = createHeaders({ properties: { region: "us-west", team: "ml" } });
    expect(h["x-agentcc-property-region"]).toBe("us-west");
    expect(h["x-agentcc-property-team"]).toBe("ml");
  });

  it("includes config headers when config provided", () => {
    const h = createHeaders({
      apiKey: "sk-test",
      config: { cache: { ttl: 60 } },
    });
    expect(h["Authorization"]).toBe("Bearer sk-test");
    expect(h["x-agentcc-config"]).toBeDefined();
    expect(h["x-agentcc-cache-ttl"]).toBe("60");
  });

  it("returns empty object when no options set", () => {
    const h = createHeaders({});
    expect(Object.keys(h)).toHaveLength(0);
  });
});
