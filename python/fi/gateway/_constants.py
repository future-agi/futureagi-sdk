"""Constants for the AgentCC SDK — header names, defaults, version, sentinel."""

from __future__ import annotations

import os
from typing import Any

__version__ = "0.1.0"

# --- Defaults ---

DEFAULT_TIMEOUT: float = 600.0
DEFAULT_MAX_RETRIES: int = 2
DEFAULT_MAX_CONNECTIONS: int = 100
DEFAULT_KEEPALIVE_CONNECTIONS: int = 20
DEFAULT_KEEPALIVE_EXPIRY: float = 5.0

# --- Request header names ---

HEADER_API_KEY = "Authorization"
HEADER_CONTENT_TYPE = "Content-Type"
HEADER_USER_AGENT = "User-Agent"
HEADER_SDK_VERSION = "x-agentcc-sdk-version"
HEADER_TRACE_ID = "x-agentcc-trace-id"
HEADER_SESSION_ID = "x-agentcc-session-id"
HEADER_METADATA = "x-agentcc-metadata"
HEADER_REQUEST_TIMEOUT = "x-agentcc-request-timeout"
HEADER_CACHE_TTL = "x-agentcc-cache-ttl"
HEADER_CACHE_NAMESPACE = "x-agentcc-cache-namespace"
HEADER_CACHE_FORCE_REFRESH = "x-agentcc-cache-force-refresh"
HEADER_CACHE_CONTROL = "Cache-Control"
HEADER_GUARDRAIL_POLICY = "X-Guardrail-Policy"
HEADER_CONFIG = "x-agentcc-config"

# --- Response header names ---

HEADER_RESPONSE_REQUEST_ID = "x-agentcc-request-id"
HEADER_RESPONSE_TRACE_ID = "x-agentcc-trace-id"
HEADER_RESPONSE_PROVIDER = "x-agentcc-provider"
HEADER_RESPONSE_LATENCY = "x-agentcc-latency-ms"
HEADER_RESPONSE_COST = "x-agentcc-cost"
HEADER_RESPONSE_CACHE = "x-agentcc-cache"
HEADER_RESPONSE_MODEL_USED = "x-agentcc-model-used"
HEADER_RESPONSE_GUARDRAIL_TRIGGERED = "x-agentcc-guardrail-triggered"
HEADER_RESPONSE_GUARDRAIL_NAME = "x-agentcc-guardrail-name"
HEADER_RESPONSE_GUARDRAIL_ACTION = "x-agentcc-guardrail-action"
HEADER_RESPONSE_GUARDRAIL_CONFIDENCE = "x-agentcc-guardrail-confidence"
HEADER_RESPONSE_GUARDRAIL_MESSAGE = "x-agentcc-guardrail-message"
HEADER_RESPONSE_FALLBACK_USED = "x-agentcc-fallback-used"
HEADER_RESPONSE_ROUTING_STRATEGY = "x-agentcc-routing-strategy"
HEADER_RESPONSE_TIMEOUT = "x-agentcc-timeout-ms"
HEADER_RATELIMIT_LIMIT = "x-ratelimit-limit-requests"
HEADER_RATELIMIT_REMAINING = "x-ratelimit-remaining-requests"
HEADER_RATELIMIT_RESET = "x-ratelimit-reset-requests"

# --- AgentCC param → header mapping ---

AGENTCC_PARAM_TO_HEADER: dict[str, str] = {
    "session_id": HEADER_SESSION_ID,
    "trace_id": HEADER_TRACE_ID,
    "request_metadata": HEADER_METADATA,
    "request_timeout": HEADER_REQUEST_TIMEOUT,
    "cache_ttl": HEADER_CACHE_TTL,
    "cache_namespace": HEADER_CACHE_NAMESPACE,
    "cache_force_refresh": HEADER_CACHE_FORCE_REFRESH,
    "cache_control": HEADER_CACHE_CONTROL,
    "guardrail_policy": HEADER_GUARDRAIL_POLICY,
}

# --- Retryable status codes ---

RETRYABLE_STATUS_CODES: set[int] = {408, 429, 500, 502, 503, 504}

# --- Sentinel for "not given" (distinct from None) ---


class _NotGiven:
    """Sentinel to distinguish 'not provided' from None.

    This is important when None is a valid explicit value.
    For example: temperature=None means 'use default', which is different
    from the user not specifying temperature at all.
    """

    _instance: _NotGiven | None = None

    def __new__(cls) -> _NotGiven:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "NOT_GIVEN"

    def __str__(self) -> str:
        return "NOT_GIVEN"


NOT_GIVEN: Any = _NotGiven()
"""Sentinel value indicating a parameter was not provided."""

# --- Gateway URL ---

AGENTCC_GATEWAY_URL: str = os.environ.get("AGENTCC_BASE_URL", "https://gateway.futureagi.com/v1")
"""Default AgentCC Gateway URL. Override via ``AGENTCC_BASE_URL`` env var."""
