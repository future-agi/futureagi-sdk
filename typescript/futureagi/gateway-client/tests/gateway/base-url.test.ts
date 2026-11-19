/**
 * D-07: trailing slashes and one trailing /v1 are dropped from the base URL,
 * always. @agentcc/client 1.x used it as given (only trailing slashes went),
 * so the `<origin>/v1` that FA's management API and the Console hand out
 * became /v1/v1/... (golden env.base_url.*). The shapes are the parity
 * env matrix's; fi.gateway (Python) normalises the same way.
 */
import { describe, it, expect, jest, beforeEach, afterEach } from "@jest/globals";
import { AgentCC, checkValidKey, healthCheck } from "../../src/index.js";
import { normalizeBaseUrl } from "../../src/env.js";

const URL = "https://gateway.example.test";
const SHAPES: Array<[string, string, string]> = [
  ["trailing_slash", `${URL}/`, `${URL}/v1/models`],
  ["v1", `${URL}/v1`, `${URL}/v1/models`],
  ["v1_slash", `${URL}/v1/`, `${URL}/v1/models`],
  ["v1_twice", `${URL}/v1/v1`, `${URL}/v1/v1/models`],
  ["uppercase_v1", `${URL}/V1`, `${URL}/V1/v1/models`],
  ["prefix", `${URL}/gw`, `${URL}/gw/v1/models`],
  ["prefix_v1", `${URL}/gw/v1`, `${URL}/gw/v1/models`],
  ["port", "http://127.0.0.1:8090/v1", "http://127.0.0.1:8090/v1/models"],
  ["localhost", "http://localhost:8090", "http://localhost:8090/v1/models"],
];

function okFetch() {
  return jest.fn<typeof globalThis.fetch>(async () => new Response(JSON.stringify({ object: "list", data: [] }), { status: 200, headers: { "content-type": "application/json" } }));
}

let saved: NodeJS.ProcessEnv;
beforeEach(() => {
  saved = { ...process.env };
  for (const k of Object.keys(process.env)) if (/^(AGENTCC_|FI_|OPENAI_)/.test(k)) delete process.env[k];
});
afterEach(() => {
  process.env = saved;
});

describe("D-07 base URL", () => {
  it.each(SHAPES)("%s: %s requests %s", async (_name, baseUrl, expected) => {
    const fetch = okFetch();
    await new AgentCC({ apiKey: "k", baseUrl, fetch }).models.list();
    expect(fetch.mock.calls[0][0]).toBe(expected);
  });

  it.each(SHAPES)("%s from AGENTCC_BASE_URL is normalised the same way", async (_name, baseUrl, expected) => {
    process.env.AGENTCC_BASE_URL = baseUrl;
    const fetch = okFetch();
    await new AgentCC({ apiKey: "k", fetch }).models.list();
    expect(fetch.mock.calls[0][0]).toBe(expected);
  });

  it("normalizeBaseUrl drops every trailing slash, then one /v1, then the slashes before it", () => {
    expect(normalizeBaseUrl("https://gw//v1//")).toBe("https://gw");
    expect(normalizeBaseUrl("https://gw/v10")).toBe("https://gw/v10");
    expect(normalizeBaseUrl("https://gw/apiv1")).toBe("https://gw/apiv1");
  });

  it("with nothing set the client uses the local gateway http://localhost:8090 (1.x's default, loopback)", async () => {
    const fetch = okFetch();
    await new AgentCC({ apiKey: "k", fetch }).models.list();
    expect(fetch.mock.calls[0][0]).toBe("http://localhost:8090/v1/models");
  });

  it("dryRun, withOptions and session clients keep the normalised URL", () => {
    const client = new AgentCC({ apiKey: "k", baseUrl: `${URL}/v1/` });
    const req = { model: "m", messages: [{ role: "user" as const, content: "hi" }] };
    expect(client.chat.completions.dryRun(req).url).toBe(`${URL}/v1/chat/completions`);
    expect(client.withOptions({ timeout: 1 }).chat.completions.dryRun(req).url).toBe(`${URL}/v1/chat/completions`);
    expect(client.session().client.chat.completions.dryRun(req).url).toBe(`${URL}/v1/chat/completions`);
  });

  it("checkValidKey and healthCheck use the normalised URL", async () => {
    const seen: string[] = [];
    const real = globalThis.fetch;
    globalThis.fetch = (async (url: string | URL | Request) => {
      seen.push(String(url));
      return new Response(JSON.stringify({ object: "list", data: [], choices: [] }), { status: 200, headers: { "content-type": "application/json" } });
    }) as typeof globalThis.fetch;
    try {
      await checkValidKey({ apiKey: "k", baseUrl: `${URL}/v1` });
      await healthCheck({ apiKey: "k", baseUrl: `${URL}/v1/`, model: "m" });
    } finally {
      globalThis.fetch = real;
    }
    expect(seen).toEqual([`${URL}/v1/models`, `${URL}/v1/chat/completions`]);
  });
});
