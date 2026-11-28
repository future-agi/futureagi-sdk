// ---------------------------------------------------------------------------
// Pre-Call Rules — client-side safety net for request validation
// ---------------------------------------------------------------------------

import { AgentCCError } from "./errors";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface PreCallRuleInput {
  /** The model being requested (if available in the body). */
  model?: string;
  /** The request path, e.g. "/v1/chat/completions". */
  path: string;
  /** The request body (or null for GET requests). */
  body: Record<string, unknown> | null;
}

export interface PreCallRuleResult {
  /** If false, the request is blocked. */
  allow: boolean;
  /** Human-readable reason for blocking (when allow is false). */
  reason?: string;
}

/**
 * A pre-call rule function. Evaluated synchronously before every request.
 * Return `{ allow: false, reason }` to block the request.
 */
export type PreCallRule = (input: PreCallRuleInput) => PreCallRuleResult;

// ---------------------------------------------------------------------------
// Evaluator
// ---------------------------------------------------------------------------

/**
 * Evaluate all pre-call rules. Throws AgentCCError on the first rule that
 * returns `allow: false`.
 */
export function evaluatePreCallRules(
  rules: PreCallRule[],
  input: PreCallRuleInput,
): void {
  for (const rule of rules) {
    const result = rule(input);
    if (!result.allow) {
      throw new AgentCCError(
        `Pre-call rule blocked request: ${result.reason ?? "no reason given"}`,
      );
    }
  }
}

// ---------------------------------------------------------------------------
// Built-in rule factories
// ---------------------------------------------------------------------------

/**
 * Create a rule that only allows specific models.
 *
 * @example
 * ```typescript
 * const client = new AgentCC({
 *   preCallRules: [allowModels(["gpt-4o", "gpt-4o-mini"])],
 * });
 * ```
 */
export function allowModels(models: string[]): PreCallRule {
  const allowed = new Set(models);
  return (input) => {
    if (!input.model) return { allow: true };
    if (allowed.has(input.model)) return { allow: true };
    return {
      allow: false,
      reason: `Model "${input.model}" is not in the allowed list: [${models.join(", ")}]`,
    };
  };
}

/**
 * Create a rule that blocks specific models.
 *
 * @example
 * ```typescript
 * const client = new AgentCC({
 *   preCallRules: [blockModels(["o1-preview"])],
 * });
 * ```
 */
export function blockModels(models: string[]): PreCallRule {
  const blocked = new Set(models);
  return (input) => {
    if (!input.model) return { allow: true };
    if (blocked.has(input.model)) {
      return {
        allow: false,
        reason: `Model "${input.model}" is blocked`,
      };
    }
    return { allow: true };
  };
}

/**
 * Create a rule that requires a session ID header.
 */
export function requireSessionId(): PreCallRule {
  return (input) => {
    const body = input.body;
    if (body && body.session_id) return { allow: true };
    return {
      allow: false,
      reason: "A session_id is required for all requests",
    };
  };
}
