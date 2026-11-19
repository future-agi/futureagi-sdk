/**
 * D-14: FI_GATEWAY_API_KEY / FI_GATEWAY_BASE_URL come first, AGENTCC_* stay
 * as aliases, and the Future AGI key pair is never sent. fi.gateway (Python)
 * resolves in the same order with the same guard; the parity env matrix
 * (golden env.*, tests/fixtures/gateway/golden) pins the 1.0.1 side.
 */
import { describe, it, expect, jest, beforeEach, afterEach } from "@jest/globals";
import { AgentCC, AgentCCError } from "../../src/index.js";
import { createAgentCCClient, resetAgentCCClient } from "../../src/nextjs.js";
import { fromEnv, resolveApiKey, resolveBaseUrl, KEY_ENV, URL_ENV } from "../../src/env.js";

function okFetch() {
  const headersAtCall: Record<string, string>[] = [];
  const fetch = jest.fn<typeof globalThis.fetch>(async (_url, init) => {
    // Observe the wire before the transport scrubs its attempt-owned headers.
    headersAtCall.push({ ...(init?.headers as Record<string, string>) });
    return new Response(JSON.stringify({ object: "list", data: [] }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  });
  return Object.assign(fetch, { headersAtCall });
}

function sent(fetch: ReturnType<typeof okFetch>, call = 0): { url: string; headers: Record<string, string> } {
  const [url] = fetch.mock.calls[call] as [string, RequestInit];
  return { url, headers: fetch.headersAtCall[call] };
}

let saved: NodeJS.ProcessEnv;
const spyWarn = () => jest.spyOn(console, "warn").mockImplementation(() => {});
let warn: ReturnType<typeof spyWarn>;
beforeEach(() => {
  saved = { ...process.env };
  for (const k of Object.keys(process.env)) if (/^(AGENTCC_|FI_|OPENAI_)/.test(k)) delete process.env[k];
  warn = spyWarn();
});
afterEach(() => {
  process.env = saved;
  warn.mockRestore();
});

describe("D-14 key order", () => {
  it("the apiKey option wins over both variables", async () => {
    process.env.FI_GATEWAY_API_KEY = "fi-gw";
    process.env.AGENTCC_API_KEY = "agentcc";
    const fetch = okFetch();
    await new AgentCC({ apiKey: "arg", baseUrl: "http://gw.test", fetch }).models.list();
    expect(sent(fetch).headers.Authorization).toBe("Bearer arg");
  });

  it("FI_GATEWAY_API_KEY is read when no option is given", async () => {
    process.env.FI_GATEWAY_API_KEY = "fi-gw";
    const fetch = okFetch();
    await new AgentCC({ baseUrl: "http://gw.test", fetch }).models.list();
    expect(sent(fetch).headers.Authorization).toBe("Bearer fi-gw");
  });

  it("AGENTCC_API_KEY is still read (alias)", async () => {
    process.env.AGENTCC_API_KEY = "agentcc";
    const fetch = okFetch();
    await new AgentCC({ baseUrl: "http://gw.test", fetch }).models.list();
    expect(sent(fetch).headers.Authorization).toBe("Bearer agentcc");
  });

  it("an empty value falls through to the next source, as 1.x's || did", async () => {
    process.env.FI_GATEWAY_API_KEY = "";
    process.env.AGENTCC_API_KEY = "agentcc";
    const fetch = okFetch();
    await new AgentCC({ apiKey: "", baseUrl: "http://gw.test", fetch }).models.list();
    expect(sent(fetch).headers.Authorization).toBe("Bearer agentcc");
    expect(warn).not.toHaveBeenCalled();
  });

  it("with no key anywhere no Authorization header is sent (1.x behaviour)", async () => {
    const fetch = okFetch();
    await new AgentCC({ baseUrl: "http://gw.test", fetch }).models.list();
    expect(Object.keys(sent(fetch).headers).map((h) => h.toLowerCase())).not.toContain("authorization");
  });

  it("both variables set to different values: FI_GATEWAY_API_KEY wins and one warning names the two, never the values", async () => {
    process.env.FI_GATEWAY_API_KEY = "fi-gw-secret-value";
    process.env.AGENTCC_API_KEY = "agentcc-secret-value";
    const fetch = okFetch();
    await new AgentCC({ baseUrl: "http://gw.test", fetch }).models.list();
    expect(sent(fetch).headers.Authorization).toBe("Bearer fi-gw-secret-value");
    expect(warn).toHaveBeenCalledTimes(1);
    const line = String(warn.mock.calls[0][0]);
    expect(line).toBe("FI_GATEWAY_API_KEY and AGENTCC_API_KEY are both set to different values; using FI_GATEWAY_API_KEY");
    expect(line).not.toContain("secret-value");
  });

  it("both variables set to the same value: no warning", () => {
    process.env.FI_GATEWAY_API_KEY = "same";
    process.env.AGENTCC_API_KEY = "same";
    new AgentCC({ baseUrl: "http://gw.test" });
    expect(warn).not.toHaveBeenCalled();
  });

  it("each resolution warns (no process-wide once flag, as fi.gateway)", () => {
    process.env.FI_GATEWAY_API_KEY = "a";
    process.env.AGENTCC_API_KEY = "b";
    new AgentCC({ baseUrl: "http://gw.test" });
    new AgentCC({ baseUrl: "http://gw.test" });
    expect(warn).toHaveBeenCalledTimes(2);
  });

  it("the option given: the variables are not read, so no warning", () => {
    process.env.FI_GATEWAY_API_KEY = "a";
    process.env.AGENTCC_API_KEY = "b";
    new AgentCC({ apiKey: "arg", baseUrl: "http://gw.test" });
    expect(warn).not.toHaveBeenCalled();
  });
});

describe("D-14 base URL order", () => {
  it("baseUrl option, then FI_GATEWAY_BASE_URL, then AGENTCC_BASE_URL, then http://localhost:8090", async () => {
    const urls: string[] = [];
    const run = async (opts: { baseUrl?: string }) => {
      const fetch = okFetch();
      await new AgentCC({ apiKey: "k", fetch, ...opts }).models.list();
      urls.push(sent(fetch).url);
    };
    await run({});
    process.env.AGENTCC_BASE_URL = "http://agentcc.test/v1";
    await run({});
    process.env.FI_GATEWAY_BASE_URL = "http://fi-gw.test/";
    await run({});
    await run({ baseUrl: "http://arg.test" });
    expect(urls).toEqual([
      "http://localhost:8090/v1/models",
      "http://agentcc.test/v1/models",
      "http://fi-gw.test/v1/models",
      "http://arg.test/v1/models",
    ]);
  });

  it("both URL variables set to different values: FI_GATEWAY_BASE_URL wins and one warning names the two", () => {
    process.env.FI_GATEWAY_BASE_URL = "http://fi-gw.test";
    process.env.AGENTCC_BASE_URL = "http://agentcc.test";
    const client = new AgentCC({ apiKey: "k" });
    expect(client.chat.completions.dryRun({ model: "m", messages: [] }).url).toBe("http://fi-gw.test/v1/chat/completions");
    expect(warn).toHaveBeenCalledTimes(1);
    expect(String(warn.mock.calls[0][0])).toBe(
      "FI_GATEWAY_BASE_URL and AGENTCC_BASE_URL are both set to different values; using FI_GATEWAY_BASE_URL",
    );
  });

  it("an empty FI_GATEWAY_BASE_URL falls through to AGENTCC_BASE_URL", () => {
    process.env.FI_GATEWAY_BASE_URL = "";
    process.env.AGENTCC_BASE_URL = "http://agentcc.test";
    expect(resolveBaseUrl(undefined)).toBe("http://agentcc.test");
  });

  it("AGENTCC_GATEWAY_URL (the S-bucket constant's variable) is not read by the client, as in 1.x", () => {
    process.env.AGENTCC_GATEWAY_URL = "http://other.test";
    expect(resolveBaseUrl(undefined)).toBe("http://localhost:8090");
    delete process.env.AGENTCC_GATEWAY_URL;
  });

  it("the name lists are the documented order", () => {
    expect([...KEY_ENV]).toEqual(["FI_GATEWAY_API_KEY", "AGENTCC_API_KEY"]);
    expect([...URL_ENV]).toEqual(["FI_GATEWAY_BASE_URL", "AGENTCC_BASE_URL"]);
    expect(fromEnv(["FI_GATEWAY_API_KEY"])).toBe("");
  });
});

describe("D-14 the Future AGI key pair is never sent", () => {
  it.each(["FI_API_KEY", "FI_SECRET_KEY"])("a gateway key equal to %s from the environment raises AgentCCError naming the variable, not the value", (name) => {
    process.env[name] = "fi-pair-value-123";
    let caught: unknown;
    try {
      new AgentCC({ apiKey: "fi-pair-value-123", baseUrl: "http://gw.test" });
    } catch (e) {
      caught = e;
    }
    expect(caught).toBeInstanceOf(AgentCCError);
    const message = (caught as Error).message;
    expect(message).toContain(name);
    expect(message).toContain("FI_GATEWAY_API_KEY");
    expect(message).toContain("Agent Command Center");
    expect(message).not.toContain("fi-pair-value-123");
  });

  it("the guard applies to a key from FI_GATEWAY_API_KEY and from AGENTCC_API_KEY too", () => {
    process.env.FI_API_KEY = "pair";
    process.env.FI_GATEWAY_API_KEY = "pair";
    expect(() => new AgentCC({ baseUrl: "http://gw.test" })).toThrow(AgentCCError);
    delete process.env.FI_GATEWAY_API_KEY;
    process.env.AGENTCC_API_KEY = "pair";
    expect(() => new AgentCC({ baseUrl: "http://gw.test" })).toThrow(AgentCCError);
  });

  it("the nextjs singleton and every helper that builds a client get the same guard", () => {
    process.env.FI_SECRET_KEY = "pair";
    process.env.FI_GATEWAY_API_KEY = "pair";
    resetAgentCCClient();
    try {
      expect(() => createAgentCCClient()).toThrow(AgentCCError);
    } finally {
      resetAgentCCClient();
    }
  });

  it("FI_API_KEY, FI_SECRET_KEY and FI_PLATFORM_TOKEN are never read as the gateway key", () => {
    process.env.FI_API_KEY = "fi-api";
    process.env.FI_SECRET_KEY = "fi-secret";
    process.env.FI_PLATFORM_TOKEN = "fi-token";
    expect(resolveApiKey(undefined, (m) => new AgentCCError(m))).toBe("");
  });

  it("wire: with every FI_* and OPENAI_* variable set, no FI, workspace, Omega or OpenAI account header leaves the client", async () => {
    Object.assign(process.env, {
      FI_API_KEY: "fi-api",
      FI_SECRET_KEY: "fi-secret",
      FI_PLATFORM_TOKEN: "fi-token",
      FI_BASE_URL: "http://fi.test",
      FI_PLATFORM_BASE_URL: "http://fi-platform.test",
      FI_WORKSPACE_ID: "ws",
      FI_ORGANIZATION_ID: "org",
      FI_GATEWAY_API_KEY: "gw-key",
      FI_GATEWAY_BASE_URL: "http://gw.test",
      OPENAI_API_KEY: "sk-openai",
      OPENAI_ORG_ID: "org-openai",
      OPENAI_ORGANIZATION: "org-openai",
      OPENAI_PROJECT_ID: "proj-openai",
      OPENAI_BASE_URL: "http://openai.test",
    });
    const fetch = okFetch();
    const client = new AgentCC({ fetch });
    await client.models.list();
    await client.chat.completions.create({ model: "m", messages: [{ role: "user", content: "hi" }] }).catch(() => {});
    for (let i = 0; i < fetch.mock.calls.length; i++) {
      const { url, headers } = sent(fetch, i);
      expect(url.startsWith("http://gw.test/v1/")).toBe(true);
      const names = Object.keys(headers).map((h) => h.toLowerCase());
      for (const name of names) {
        expect(name).not.toMatch(/^(x-api-key|x-secret-key|x-workspace-|x-organization-id|x-omega-|openai-organization|openai-project)/);
      }
      expect(headers.Authorization).toBe("Bearer gw-key");
      expect(JSON.stringify(headers)).not.toMatch(/fi-api|fi-secret|fi-token|sk-openai|org-openai|proj-openai/);
    }
    expect(fetch).toHaveBeenCalled();
  });
});
