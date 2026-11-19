import { evidenceFromHeaders, gatewayRequestIdPresence, parseGatewayEvidence } from "./gateway-evidence.js";
import type { GatewayEvidence } from "./gateway-evidence.js";

/** Gateway refusals are keyed by HTTP status and code, never type or message prose. */
type RefusalClass = "InsufficientCreditsError" | "AgentBudgetExhaustedError" | "BudgetExceededError"
  | "RateLimitError" | "ServiceUnavailableError" | "PermissionDeniedError" | "FutureAGICreditsOffError"
  | "AuthenticationError" | "APIStatusError" | "BadRequestError" | "NotFoundError"
  | "UnprocessableEntityError" | "GatewayTimeoutError";

/** Canonical refusal category, independent of the catch-compatible status class. */
export type RefusalCategory = "out_of_credits" | "agent_budget" | "budget_limit" | "permission"
  | "invalid_key" | "generic" | "rate_limit" | "billing_unavailable";

interface Refusal {
  readonly name: RefusalClass;
  /** Standard backoff, terminal, one in-flight replay, or positive-header-only. */
  readonly retry: "status" | "never" | "once" | "after";
}
interface RefusalDetails extends Refusal {
  readonly category: RefusalCategory;
  readonly remedy: string | null;
}

export const CREDITS_OFF_REMEDY = "An organization Owner or Admin uses the \"Turn on Future AGI credits\" control on the Gateway Models page, or adds their own provider key on the Gateway Providers page.";

