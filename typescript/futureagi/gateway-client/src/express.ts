// ---------------------------------------------------------------------------
// Express Middleware — Attaches a session-scoped AgentCC client to each request
// ---------------------------------------------------------------------------

import { AgentCC } from "./client.js";
import type { ClientOptions } from "./base-client.js";
import type { GatewayConfig } from "./gateway-config.js";
import type { CallbackHandler } from "./callbacks.js";
import type { Session } from "./session.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface AgentCCMiddlewareOptions {
  apiKey?: string;
  baseUrl?: string;
  config?: GatewayConfig;
  callbacks?: CallbackHandler[];
  /** Header to extract session ID from. Default: "x-request-id". */
  sessionFromHeader?: string;
  /** Additional client options. */
  clientOptions?: Partial<ClientOptions>;
}

// Express-compatible types (duck-typed to avoid Express dependency)
interface ExpressRequest {
  method: string;
  path: string;
  headers: Record<string, string | string[] | undefined>;
  agentcc?: AgentCC;
  agentccSession?: Session;
}

interface ExpressResponse {
  on(event: string, listener: () => void): void;
}

type ExpressNextFn = (err?: unknown) => void;

// ---------------------------------------------------------------------------
// Middleware factory
// ---------------------------------------------------------------------------

/**
 * Express middleware that attaches a session-scoped AgentCC client to `req.agentcc`.
 *
 * @example
 * ```typescript
 * import express from "express";
 * import { agentccMiddleware } from "@future-agi/sdk/gateway/express";
 *
 * const app = express();
 * app.use(agentccMiddleware({ apiKey: "sk-..." }));
 *
 * app.post("/api/chat", async (req, res) => {
 *   const result = await req.agentcc.chat.completions.create({
 *     model: "gpt-4o",
 *     messages: req.body.messages,
 *   });
 *   res.json(result);
 * });
 * ```
 */
export function agentccMiddleware(
  opts: AgentCCMiddlewareOptions,
): (req: ExpressRequest, res: ExpressResponse, next: ExpressNextFn) => void {
  const baseClient = new AgentCC({
    apiKey: opts.apiKey,
    baseUrl: opts.baseUrl,
    config: opts.config,
    callbacks: opts.callbacks,
    ...opts.clientOptions,
  });

  const sessionHeader = opts.sessionFromHeader ?? "x-request-id";

  return (req: ExpressRequest, res: ExpressResponse, next: ExpressNextFn) => {
    // Extract session ID from header or generate one
    const headerVal = req.headers[sessionHeader];
    const sessionId =
      (typeof headerVal === "string" ? headerVal : undefined) ??
      generateId();

    // Extract traceparent for propagation
    const traceparentHeader = req.headers["traceparent"];
    const traceparent =
      typeof traceparentHeader === "string" ? traceparentHeader : undefined;

    // Create session-scoped client
    const { client, session } = baseClient.session({
      sessionId,
      name: `${req.method} ${req.path}`,
    });

    // If traceparent is present, create a client with trace context
    const agentccClient = traceparent
      ? client.withOptions({
          defaultHeaders: {
            ...client["_defaultHeaders"],
            traceparent,
            "x-agentcc-trace-id": traceparent.split("-")[1] ?? sessionId,
          },
        })
      : client;

    req.agentcc = agentccClient;
    req.agentccSession = session;

    next();
  };
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function generateId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `req-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}
