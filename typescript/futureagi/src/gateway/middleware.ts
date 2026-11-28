// ---------------------------------------------------------------------------
// Middleware / Interceptor Pattern
// ---------------------------------------------------------------------------

import type { AgentCCMetadata } from "./types/shared";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface MiddlewareContext {
  method: string;
  path: string;
  body: Record<string, unknown> | null;
  headers: Record<string, string>;
  model?: string;
}

export interface MiddlewareResult {
  data: unknown;
  response: Response;
  statusCode: number;
  latencyMs: number;
  agentcc: AgentCCMetadata;
}

export type NextFn = (
  ctx: MiddlewareContext,
) => Promise<MiddlewareResult>;

export type Middleware = {
  name: string;
  onRequest: (
    ctx: MiddlewareContext,
    next: NextFn,
  ) => Promise<MiddlewareResult>;
};

// ---------------------------------------------------------------------------
// Factory
// ---------------------------------------------------------------------------

/**
 * Create a named middleware from a request handler function.
 *
 * @example
 * ```typescript
 * const logger = createMiddleware({
 *   name: "logger",
 *   async onRequest(ctx, next) {
 *     console.log(`→ ${ctx.method} ${ctx.path}`);
 *     const result = await next(ctx);
 *     console.log(`← ${result.statusCode}`);
 *     return result;
 *   },
 * });
 * client.use(logger);
 * ```
 */
export function createMiddleware(opts: {
  name: string;
  onRequest: (
    ctx: MiddlewareContext,
    next: NextFn,
  ) => Promise<MiddlewareResult>;
}): Middleware {
  return {
    name: opts.name,
    onRequest: opts.onRequest,
  };
}

// ---------------------------------------------------------------------------
// Composition
// ---------------------------------------------------------------------------

/**
 * Compose an array of middlewares into a single handler chain.
 * First middleware added is the outermost (runs first on request, last on response).
 *
 * @param middlewares - Array of middleware to compose
 * @param handler - The innermost handler (actual HTTP request)
 * @returns A composed NextFn that runs all middlewares then the handler
 */
export function composeMiddlewares(
  middlewares: Middleware[],
  handler: NextFn,
): NextFn {
  // Build from inside out: handler → last middleware → ... → first middleware
  let composed = handler;

  for (let i = middlewares.length - 1; i >= 0; i--) {
    const mw = middlewares[i];
    const next = composed;
    composed = (ctx: MiddlewareContext) => mw.onRequest(ctx, next);
  }

  return composed;
}
