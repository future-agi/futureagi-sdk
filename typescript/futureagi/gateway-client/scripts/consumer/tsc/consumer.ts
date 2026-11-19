// A TypeScript consumer of every gateway subpath, compiled from the
// installed tarball under moduleResolution node10, node16 (as .mts and .cts)
// and bundler (pack-checks.sh copies it to each). The @ts-expect-error lines
// fail the compile if a subpath's types resolve to any or go missing.
import { AgentCC, StreamError, createHeaders, openaiOptions, aiSdkProviderSettings } from "@future-agi/sdk/gateway";
import type { ChatCompletion, ChatCompletionChunk, ClientOptions, AgentCCMetadata } from "@future-agi/sdk/gateway";
import { MockAgentCC, mockCompletion } from "@future-agi/sdk/gateway/testing";
import { agentccMiddleware } from "@future-agi/sdk/gateway/express";
import { createAgentCCClient, streamResponse } from "@future-agi/sdk/gateway/nextjs";
import { AgentCCProvider, useAgentCCChat } from "@future-agi/sdk/gateway/react";
import type { UseAgentCCChatReturn } from "@future-agi/sdk/gateway/react";

const opts: ClientOptions = { apiKey: "sk-test", baseUrl: "http://127.0.0.1:9" };
const client: AgentCC = new AgentCC(opts);
export const done: Promise<ChatCompletion> = client.chat.completions.create({ model: "m", messages: [{ role: "user", content: "hi" }] });
export async function first(): Promise<ChatCompletionChunk | undefined> {
  for await (const chunk of await client.chat.completions.create({ model: "m", messages: [], stream: true })) return chunk;
  return undefined;
}
export const isStreamError = (e: unknown): e is StreamError => e instanceof StreamError && typeof e.code !== "number";
export const meta = (m: AgentCCMetadata): number | null => m.cost;
export const headers: Record<string, string> = createHeaders({ sessionId: "s1" });
export const forOpenAI: { apiKey: string; baseURL: string } = openaiOptions({ apiKey: "sk-test", baseUrl: "http://127.0.0.1:9" });
export const forAiSdk: { apiKey: string; baseURL: string } = aiSdkProviderSettings({ apiKey: "sk-test", baseURL: "http://127.0.0.1:9" });
export const mock: MockAgentCC = new MockAgentCC();
export const completion: ChatCompletion = mockCompletion("hi");
export const mw = agentccMiddleware({ apiKey: "k" });
export const fromEnv: AgentCC = createAgentCCClient();
export const sse: (s: Parameters<typeof streamResponse>[0]) => Response = (s) => streamResponse(s);
export const provider = AgentCCProvider;
export type Chat = UseAgentCCChatReturn["messages"];
export const hook: typeof useAgentCCChat = useAgentCCChat;

// @ts-expect-error a method the client does not have is a type error (the types are not any)
client.chat.completions.nope();
// @ts-expect-error a wrong option type is a type error
new AgentCC({ timeout: "slow" });
