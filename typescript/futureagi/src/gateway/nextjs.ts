// ---------------------------------------------------------------------------
// Next.js Integration Helpers — Server-side utilities for App Router
// ---------------------------------------------------------------------------

import { AgentCC } from "./client";
import type { ClientOptions } from "./base-client";
import type { StreamManager } from "./streaming";

// ---------------------------------------------------------------------------
// Singleton client
// ---------------------------------------------------------------------------

let _singleton: AgentCC | null = null;

/**
 * Get or create a singleton AgentCC client.
 * Reads `AGENTCC_API_KEY` and `AGENTCC_BASE_URL` from environment by default.
 *
 * @example
 * ```typescript
 * // app/api/chat/route.ts
 * import { createAgentCCClient } from "@future-agi/sdk/gateway/nextjs";
 *
 * export async function POST(req: Request) {
 *   const client = createAgentCCClient();
 *   const { messages } = await req.json();
 *   const result = await client.chat.completions.create({
 *     model: "gpt-4o",
 *     messages,
 *   });
 *   return Response.json(result);
 * }
 * ```
 */
export function createAgentCCClient(opts?: ClientOptions): AgentCC {
  if (!_singleton) {
    _singleton = new AgentCC(opts);
  }
  return _singleton;
}

/**
 * Reset the singleton (useful for testing).
 */
export function resetAgentCCClient(): void {
  _singleton = null;
}

// ---------------------------------------------------------------------------
// SSE Stream Response
// ---------------------------------------------------------------------------

/**
 * Convert a StreamManager into a streaming `Response` suitable for Next.js
 * App Router route handlers. Produces Server-Sent Events (SSE) format.
 *
 * @example
 * ```typescript
 * // app/api/chat/route.ts
 * import { createAgentCCClient, streamResponse } from "@future-agi/sdk/gateway/nextjs";
 *
 * export async function POST(req: Request) {
 *   const client = createAgentCCClient();
 *   const { messages } = await req.json();
 *   const stream = await client.chat.completions.stream({
 *     model: "gpt-4o",
 *     messages,
 *   });
 *   return streamResponse(stream);
 * }
 * ```
 */
export function streamResponse(
  stream: StreamManager,
  opts?: { headers?: Record<string, string> },
): Response {
  const encoder = new TextEncoder();

  const readable = new ReadableStream({
    async start(controller) {
      try {
        for await (const chunk of stream) {
          const data = `data: ${JSON.stringify(chunk)}\n\n`;
          controller.enqueue(encoder.encode(data));
        }
        controller.enqueue(encoder.encode("data: [DONE]\n\n"));
      } catch (err) {
        const errorData = `data: ${JSON.stringify({
          error: { message: (err as Error).message },
        })}\n\n`;
        controller.enqueue(encoder.encode(errorData));
      } finally {
        controller.close();
      }
    },
  });

  return new Response(readable, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
      ...opts?.headers,
    },
  });
}
