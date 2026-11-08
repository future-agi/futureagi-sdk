"""Current gateway error contract r3; pending wire changes are deliberately absent.

Each row binds the HTTP status and code, never message prose or error.type.
Retry predicates and header validation live in _retry_policy.
"""
from typing import NamedTuple
from fi.gateway import _exceptions as _errors


class _Refusal(NamedTuple):
    exception: type[_errors.APIStatusError]
    retry: bool | None
    category: str
    remedy: str


_REFUSALS: dict[tuple[int, str], _Refusal] = {
    (402, "managed_credits_exhausted"): _Refusal(
        _errors.InsufficientCreditsError, False, "out_of_credits",
        'Add credit on Settings Billing; on a grant-only install ask its operator to grant credit; alternatively use your own provider key on Gateway Providers.'),
    (402, "managed_credits_insufficient"): _Refusal(
        _errors.InsufficientCreditsError, False, "out_of_credits",
        'For in-flight holds, wait for Retry-After; otherwise add credit, lower max_tokens or use your own provider key.'),
    (402, "agent_budget_exhausted"): _Refusal(
        _errors.AgentBudgetExhaustedError, False, "agent_budget",
        'Raise the run budget or start a new run; a call-only budget may also be lowered by reducing max_tokens or choosing a cheaper model. Administrative ceilings need an authorized policy change.'),
    (429, "budget_exceeded"): _Refusal(
        _errors.BudgetExceededError, False, "budget_limit",
        'An administrator raises the binding budget, or wait for its period to reset; never automatically retry the same refusal.'),
    (429, "org_budget_exceeded"): _Refusal(
        _errors.BudgetExceededError, False, "budget_limit",
        'Raise the binding budget/daily cap through an authorized administrator, or wait for its reset; no automatic retry.'),
    (429, "managed_spend_velocity"): _Refusal(
        _errors.RateLimitError, False, "rate_limit",
        'For a full spend window wait for Retry-After or use your own provider key. For a request above a whole minute/hour cap lower max_tokens; for the new-org daily cap contact support.'),
    (429, "rate_limit_exceeded"): _Refusal(
        _errors.RateLimitError, None, "rate_limit",
        'Honor Retry-After if present; otherwise bounded exponential backoff.'),
    (503, "managed_billing_unavailable"): _Refusal(
        _errors.ServiceUnavailableError, None, "billing_unavailable",
        'Retry with bounded backoff or use your own provider key; persistent credit-store failure needs an operator.'),
    (403, "permission_denied"): _Refusal(
        _errors.PermissionDeniedError, False, "permission",
        'Choose a managed model with supported pricing, or use your own provider key. A policy/IP refusal sharing this code requires its own policy remedy.'),
    (403, "future_agi_credits_off"): _Refusal(
        _errors.FutureAGICreditsOffError, False, "permission",
        'An organization Owner or Admin uses the "Turn on Future AGI credits" control on the Gateway Models page, or adds their own provider key on the Gateway Providers page.'),
    (401, "invalid_api_key"): _Refusal(
        _errors.AuthenticationError, False, "invalid_key",
        'Create or rotate a gateway API key on Gateway API Keys and supply it in the endpoint-supported authentication header. Do not send Build Keys or provider-vendor keys as gateway credentials.'),
    (402, "agent_call_cap_exceeded"): _Refusal(
        _errors.AgentBudgetExhaustedError, False, "agent_budget",
        'Lower max_tokens, choose a cheaper model or raise the cap.'),
    (402, "call_cap_unenforceable"): _Refusal(
        _errors.AgentBudgetExhaustedError, False, "agent_budget",
        'Choose a priced model with an enforceable bound or correct the administrative identity/route/cap policy; do not bypass the cap.'),
    (402, "agent_run_stopped"): _Refusal(
        _errors.AgentBudgetExhaustedError, False, "agent_budget",
        'Address the stop cause and start a new run.'),
    (503, "budget_state_unavailable"): _Refusal(
        _errors.ServiceUnavailableError, None, "billing_unavailable",
        'Retry transient state failures with bounded backoff; an administrator must correct missing activation/stale policy or persistent unavailable durable state.'),
    (402, "managed_spend_paused"): _Refusal(
        _errors.APIStatusError, False, "budget_limit",
        'An administrator raises the exhausted budget or resumes the anomaly-paused organization; own provider keys are an alternative.'),
    (402, "payment_required"): _Refusal(
        _errors.InsufficientCreditsError, False, "out_of_credits",
        'Top up the managed API key prepaid balance.'),
    (429, "budget_throttled"): _Refusal(
        _errors.RateLimitError, True, "rate_limit",
        'Wait for the throttle slot window or ask an administrator to adjust it.'),
    (503, "key_list_not_loaded"): _Refusal(
        _errors.ServiceUnavailableError, None, "generic",
        'Wait for the first control-plane key list; an operator repairs persistent synchronization failure.'),
    (403, "model_not_permitted"): _Refusal(
        _errors.PermissionDeniedError, False, "permission",
        'Choose an allowed model with supported pricing or ask an authorized administrator to adjust the binding policy.'),
    (403, "managed_router_unbounded"): _Refusal(
        _errors.PermissionDeniedError, False, "permission",
        'Use a bounded priced managed model or your own provider key for the vendor router.'),
    (400, "unsupported_field_for_managed"): _Refusal(
        _errors.BadRequestError, False, "generic",
        'Remove/change the unsupported field or use your own provider key for the dimension.'),
    (400, "unsupported_routing_field"): _Refusal(
        _errors.BadRequestError, False, "generic",
        'Remove the unsupported routing field or select a supported endpoint/own-provider-key route.'),
    (403, "key_scope_denied"): _Refusal(
        _errors.PermissionDeniedError, False, "permission",
        'Use a key authorized for this operation or have an authorized administrator issue an appropriately scoped key.'),
    (402, "agent_key_budget_exhausted"): _Refusal(
        _errors.AgentBudgetExhaustedError, False, "agent_budget",
        'An org administrator raises/repairs the workspace agent-key budget, or wait for its stated reset.'),
    (429, "token_rate_limit_exceeded"): _Refusal(
        _errors.RateLimitError, None, "rate_limit",
        'Wait for the token-rate window or adjust the authorized token-rate limit.'),
    (429, "usage_paused"): _Refusal(
        _errors.BudgetExceededError, False, "budget_limit",
        'Adjust the exhausted budget or contact support; this is not transient rate limiting.'),
    (429, "quota_exceeded"): _Refusal(
        _errors.BudgetExceededError, False, "budget_limit",
        'Upgrade the plan or obtain additional request quota; do not blindly retry.'),
    (400, "usage_unavailable"): _Refusal(
        _errors.BadRequestError, False, "generic",
        'Send without background so the gateway can observe and bill usage.'),
    (503, "provider_busy"): _Refusal(
        _errors.ServiceUnavailableError, True, "generic",
        'Wait for a provider slot, then retry after Retry-After.'),
    (409, "idempotency_in_progress"): _Refusal(
        _errors.APIStatusError, True, "generic",
        'Retry the same request and idempotency key after Retry-After.'),
    (422, "idempotency_key_reused"): _Refusal(
        _errors.UnprocessableEntityError, False, "generic",
        'Use a new idempotency key for a genuinely different request body.'),
    (404, "managed_models_disabled"): _Refusal(
        _errors.NotFoundError, False, "generic",
        'An operator configures managed providers before this admin operation is available.'),
    (400, "deferred_run_unavailable"): _Refusal(
        _errors.BadRequestError, False, "generic",
        'Send the organization-key request synchronously.'),
    (404, "model_not_found"): _Refusal(
        _errors.NotFoundError, False, "generic",
        'Use GET /v1/models and choose a model this key can call.'),
    (504, "gateway_timeout"): _Refusal(
        _errors.GatewayTimeoutError, False, "generic",
        'The gateway timed out; check whether the request was applied before sending it again.'),
    (410, "model_expired"): _Refusal(
        _errors.APIStatusError, False, "generic",
        'Choose an active replacement model; an expired or shut-down model is not restored by retrying.'),
    (404, "no_provider_matches"): _Refusal(
        _errors.NotFoundError, False, "generic",
        'Adjust the request provider filters/order/allow_fallbacks to include an eligible endpoint; do not bypass organization policy.'),
    (400, "provider_preference_unavailable"): _Refusal(
        _errors.BadRequestError, False, "generic",
        'Remove/change the unsupported provider preference, or choose a model whose endpoint information supports it.'),
    (400, "model_ambiguous"): _Refusal(
        _errors.BadRequestError, False, "generic",
        'Send one of the complete catalog model IDs named by the refusal instead of an ambiguous bare name.'),
    (400, "no_auto_candidate"): _Refusal(
        _errors.BadRequestError, False, "generic",
        'Choose an eligible explicit model or correct the auto candidate/capability/price constraints; if there are no usable routes, enable credits or add an own-provider route through authorized controls.'),
    (400, "omega_default_unroutable"): _Refusal(
        _errors.BadRequestError, False, "generic",
        'Enable managed models through the authorized credits control or add an own provider; alternatively configure a routable default model.'),
    (400, "route_hint_unsupported"): _Refusal(
        _errors.BadRequestError, False, "generic",
        'For model auto, use route-hint cost, balanced or quality, or omit the hint; latency ranking is unsupported.'),
    (400, "routing_field_not_yet_supported"): _Refusal(
        _errors.BadRequestError, False, "generic",
        'Remove the unimplemented field or use a routing field the gateway supports.'),
    (400, "invalid_provider_preference"): _Refusal(
        _errors.BadRequestError, False, "generic",
        'Correct or remove the field named by error.param; use a supported provider preference with its documented type and allowed values.'),
    (400, "invalid_routing_field"): _Refusal(
        _errors.BadRequestError, False, "generic",
        'Correct or remove the field named by error.param. Do not send models and fallbacks together; obey the model-list and fallback-list limits and required shapes.'),
    (400, "extra_body_conflict"): _Refusal(
        _errors.BadRequestError, False, "generic",
        'Remove the conflicting duplicate or make it agree with the top-level field. Send pre-read model, messages, streaming, user, metadata and session fields at the top level.'),
    (400, "invalid_extra_body"): _Refusal(
        _errors.BadRequestError, False, "generic",
        'Send extra_body as a non-nested JSON object whose fields have the request types the gateway expects, or remove it.'),
    (404, "provider_not_found"): _Refusal(
        _errors.NotFoundError, False, "generic",
        'Correct or remove the provider lock, or ask an authorized operator to configure the intended provider; do not bypass provider access policy.'),
}

_CREDITS_OFF_REMEDY = _REFUSALS[(403, "future_agi_credits_off")].remedy
