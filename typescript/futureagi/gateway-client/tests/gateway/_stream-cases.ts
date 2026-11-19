/**
 * Shared by the stream delta tests (D-11, D-12, D-16): the extra stream
 * answers of the parity fixtures (tests/fixtures/gateway/stream-cases-extra.json), a client that
 * replays one, and a drain that keeps what came before an error.
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { jest } from "@jest/globals";
import { AgentCC } from "../../src/index.js";
import type { ChatCompletionChunk } from "../../src/index.js";

export interface Reply {
  status: number;
  headers: Record<string, string>;
  json?: unknown;
  sse?: string[];
  raw?: string[];
}
const EXTRA = JSON.parse(readFileSync(join(__dirname, "../../../../../tests/fixtures/gateway/stream-cases-extra.json"), "utf8")) as {
  cases: Array<{ name: string; reply: Reply }>;
};
export const CASE = (name: string): Reply => {
  const found = EXTRA.cases.find((c) => c.name === name);
  if (!found) throw new Error(`no stream case ${name} in stream-cases-extra.json`);
  return found.reply;
};

function body(reply: Reply): string {
  if (reply.json !== undefined) return JSON.stringify(reply.json);
  if (reply.raw) return reply.raw.join("");
  return (reply.sse ?? []).map((frame) => `data: ${frame}\n\n`).join("");
}

export function clientFor(reply: Reply) {
  const sent: Array<Record<string, unknown>> = [];
  const fetch = jest.fn<typeof globalThis.fetch>(async (_url, init) => {
    sent.push(JSON.parse(String(init?.body)) as Record<string, unknown>);
    return new Response(body(reply), { status: reply.status, headers: reply.headers });
  });
  return { client: new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, maxRetries: 0 }), sent };
}

export const PARAMS = { model: "gpt-4o-mini", messages: [{ role: "user" as const, content: "hi" }] };

export async function drain<T>(it: AsyncIterable<T>): Promise<{ items: T[]; error: unknown }> {
  const items: T[] = [];
  try {
    for await (const item of it) items.push(item);
  } catch (error) {
    return { items, error };
  }
  return { items, error: null };
}

export function chunk(over: Partial<ChatCompletionChunk>): string {
  return JSON.stringify({ id: "c", object: "chat.completion.chunk", created: 1, model: "m", choices: [], ...over });
}
