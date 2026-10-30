"""AgentCCMetadata — parsed gateway response headers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RateLimitInfo(BaseModel):
    """Rate-limit information extracted from ``x-ratelimit-*`` headers."""

    limit: int | None = None
    remaining: int | None = None
    reset: int | None = None


class AgentCCMetadata(BaseModel):
    """Structured metadata parsed from AgentCC gateway response headers.

    Every response from the gateway includes ``x-agentcc-*`` headers.
    This model provides typed access to that metadata.
    """

    model_config = ConfigDict(extra="ignore")

    request_id: str = "unknown"
    trace_id: str = "unknown"
    provider: str = "unknown"
    latency_ms: int = 0
    cost: float | None = None
    cache_status: str | None = None
    model_used: str | None = None
    guardrail_triggered: bool = False
    fallback_used: bool = False
    routing_strategy: str | None = None
    timeout_ms: int | None = None
    ratelimit: RateLimitInfo | None = None
    http_response: Any = Field(default=None, exclude=True)

    @classmethod
    def from_headers(cls, headers: Mapping[str, str], *, http_response: Any = None) -> AgentCCMetadata:
        """Parse ``x-agentcc-*`` response headers into a :class:`AgentCCMetadata` instance."""
        from fi.gateway._constants import (
            HEADER_RATELIMIT_LIMIT,
            HEADER_RATELIMIT_REMAINING,
            HEADER_RATELIMIT_RESET,
            HEADER_RESPONSE_CACHE,
            HEADER_RESPONSE_COST,
            HEADER_RESPONSE_FALLBACK_USED,
            HEADER_RESPONSE_GUARDRAIL_TRIGGERED,
            HEADER_RESPONSE_LATENCY,
            HEADER_RESPONSE_MODEL_USED,
            HEADER_RESPONSE_PROVIDER,
            HEADER_RESPONSE_REQUEST_ID,
            HEADER_RESPONSE_ROUTING_STRATEGY,
            HEADER_RESPONSE_TIMEOUT,
            HEADER_RESPONSE_TRACE_ID,
        )

        # Parse rate-limit headers — only build RateLimitInfo if any are present
        rl_limit = _int_or_none(headers.get(HEADER_RATELIMIT_LIMIT))
        rl_remaining = _int_or_none(headers.get(HEADER_RATELIMIT_REMAINING))
        rl_reset = _int_or_none(headers.get(HEADER_RATELIMIT_RESET))
        ratelimit: RateLimitInfo | None = None
        if rl_limit is not None or rl_remaining is not None or rl_reset is not None:
            ratelimit = RateLimitInfo(limit=rl_limit, remaining=rl_remaining, reset=rl_reset)

        return cls(
            request_id=headers.get(HEADER_RESPONSE_REQUEST_ID, "unknown"),
            trace_id=headers.get(HEADER_RESPONSE_TRACE_ID, "unknown"),
            provider=headers.get(HEADER_RESPONSE_PROVIDER, "unknown"),
            latency_ms=_int_or_none(headers.get(HEADER_RESPONSE_LATENCY)) or 0,
            cost=_float_or_none(headers.get(HEADER_RESPONSE_COST)),
            cache_status=headers.get(HEADER_RESPONSE_CACHE),
            model_used=headers.get(HEADER_RESPONSE_MODEL_USED),
            guardrail_triggered=headers.get(HEADER_RESPONSE_GUARDRAIL_TRIGGERED, "").lower() == "true",
            fallback_used=headers.get(HEADER_RESPONSE_FALLBACK_USED, "").lower() == "true",
            routing_strategy=headers.get(HEADER_RESPONSE_ROUTING_STRATEGY),
            timeout_ms=_int_or_none(headers.get(HEADER_RESPONSE_TIMEOUT)),
            ratelimit=ratelimit,
            http_response=http_response,
        )


def _int_or_none(val: str | None) -> int | None:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def _float_or_none(val: str | None) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None
