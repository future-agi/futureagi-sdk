import { describe, expect, it } from "@jest/globals";
import { AgentCC, AgentCCError } from "../src/index.js";

type RequestOptions = Parameters<AgentCC["request"]>[0];

describe("public request preparation", () => {
  it("is an identity unless overridden", () => {
    const client = new AgentCC({ apiKey: "test-personal", baseUrl: "http://localhost:8080" });
    const options = { method: "POST", path: "/test", body: { model: "test" } };
    expect(client.prepareRequest(options)).toBe(options);
    expect(client.prepareRequest(options, "build")).toBe(options);
  });

  it("prepares all public request forms and dry runs without private transport access", async () => {
    const modes: string[] = [];
    const bodies: unknown[] = [];
    class Prepared extends AgentCC {
      override prepareRequest(options: RequestOptions, mode: "send" | "build" = "send"): RequestOptions {
        modes.push(mode);
        return { ...options, body: { marker: mode } };
      }
    }
    const client = new Prepared({ apiKey: "test-personal", baseUrl: "http://localhost:8080", maxRetries: 0,
      fetch: async (_url, init) => {
        bodies.push(JSON.parse(String(init?.body)));
        return new Response("{}", { headers: { "content-type": "application/json" } });
      },
    });
    const options = { method: "POST", path: "/test" };
    expect(client.buildRequest(options).body).toEqual({ marker: "build" });
    await client.request(options);
    await client.requestWithResponse(options);
    await client.requestRaw(options);
    await client.requestStream(options);
    expect(modes).toEqual(["build", "send", "send", "send", "send"]);
    expect(bodies).toEqual(Array(4).fill({ marker: "send" }));
  });

  it("propagates a typed refusal before transport", async () => {
    let calls = 0;
    class Refused extends AgentCC {
      override prepareRequest(_options: RequestOptions): never {
        throw new AgentCCError("refused before transport");
      }
    }
    const client = new Refused({ apiKey: "test-personal", baseUrl: "http://localhost:8080",
      fetch: async () => { calls++; return new Response("{}"); },
    });
    await expect(client.request({ method: "GET", path: "/test" })).rejects.toBeInstanceOf(AgentCCError);
    expect(calls).toBe(0);
  });
});
