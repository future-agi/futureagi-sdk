"""Shared AgentCC-specific parameter handling for all API resources.

Extracts AgentCC gateway params (session_id, trace_id, cache_ttl, etc.)
from method kwargs and converts them to HTTP headers, keeping them
out of the JSON request body.
"""

from __future__ import annotations

from typing import Any

from fi.gateway._constants import NOT_GIVEN


# AgentCC-specific param keys that map to headers (not sent in the body)
AGENTCC_PARAM_KEYS = frozenset({
    "session_id",
    "trace_id",
    "request_metadata",
    "request_timeout",
    "cache_ttl",
    "cache_namespace",
    "cache_force_refresh",
    "cache_control",
    "guardrail_policy",
})


def collect_agentcc_params(
    *,
    session_id: Any = NOT_GIVEN,
    trace_id: Any = NOT_GIVEN,
    request_metadata: Any = NOT_GIVEN,
    request_timeout: Any = NOT_GIVEN,
    cache_ttl: Any = NOT_GIVEN,
    cache_namespace: Any = NOT_GIVEN,
    cache_force_refresh: Any = NOT_GIVEN,
    cache_control: Any = NOT_GIVEN,
    guardrail_policy: Any = NOT_GIVEN,
) -> dict[str, Any]:
    """Collect AgentCC params into a dict (only those that are provided)."""
    agentcc_params: dict[str, Any] = {}
    _locals = {
        "session_id": session_id,
        "trace_id": trace_id,
        "request_metadata": request_metadata,
        "request_timeout": request_timeout,
        "cache_ttl": cache_ttl,
        "cache_namespace": cache_namespace,
        "cache_force_refresh": cache_force_refresh,
        "cache_control": cache_control,
        "guardrail_policy": guardrail_policy,
    }
    for key, val in _locals.items():
        if val is not NOT_GIVEN:
            agentcc_params[key] = val
    return agentcc_params


def build_extra_headers(
    *,
    extra_headers: dict[str, str] | None = None,
    properties: dict[str, str] | None = None,
    user_id: str | None = None,
    request_id: str | None = None,
) -> dict[str, str]:
    """Build extra headers from AgentCC-specific request params."""
    hdrs: dict[str, str] = dict(extra_headers) if extra_headers else {}

    # Custom properties -> x-agentcc-property-{key}
    if properties:
        for key, val in properties.items():
            hdrs[f"x-agentcc-property-{key}"] = val

    # User ID -> x-agentcc-user-id
    if user_id is not None:
        hdrs["x-agentcc-user-id"] = user_id

    # Request ID -> x-agentcc-request-id
    if request_id is not None:
        hdrs["x-agentcc-request-id"] = request_id

    return hdrs


def merge_session_headers(client: Any, headers: dict[str, str]) -> dict[str, str]:
    """Merge active session headers into the extra headers dict.

    Session headers are added first so that explicit per-request headers
    take precedence (they overwrite session values).
    """
    active_session = getattr(client, "_active_session", None)
    if active_session is None:
        return headers
    session_hdrs = active_session.to_headers()
    merged = dict(session_hdrs)
    merged.update(headers)
    return merged
