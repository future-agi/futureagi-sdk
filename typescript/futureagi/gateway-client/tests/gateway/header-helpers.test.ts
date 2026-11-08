/**
 * The request header helpers kept from @agentcc/client 1.0.1. Each
 * header the gateway reads is produced by createHeaders (for other HTTP
 * clients) and, where 1.0.1 had one, by the per-request parameter or the
 * client option, and reaches the wire. The x-agentcc-timeout-ms request
 * helper comes in a later minor release; TypeScript 1.0.1 had none.
 */
import { describe, it, expect, jest } from "@jest/globals";
import { AgentCC, createHeaders } from "../../src/index.js";

function wire() {
  const calls: Array<{ headers: Record<string, string>; body: Record<string, unknown> }> = [];
  const fetch = jest.fn<typeof globalThis.fetch>(async (_url, init) => {
    calls.push({ headers: { ...(init?.headers as Record<string, string>) }, body: JSON.parse(String(init?.body ?? "{}")) as Record<string, unknown> });
    return new Response(JSON.stringify({ id: "c", object: "chat.completion", created: 1, model: "m", choices: [{ index: 0, message: { role: "assistant", content: "ok" }, finish_reason: "stop" }] }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  });
  return { fetch, calls };
}

const ALL = createHeaders({
  config: { cache: { ttl: 300, namespace: "ns-config", force_refresh: true } },
  traceId: "trace-1",
  sessionId: "sess-1",
  sessionName: "checkout",
  sessionPath: "/cart/pay",
  metadata: { team: "a" },
  userId: "user-1",
  requestId: "req-1",
  cacheTtl: 60,
  cacheNamespace: "ns-1",
  cacheForceRefresh: true,
  guardrailPolicy: "strict",
  properties: { env: "prod" },
});

describe("request header helpers", () => {
  it.each([
    ["x-agentcc-config", JSON.stringify({ cache: { ttl: 300, namespace: "ns-config", force_refresh: true } })],
    ["x-agentcc-cache-ttl", "60"],
    ["x-agentcc-cache-namespace", "ns-1"],
    ["x-agentcc-cache-force-refresh", "true"],
    ["x-agentcc-session-id", "sess-1"],
    ["x-agentcc-session-name", "checkout"],
    ["x-agentcc-session-path", "/cart/pay"],
    ["x-agentcc-trace-id", "trace-1"],
    ["x-agentcc-user-id", "user-1"],
    ["x-agentcc-metadata", JSON.stringify({ team: "a" })],
    ["x-agentcc-property-env", "prod"],
    ["x-agentcc-request-id", "req-1"],
    ["X-Guardrail-Policy", "strict"],
  ])("createHeaders sends %s", (name, value) => {
    expect(ALL[name]).toBe(value);
  });

  it("per-request parameters become headers on the wire and leave the body", async () => {
    const { fetch, calls } = wire();
    const client = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch });
    await client.chat.completions.create({
      model: "m",
      messages: [{ role: "user", content: "hi" }],
      session_id: "s-req",
      trace_id: "t-req",
      request_metadata: { k: "v" },
      request_timeout: 5000,
      cache_ttl: 120,
      cache_namespace: "ns-req",
      cache_force_refresh: true,
      guardrail_policy: "pii",
    } as never);
    const { headers, body } = calls[0];
    expect(headers).toMatchObject({
      "x-agentcc-session-id": "s-req",
      "x-agentcc-trace-id": "t-req",
      "x-agentcc-metadata": JSON.stringify({ k: "v" }),
      "x-agentcc-request-timeout": "5000",
      "x-agentcc-cache-ttl": "120",
      "x-agentcc-cache-namespace": "ns-req",
      "x-agentcc-cache-force-refresh": "true",
      "X-Guardrail-Policy": "pii",
    });
    for (const key of ["session_id", "trace_id", "request_metadata", "request_timeout", "cache_ttl", "cache_namespace", "cache_force_refresh", "guardrail_policy"]) {
      expect(body).not.toHaveProperty(key);
    }
  });

  it("client options send session id, metadata and the cache config on every request", async () => {
    const { fetch, calls } = wire();
    const client = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, sessionId: "s-client", metadata: { app: "x" }, config: { cache: { ttl: 30 } } });
    await client.chat.completions.create({ model: "m", messages: [{ role: "user", content: "hi" }] });
    expect(calls[0].headers).toMatchObject({
      "x-agentcc-session-id": "s-client",
      "x-agentcc-metadata": JSON.stringify({ app: "x" }),
      "x-agentcc-config": JSON.stringify({ cache: { ttl: 30 } }),
      "x-agentcc-cache-ttl": "30",
    });
  });

  it("a session client sends the session id, name and metadata", async () => {
    const { fetch, calls } = wire();
    const client = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch });
    const { client: scoped } = client.session({ sessionId: "s-scope", name: "agent", metadata: { run: 1 } });
    await scoped.chat.completions.create({ model: "m", messages: [{ role: "user", content: "hi" }] });
    expect(calls[0].headers).toMatchObject({
      "x-agentcc-session-id": "s-scope",
      "x-agentcc-session-name": "agent",
      "x-agentcc-metadata": JSON.stringify({ run: 1 }),
    });
  });
});