// Contract rows are normative client mappings, not deployment certification.
const REFUSALS = new Map<string, RefusalDetails>([
  ["403:managed_model_unpriced", { name: "PermissionDeniedError", retry: "never", category: "permission", remedy: "Choose a priced model or use your own provider key." }],
  ["400:managed_model_ambiguous", { name: "BadRequestError", retry: "never", category: "generic", remedy: "Choose a provider-prefixed candidate ID or use the organization's own provider key for a candidate." }],
  ["400:managed_resource_unsupported", { name: "BadRequestError", retry: "never", category: "generic", remedy: "Use a supported managed request shape or your own provider key." }],
  ["402:managed_credits_exhausted", { name: "InsufficientCreditsError", retry: "never", category: "out_of_credits", remedy: "Add credit on Settings Billing; on a grant-only install ask its operator to grant credit; alternatively use your own provider key on Gateway Providers." }],
  ["402:managed_credits_insufficient", { name: "InsufficientCreditsError", retry: "never", category: "out_of_credits", remedy: "For in-flight holds, wait for Retry-After; otherwise add credit, lower max_tokens or use your own provider key." }],
  ["402:agent_budget_exhausted", { name: "AgentBudgetExhaustedError", retry: "never", category: "agent_budget", remedy: "Raise the run budget or start a new run; a call-only budget may also be lowered by reducing max_tokens or choosing a cheaper model. Administrative ceilings need an authorized policy change." }],
  ["429:budget_exceeded", { name: "BudgetExceededError", retry: "never", category: "budget_limit", remedy: "An administrator raises the binding budget, or wait for its period to reset; never automatically retry the same refusal." }],
  ["429:org_budget_exceeded", { name: "BudgetExceededError", retry: "never", category: "budget_limit", remedy: "Raise the binding budget/daily cap through an authorized administrator, or wait for its reset; no automatic retry." }],
  ["429:managed_spend_velocity", { name: "RateLimitError", retry: "after", category: "rate_limit", remedy: "For a full spend window wait for Retry-After or use your own provider key. For a request above a whole minute/hour cap lower max_tokens; for the new-org daily cap contact support." }],
  ["429:rate_limit_exceeded", { name: "RateLimitError", retry: "status", category: "rate_limit", remedy: "Honor Retry-After if present; otherwise bounded exponential backoff." }],
  ["503:managed_billing_unavailable", { name: "ServiceUnavailableError", retry: "status", category: "billing_unavailable", remedy: "Retry with bounded backoff or use your own provider key; persistent credit-store failure needs an operator." }],
  ["403:permission_denied", { name: "PermissionDeniedError", retry: "never", category: "permission", remedy: "Choose a managed model with supported pricing, or use your own provider key. A policy/IP refusal sharing this code requires its own policy remedy." }],
  ["403:future_agi_credits_off", { name: "FutureAGICreditsOffError", retry: "never", category: "permission", remedy: CREDITS_OFF_REMEDY }],
  ["401:invalid_api_key", { name: "AuthenticationError", retry: "never", category: "invalid_key", remedy: "Create or rotate a gateway API key on Gateway API Keys and supply it in the endpoint-supported authentication header. Do not send Build Keys or provider-vendor keys as gateway credentials." }],
  ["402:agent_call_cap_exceeded", { name: "AgentBudgetExhaustedError", retry: "never", category: "agent_budget", remedy: "Lower max_tokens, choose a cheaper model or raise the cap." }],
  ["402:call_cap_unenforceable", { name: "AgentBudgetExhaustedError", retry: "never", category: "agent_budget", remedy: "Choose a priced model with an enforceable bound or correct the administrative identity/route/cap policy; do not bypass the cap." }],
  ["402:agent_run_stopped", { name: "AgentBudgetExhaustedError", retry: "never", category: "agent_budget", remedy: "Address the stop cause and start a new run." }],
  ["503:budget_state_unavailable", { name: "ServiceUnavailableError", retry: "status", category: "billing_unavailable", remedy: "Retry transient state failures with bounded backoff; an administrator must correct missing activation/stale policy or persistent unavailable durable state." }],
  ["402:managed_spend_paused", { name: "APIStatusError", retry: "never", category: "budget_limit", remedy: "An administrator raises the exhausted budget or resumes the anomaly-paused organization; own provider keys are an alternative." }],
  ["402:payment_required", { name: "InsufficientCreditsError", retry: "never", category: "out_of_credits", remedy: "Top up the managed API key prepaid balance." }],
  ["429:budget_throttled", { name: "RateLimitError", retry: "after", category: "rate_limit", remedy: "Wait for the throttle slot window or ask an administrator to adjust it." }],
  ["503:key_list_not_loaded", { name: "ServiceUnavailableError", retry: "status", category: "generic", remedy: "Wait for the first control-plane key list; an operator repairs persistent synchronization failure." }],
  ["403:model_not_permitted", { name: "PermissionDeniedError", retry: "never", category: "permission", remedy: "Choose an allowed model with supported pricing or ask an authorized administrator to adjust the binding policy." }],
  ["403:managed_router_unbounded", { name: "PermissionDeniedError", retry: "never", category: "permission", remedy: "Use a bounded priced managed model or your own provider key for the vendor router." }],
  ["400:unsupported_field_for_managed", { name: "BadRequestError", retry: "never", category: "generic", remedy: "Remove/change the unsupported field or use your own provider key for the dimension." }],
  ["400:unsupported_routing_field", { name: "BadRequestError", retry: "never", category: "generic", remedy: "Remove the unsupported routing field or select a supported endpoint/own-provider-key route." }],
  ["403:key_scope_denied", { name: "PermissionDeniedError", retry: "never", category: "permission", remedy: "Use a key authorized for this operation or have an authorized administrator issue an appropriately scoped key." }],
  ["402:agent_key_budget_exhausted", { name: "AgentBudgetExhaustedError", retry: "never", category: "agent_budget", remedy: "An org administrator raises/repairs the workspace agent-key budget, or wait for its stated reset." }],
  ["429:token_rate_limit_exceeded", { name: "RateLimitError", retry: "status", category: "rate_limit", remedy: "Wait for the token-rate window or adjust the authorized token-rate limit." }],
  ["429:usage_paused", { name: "BudgetExceededError", retry: "never", category: "budget_limit", remedy: "Adjust the exhausted budget or contact support; this is not transient rate limiting." }],
  ["429:quota_exceeded", { name: "BudgetExceededError", retry: "never", category: "budget_limit", remedy: "Upgrade the plan or obtain additional request quota; do not blindly retry." }],
  ["400:usage_unavailable", { name: "BadRequestError", retry: "never", category: "generic", remedy: "Send without background so the gateway can observe and bill usage." }],
  ["503:provider_busy", { name: "ServiceUnavailableError", retry: "after", category: "generic", remedy: "Wait for a provider slot, then retry after Retry-After." }],
  ["409:idempotency_in_progress", { name: "APIStatusError", retry: "after", category: "generic", remedy: "Retry the same request and idempotency key after Retry-After." }],
  ["422:idempotency_key_reused", { name: "UnprocessableEntityError", retry: "never", category: "generic", remedy: "Use a new idempotency key for a genuinely different request body." }],
  ["404:managed_models_disabled", { name: "NotFoundError", retry: "never", category: "generic", remedy: "An operator configures managed providers before this admin operation is available." }],
  ["400:deferred_run_unavailable", { name: "BadRequestError", retry: "never", category: "generic", remedy: "Send the organization-key request synchronously." }],
  ["404:model_not_found", { name: "NotFoundError", retry: "never", category: "generic", remedy: "Use GET /v1/models and choose a model this key can call." }],
  ["504:gateway_timeout", { name: "GatewayTimeoutError", retry: "never", category: "generic", remedy: "The gateway timed out; check whether the request was applied before sending it again." }],
  ["410:model_expired", { name: "APIStatusError", retry: "never", category: "generic", remedy: "Choose an active replacement model; an expired or shut-down model is not restored by retrying." }],
  ["404:no_provider_matches", { name: "NotFoundError", retry: "never", category: "generic", remedy: "Adjust the request provider filters/order/allow_fallbacks to include an eligible endpoint; do not bypass organization policy." }],
  ["400:provider_preference_unavailable", { name: "BadRequestError", retry: "never", category: "generic", remedy: "Remove/change the unsupported provider preference, or choose a model whose endpoint information supports it." }],
  ["400:model_ambiguous", { name: "BadRequestError", retry: "never", category: "generic", remedy: "Send one of the complete catalog model IDs named by the refusal instead of an ambiguous bare name." }],
  ["400:no_auto_candidate", { name: "BadRequestError", retry: "never", category: "generic", remedy: "Choose an eligible explicit model or correct the auto candidate/capability/price constraints; if there are no usable routes, enable credits or add an own-provider route through authorized controls." }],
  ["400:omega_default_unroutable", { name: "BadRequestError", retry: "never", category: "generic", remedy: "Enable managed models through the authorized credits control or add an own provider; alternatively configure a routable default model." }],
  ["400:route_hint_unsupported", { name: "BadRequestError", retry: "never", category: "generic", remedy: "For model auto, use route-hint cost, balanced or quality, or omit the hint; latency ranking is unsupported." }],
  ["400:routing_field_not_yet_supported", { name: "BadRequestError", retry: "never", category: "generic", remedy: "Remove the unimplemented field or use a routing field the gateway supports." }],
  ["400:invalid_provider_preference", { name: "BadRequestError", retry: "never", category: "generic", remedy: "Correct or remove the field named by error.param; use a supported provider preference with its documented type and allowed values." }],
  ["400:invalid_routing_field", { name: "BadRequestError", retry: "never", category: "generic", remedy: "Correct or remove the field named by error.param. Do not send models and fallbacks together; obey the model-list and fallback-list limits and required shapes." }],
  ["400:extra_body_conflict", { name: "BadRequestError", retry: "never", category: "generic", remedy: "Remove the conflicting duplicate or make it agree with the top-level field. Send pre-read model, messages, streaming, user, metadata and session fields at the top level." }],
  ["400:invalid_extra_body", { name: "BadRequestError", retry: "never", category: "generic", remedy: "Send extra_body as a non-nested JSON object whose fields have the request types the gateway expects, or remove it." }],
  ["404:provider_not_found", { name: "NotFoundError", retry: "never", category: "generic", remedy: "Correct or remove the provider lock, or ask an authorized operator to configure the intended provider; do not bypass provider access policy." }],
]);

