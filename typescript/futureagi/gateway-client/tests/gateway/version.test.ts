/**
 * D-03: the client reports the @future-agi/sdk version it ships in, as
 * futureagi-typescript/<v> in User-Agent and <v> in x-agentcc-sdk-version
 * (1.0.1 sent agentcc-typescript/1.0.1 and 1.0.1). The gateway reads neither
 * header, so this changes nothing on the server.
 */
import { describe, it, expect, jest } from "@jest/globals";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { AgentCC, VERSION } from "../../src/index.js";

const PKG = JSON.parse(readFileSync(join(__dirname, "..", "..", "..", "package.json"), "utf8")) as { name: string; version: string };

describe("D-03 version", () => {
  it("VERSION is the @future-agi/sdk package version", () => {
    expect(PKG.name).toBe("@future-agi/sdk");
    expect(VERSION).toBe(PKG.version);
  });

  it("every request sends User-Agent futureagi-typescript/<v> and x-agentcc-sdk-version <v>", async () => {
    const fetch = jest.fn<typeof globalThis.fetch>(async () => new Response("{}", { status: 200, headers: { "content-type": "application/json" } }));
    await new AgentCC({ apiKey: "k", fetch }).models.list();
    const headers = (fetch.mock.calls[0][1] as RequestInit).headers as Record<string, string>;
    expect(headers["User-Agent"]).toBe(`futureagi-typescript/${PKG.version}`);
    expect(headers["x-agentcc-sdk-version"]).toBe(PKG.version);
  });
});
