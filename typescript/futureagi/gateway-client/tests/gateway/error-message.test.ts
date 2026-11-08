/**
 * D-04: APIStatusError.message is the gateway's error message. The gateway
 * answers `{"error": {"message", "type", "param", "code"}}`; @agentcc/client
 * 1.x read only a top-level `message`, so every gateway error read "Request
 * failed with status N" (golden statuses.*). The envelopes and statuses
 * are the parity fixtures' (tests/fixtures/gateway/responses.json).
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, it, expect, jest } from "@jest/globals";
import { AgentCC, APIStatusError, GuardrailBlockedError, BadRequestError } from "../../src/index.js";

const FIXTURES = JSON.parse(readFileSync(join(__dirname, "../../../../../tests/fixtures/gateway/responses.json"), "utf8")) as {
  error_envelopes: Record<string, unknown>;
  statuses: number[];
};

// The classes with a fixed message of their own keep it (1.0.1 behaviour).
const FIXED: Record<number, string> = {
  246: "Request completed with guardrail warning",
  446: "Request blocked by guardrail",
};

function expectedMessage(status: number, envelope: string): string {
  if (FIXED[status]) return FIXED[status];
  if (envelope === "error_object") return "the gateway said no";
  if (envelope === "error_object_minimal") return "minimal error";
  if (envelope === "top_level_message") return "top-level message only";
  if (envelope === "non_json") return "Unknown error";
  return `Request failed with status ${status}`;
}

async function raised(status: number, body: unknown): Promise<APIStatusError> {
  // An empty answer has no body stream, as on the wire (as the golden recorder sees it): the
  // failed json() then leaves text() readable, which is what 1.0.1 recorded.
  const text = body === "" ? null : typeof body === "string" ? body : JSON.stringify(body);
  const contentType = typeof body === "string" ? "text/plain; charset=utf-8" : "application/json";
  const fetch = jest.fn<typeof globalThis.fetch>(async () => new Response(text, { status, headers: { "content-type": contentType } }));
  const client = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, maxRetries: 0 });
  try {
    await client.chat.completions.create({ model: "m", messages: [{ role: "user", content: "hi" }] });
  } catch (e) {
    return e as APIStatusError;
  }
  throw new Error(`status ${status} did not raise`);
}

const CASES: Array<[number, string]> = [];
for (const status of FIXTURES.statuses) {
  if (status === 246) continue; // a 246 returns the completion; it raises nothing
  for (const envelope of Object.keys(FIXTURES.error_envelopes)) CASES.push([status, envelope]);
}

describe("D-04 error message from the gateway envelope", () => {
  it.each(CASES)("status %i, %s body", async (status, envelope) => {
    const err = await raised(status, FIXTURES.error_envelopes[envelope]);
    expect(err).toBeInstanceOf(APIStatusError);
    expect(err.statusCode).toBe(status);
    expect(err.message).toBe(expectedMessage(status, envelope));
    expect(String(err)).toBe(`${err.name}: ${expectedMessage(status, envelope)}`);
  });

  it("the body stays the whole response body, as in 1.0.1", async () => {
    const err = await raised(400, FIXTURES.error_envelopes.error_object);
    expect(err).toBeInstanceOf(BadRequestError);
    expect(err.body).toEqual(FIXTURES.error_envelopes.error_object);
  });

  it("an envelope whose message is empty or not a string falls back as before", () => {
    const h = new Headers();
    expect(new APIStatusError(400, { error: { message: "" } }, h).message).toBe("Request failed with status 400");
    expect(new APIStatusError(400, { error: { message: 5 } }, h).message).toBe("Request failed with status 400");
    expect(new APIStatusError(400, { error: "flat" }, h).message).toBe("Request failed with status 400");
    expect(new APIStatusError(400, { error: { message: "" }, message: "top" }, h).message).toBe("top");
    expect(new APIStatusError(400, null, h).message).toBe("Request failed with status 400");
    expect(new APIStatusError(400, [1], h).message).toBe("Request failed with status 400");
  });

  it("an explicit message still wins, and the guardrail block keeps its own", () => {
    const h = new Headers();
    expect(new APIStatusError(400, { error: { message: "gw" } }, h, "explicit").message).toBe("explicit");
    expect(new GuardrailBlockedError({ error: { message: "gw" } }, h).message).toBe("Request blocked by guardrail");
  });
});