const FLAT_CODES = new Set([
  "managed_credits_exhausted", "managed_credits_insufficient", "agent_budget_exhausted",
  "budget_exceeded", "org_budget_exceeded", "managed_spend_velocity",
  "rate_limit_exceeded", "managed_billing_unavailable",
]);

function object(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? value as Record<string, unknown> : null;
}

function errorObject(body: unknown): Record<string, unknown> | null {
  const outer = object(body);
  // An existing envelope, even malformed or code-less, always wins over flat code.
  if (!outer || "error" in outer) return object(outer?.error);
  return typeof outer.code === "string" && FLAT_CODES.has(outer.code) ? { code: outer.code } : null;
}

/** Only error.metadata is wire metadata; flat compatibility admits codes, not hints. */
export function refusalMetadata(body: unknown): Record<string, unknown> | null {
  return object(object(object(body)?.error)?.metadata);
}

/** Unknown/mismatched pairs have no canonical details, regardless of metadata. */
export function refusalDetails(status: number, body: unknown): RefusalDetails | null {
  const error = errorObject(body);
  if (typeof error?.code !== "string") return null;
  const entry = REFUSALS.get(`${status}:${error.code}`);
  if (!entry) return null;
  const metadata = refusalMetadata(body);
  if (status === 402 && error.code === "managed_credits_insufficient"
    && metadata?.limit_source === "agentcc_in_flight" && metadata.remedy_hint === "retry") {
    return { ...entry, retry: "once" };
  }
  if (status === 429 && error.code === "managed_spend_velocity"
    && !(metadata?.remedy_hint === "retry" && !("reason" in metadata))) {
    return { ...entry, retry: "never" };
  }
  // Every documented budget-state producer allows bounded backoff. There is no
  // persistent/transient wire discriminator; do not invent one from prose/type.
  return entry;
}

