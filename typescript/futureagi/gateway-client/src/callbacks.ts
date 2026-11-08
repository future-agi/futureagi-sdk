/**
 * Callback system for request lifecycle hooks.
 *
 * @module
 */

import type { AgentCCMetadata } from "./types/shared.js";
import type { Session } from "./session.js";

// ---------------------------------------------------------------------------
// Data types passed to callbacks
// ---------------------------------------------------------------------------

export interface CallbackRequest {
  method: string;
  url: string;
  headers: Record<string, string>;
  body: unknown;
}

export interface CallbackResponse {
  statusCode: number;
  headers: Record<string, string>;
  agentcc: AgentCCMetadata;
  body: unknown;
}

// ---------------------------------------------------------------------------
// Abstract callback handler
// ---------------------------------------------------------------------------

/**
 * Abstract class with the 10 lifecycle hooks the client calls. Override the
 * ones you need. All methods are no-ops by default.
 *
 * @agentcc/client 1.x also declared onStreamStart, onStreamChunk, onStreamEnd,
 * onBudgetWarning and onSessionEnd, which no code path ever called; they stay
 * in the @agentcc/client 2.x compatibility package only.
 */
export abstract class CallbackHandler {
  onRequestStart(_request: CallbackRequest): void | Promise<void> {}
  onRequestEnd(_request: CallbackRequest, _response: CallbackResponse): void | Promise<void> {}
  onError(_request: CallbackRequest, _error: Error): void | Promise<void> {}
  onRetry(_request: CallbackRequest, _error: Error, _attempt: number, _delay: number): void | Promise<void> {}
  onGuardrailWarning(_request: CallbackRequest, _response: CallbackResponse): void | Promise<void> {}
  onGuardrailBlock(_request: CallbackRequest, _error: Error): void | Promise<void> {}
  onCacheHit(_request: CallbackRequest, _response: CallbackResponse, _cacheType: string): void | Promise<void> {}
  onCostUpdate(_request: CallbackRequest, _cost: number, _cumulativeCost: number): void | Promise<void> {}
  onFallback(_request: CallbackRequest, _originalModel: string, _fallbackModel: string, _reason: string): void | Promise<void> {}
  onSessionStart(_session: Session): void | Promise<void> {}
}

// ---------------------------------------------------------------------------
// Utility: invoke callbacks safely (fire-and-forget, never propagate errors)
// ---------------------------------------------------------------------------

export async function invokeCallbacks(
  callbacks: CallbackHandler[],
  method: keyof CallbackHandler,
  ...args: unknown[]
): Promise<void> {
  for (const cb of callbacks) {
    try {
      const fn = cb[method] as (...a: unknown[]) => void | Promise<void>;
      await fn.apply(cb, args);
    } catch {
      // Callback errors are swallowed — never break the request path
    }
  }
}
