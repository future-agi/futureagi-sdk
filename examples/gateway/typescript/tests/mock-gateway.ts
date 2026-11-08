import { createServer, type IncomingHttpHeaders, type Server } from "node:http";
import { once } from "node:events";
import { MockAgentCC, mockCompletion } from "@future-agi/sdk/gateway/testing";
import type { ChatCompletionCreateParams } from "@future-agi/sdk/gateway";

export const answer = "Hello from the mock gateway.";
export const key = "mock-personal-gateway-key";
export type Captured = { path: string; headers: IncomingHttpHeaders; body: ChatCompletionCreateParams };

/** A wire bridge: real framework HTTP calls terminate in the SDK's MockAgentCC. */
export async function mockGateway() {
  const mock = new MockAgentCC();
  const calls: Captured[] = [];
  let status = 200;
  const server = createServer(async (request, response) => {
    try {
      let text = "";
      for await (const chunk of request) text += chunk;
      const body = JSON.parse(text) as ChatCompletionCreateParams;
      calls.push({ path: request.url!, headers: request.headers, body });
      if (request.method !== "POST" || request.url !== "/v1/chat/completions") {
        response.writeHead(404).end();
        return;
      }
      if (request.headers.authorization !== `Bearer ${key}` || status !== 200) {
        response.writeHead(status === 200 ? 401 : status, { "Content-Type": "application/json" });
        response.end(JSON.stringify({ error: { message: "Mock gateway refused request", type: "authentication_error" } }));
        return;
      }
      mock.chat.completions.respondWith(mockCompletion(answer, { model: "example-model" }));
      const completion = await mock.chat.completions.create(body);
      if (body.stream) {
        response.writeHead(200, { "Content-Type": "text/event-stream" });
        for (const [delta, finish] of [[{ role: "assistant", content: answer }, null], [{}, "stop"]]) {
          const chunk = { id: completion.id, object: "chat.completion.chunk", created: completion.created,
            model: completion.model, choices: [{ index: 0, delta, finish_reason: finish }] };
          response.write(`data: ${JSON.stringify(chunk)}\n\n`);
        }
        response.end("data: [DONE]\n\n");
      } else {
        response.writeHead(200, { "Content-Type": "application/json" });
        response.end(JSON.stringify(completion));
      }
    } catch {
      response.writeHead(500).end();
    }
  });
  const url = await listen(server);
  return { mock, calls, url, refuse(code: number) { status = code; }, close: () => close(server) };
}

export async function listen(server: Server): Promise<string> {
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  const address = server.address();
  if (!address || typeof address === "string") throw new Error("Expected loopback port");
  return `http://127.0.0.1:${address.port}`;
}

export async function close(server: Server) {
  server.closeAllConnections();
  await new Promise<void>((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
}

/** Explicit fixtures prove the frameworks do not inherit provider credentials or URLs. */
export function configure(url: string): () => void {
  const values: Record<string, string | undefined> = {
    FI_GATEWAY_API_KEY: key, FI_GATEWAY_BASE_URL: `${url}/v1/`, FI_GATEWAY_MODEL: "example-model",
    OPENAI_API_KEY: "unused-provider-key", OPENAI_BASE_URL: "https://provider.invalid/v1",
    OPENAI_ORG_ID: "unused-provider-org", OPENAI_PROJECT_ID: "unused-provider-project",
    FI_API_KEY: undefined, FI_SECRET_KEY: undefined, AGENTCC_API_KEY: undefined, AGENTCC_BASE_URL: undefined,
  };
  const previous = Object.fromEntries(Object.keys(values).map((name) => [name, process.env[name]]));
  for (const [name, value] of Object.entries(values)) {
    if (value === undefined) delete process.env[name]; else process.env[name] = value;
  }
  return () => {
    for (const [name, value] of Object.entries(previous)) {
      if (value === undefined) delete process.env[name]; else process.env[name] = value;
    }
  };
}