/** A null classification preserves the existing status-only error class. */
export function classifyRefusal(status: number, body: unknown): Refusal | null {
  const entry = refusalDetails(status, body);
  return entry ? { name: entry.name, retry: entry.retry } : null;
}

/**
 * Maximum automatic Retry-After: 2,147,483 seconds, fitting the signed 32-bit
 * millisecond timer supported by Node and browsers. Larger positive integer
 * hints stop automatic replay rather than shortening the server's wait. Valid
 * hints on recognized retryable rows are not subject to the legacy 60s cap.
 * Fractional, signed, exponent, HTTP-date and comma-combined hints never
 * authorize conditional credit/spend-window replay.
 */
export const MAX_RETRY_AFTER_SECONDS = 2_147_483;
function retryAfterSeconds(headers?: Headers): number | null {
  const raw = headers?.get("retry-after")?.replace(/^[ \t]+|[ \t]+$/g, "");
  if (!raw || /[^0-9]/.test(raw)) return null;
  const seconds = Number(raw);
  return seconds > 0 ? seconds : null;
}
/** Strict positive ASCII integer delta-seconds within the SDK timer maximum. */
export function positiveRetryAfter(headers?: Headers): number | null {
  const seconds = retryAfterSeconds(headers);
  return seconds !== null && seconds <= MAX_RETRY_AFTER_SECONDS ? seconds * 1000 : null;
}

export const UNCONFIRMED_DISPATCH_REMEDY = "The gateway did not confirm whether the request was applied; check whether it was applied before sending it again.";

/** Only response headers establish dispatch; body hints never authorize a replay. */
export function hasUnconfirmedDispatch(status: number, body: unknown, headers?: Headers, evidence?: GatewayEvidence): boolean {
  const snapshot = evidence ?? (headers ? evidenceFromHeaders(headers) : parseGatewayEvidence());
  // Explicit contract rows take precedence. Unknown/mismatched codes do not:
  // a gateway identity with missing or invalid dispatch still needs guidance.
  return refusalDetails(status, body) === null
    && gatewayRequestIdPresence(snapshot) !== "absent"
    && snapshot.dispatched !== false;
}

/** Explicit contract rows win; all other retries require a safe dispatch boundary. */
export function refusalRetry(status: number, body: unknown, headers?: Headers, evidence?: GatewayEvidence): Refusal["retry"] {
  if (hasUnconfirmedDispatch(status, body, headers, evidence)) return "never";
  const retry = refusalDetails(status, body)?.retry
    ?? (errorObject(body)?.code == null ? "status" : "never");
  // Never turn an unrepresentable wait into an immediate timer or shorter backoff.
  if ((retryAfterSeconds(headers) ?? 0) > MAX_RETRY_AFTER_SECONDS) return "never";
  return (retry === "after" || retry === "once") && positiveRetryAfter(headers) === null ? "never" : retry;
}

export function numberField(metadata: Record<string, unknown> | null, key: string): number | null {
  const value = metadata?.[key];
  return typeof value === "number" ? value : null;
}

export function stringField(metadata: Record<string, unknown> | null, key: string): string | null {
  const value = metadata?.[key];
  return typeof value === "string" ? value : null;
}

export function suggestionsField(metadata: Record<string, unknown> | null): string[] | null {
  const value = metadata?.suggestions;
  return Array.isArray(value) && value.every((item) => typeof item === "string") ? value : null;
}

/** Authentication reasons are carried in error.metadata, not in the error type. */
export function refusalReason(body: unknown): string | null {
  return stringField(refusalMetadata(body), "reason");
}

/** Retain the existing typed-credit/budget subclass ancestry. */
export function withRefusalDetails<T extends new (...args: any[]) => { readonly body: unknown }>(Base: T) {
  return class extends Base {
    get metadata(): Record<string, unknown> | null { return refusalMetadata(this.body); }
    get requiredUsd(): number | null { return numberField(this.metadata, "required_usd"); }
    get availableUsd(): number | null { return numberField(this.metadata, "available_usd"); }
    get limitSource(): string | null { return stringField(this.metadata, "limit_source"); }
    get remedyHint(): string | null { return stringField(this.metadata, "remedy_hint"); }
    get scope(): string | null { return stringField(this.metadata, "scope"); }
    get resetsAt(): string | null { return stringField(this.metadata, "resets_at"); }
    get reason(): string | null { return stringField(this.metadata, "reason"); }
  };
}
