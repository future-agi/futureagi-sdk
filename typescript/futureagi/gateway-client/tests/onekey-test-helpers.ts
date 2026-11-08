import { expect, jest } from "@jest/globals";
import * as gateway from "../src/index.js";
import type { ClientOptions } from "../src/index.js";

export const HEADERS = {
  "retry-after": "2",
  "x-agentcc-request-id": "req-refusal",
  "x-ratelimit-limit-requests": "100",
  "x-ratelimit-remaining-requests": "0",
  "x-ratelimit-reset-requests": "12",
};
export const IN_FLIGHT = { limit_source: "agentcc_in_flight", remedy_hint: "retry" };
export const FULL = {
  required_usd: 0.02, available_usd: 0, limit_source: "credits",
  remedy_hint: "fund", scope: "org", resets_at: "2026-12-01T00:00:00Z",
  reason: "limit reached", extra: { kept: true },
};
export const FIELDS = {
  requiredUsd: "required_usd", availableUsd: "available_usd", limitSource: "limit_source",
  remedyHint: "remedy_hint", scope: "scope", resetsAt: "resets_at", reason: "reason",
} as const;

export function envelope(code: unknown, metadata: unknown = FULL, type: unknown = "rate_limit_error") {
  return { error: { message: "refused", code, type, metadata } };
}

export function errorClass(name: string): new (body: unknown, headers: Headers) => gateway.APIStatusError {
  const cls = (gateway as unknown as Record<string, unknown>)[name];
  expect(typeof cls).toBe("function");
  return cls as new (body: unknown, headers: Headers) => gateway.APIStatusError;
}

export function setup(status: number, body: unknown, options: ClientOptions = {}) {
  const fetch = jest.fn<typeof globalThis.fetch>(async () =>
    new Response(JSON.stringify(body), { status, headers: HEADERS }));
  const client = new gateway.AgentCC({ apiKey: "test-only", baseUrl: "https://gateway.test", ...options, fetch });
  return { client, fetch };
}

export type RequestPath = "json" | "raw" | "stream";
export function send(client: gateway.AgentCC, path: RequestPath = "raw"): Promise<unknown> {
  const params = { model: "example/model", messages: [{ role: "user" as const, content: "hello" }] };
  if (path === "stream") return client.chat.completions.create({ ...params, stream: true });
  if (path === "json") return client.request({ method: "POST", path: "/v1/chat/completions", body: params });
  return client.chat.completions.create(params);
}

export async function refusal(promise: Promise<unknown>): Promise<gateway.APIStatusError> {
  try {
    await promise;
  } catch (error) {
    expect(error).toBeInstanceOf(gateway.APIStatusError);
    return error as gateway.APIStatusError;
  }
  throw new Error("Expected a refusal");
}

export function details(error: gateway.APIStatusError): Record<string, unknown> {
  return error as unknown as Record<string, unknown>;
}
