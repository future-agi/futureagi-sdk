"""Shared AgentCC-specific parameter handling for all API resources.

Extracts AgentCC gateway params (session_id, trace_id, cache_ttl, etc.)
from method kwargs and converts them to HTTP headers, keeping them
out of the JSON request body.
"""

from __future__ import annotations

import json
from typing import Any

from fi.gateway._constants import HEADER_METADATA, NOT_GIVEN

# AgentCC-specific param keys that map to headers (not sent in the body)
AGENTCC_PARAM_KEYS = frozenset(
    {
        "session_id",
        "trace_id",
        "request_metadata",
        "request_timeout",
        "cache_ttl",
        "cache_namespace",
        "cache_force_refresh",
        "cache_control",
        "guardrail_policy",
    }
)


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


def _layer_metadata(*layers: Any) -> Any:
    """The metadata a request sends: its layers merged key by key, a later layer winning.

    The layers are, in order, the client's ``metadata=``, the active session's metadata
    and the request's ``request_metadata``. ``None`` adds nothing; a layer that is not a
    dict (a JSON string given as ``request_metadata``) is sent as given, replacing the
    layers under it.
    """
    result: Any = None
    for layer in layers:
        if layer is None or layer is NOT_GIVEN:
            continue
        if isinstance(layer, dict) and isinstance(result, dict):
            result = {**result, **layer}
        else:
            result = dict(layer) if isinstance(layer, dict) else layer
    return result


def merge_session_headers(
    client: Any, headers: dict[str, str], agentcc_params: dict[str, Any] | None = None,
    *, defer: bool = False,
) -> dict[str, str]:
    """Merge active session headers into the extra headers dict.

    Session headers are added first so that explicit per-request headers
    take precedence (they overwrite session values).

    Published sessions use per-key metadata headers and leave request metadata
    alone. Only ``metadata_mode='merge'`` layers client/session/request dictionaries
    into one JSON header. An explicit raw metadata header always wins.
    """
    active_session = getattr(client, "_active_session", None)
    if active_session is None:
        return headers
    # The session renders its own wire form: per-key aliases by default and one
    # JSON value only under ``metadata_mode='merge'``, so the two never disagree.
    session_hdrs = active_session.to_headers()
    session_metadata = getattr(active_session, "metadata", None)
    if session_metadata and getattr(client, "_metadata_mode", "replace") == "merge":
        client_metadata = getattr(client, "_metadata", None)
        if agentcc_params is None:
            session_hdrs[HEADER_METADATA] = json.dumps(
                _layer_metadata(client_metadata, session_metadata),
                separators=(",", ":"),
            )
        else:
            session_hdrs.pop(HEADER_METADATA, None)
            agentcc_params["request_metadata"] = _layer_metadata(
                client_metadata,
                session_metadata,
                agentcc_params.get("request_metadata"),
            )
    if defer and agentcc_params is not None:
        # Compose SDK session values only in the transport's separate wire dict.
        # The request descriptor must retain just the caller's live headers.
        agentcc_params["_session_headers"] = session_hdrs
        if session_metadata and getattr(client, "_metadata_mode", "replace") == "merge":
            agentcc_params["_client_header_names"] = (HEADER_METADATA,)
        return headers
    merged = dict(session_hdrs)
    merged.update(headers)
    return merged
