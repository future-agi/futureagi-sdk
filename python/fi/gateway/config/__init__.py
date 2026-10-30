"""Gateway configuration builders — routing, fallback, retry, cache, guardrails.

This module re-exports all configuration classes from ``agentcc._gateway_config``
and provides backward-compatible Pydantic-based wrappers for the older
``config/`` submodule API.

The canonical implementation lives in ``_gateway_config.py`` (pure dataclasses).
The Pydantic models in ``config/caching.py``, ``config/routing.py``, etc. are
kept for backward compatibility but new code should use the dataclass versions.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field, field_validator
from typing_extensions import Literal

# Re-export the dataclass-based config classes as the primary API
from fi.gateway._gateway_config import (
    CacheConfig as DataclassCacheConfig,
    ConditionalRoutingConfig,
    FallbackConfig,
    FallbackTarget,
    GatewayConfig as DataclassGatewayConfig,
    GuardrailCheck,
    GuardrailConfig as DataclassGuardrailConfig,
    LoadBalanceConfig,
    LoadBalanceTarget,
    RetryConfig as DataclassRetryConfig,
    RoutingCondition,
    TimeoutConfig,
    TrafficMirrorConfig,
    create_headers,
)

# ---------------------------------------------------------------------------
# Pydantic wrappers (backward compat with config/ submodule API)
# ---------------------------------------------------------------------------


class Target(BaseModel):
    """A single routing target (provider + optional model)."""

    provider: str
    model: str | None = None
    weight: float | None = None
    virtual_key: str | None = None


class LoadBalanceStrategy(BaseModel):
    """Load-balance strategy across multiple targets."""

    mode: Literal["round-robin", "weighted", "least-latency", "cost-optimized"]
    targets: list[Target]

    @field_validator("targets")
    @classmethod
    def _min_one_target(cls, v: list[Target]) -> list[Target]:
        if len(v) < 1:
            msg = "At least one target is required"
            raise ValueError(msg)
        return v

    def model_post_init(self, __context: object) -> None:
        """Validate that weighted mode targets have weights summing to ~1.0."""
        if self.mode == "weighted":
            for t in self.targets:
                if t.weight is None:
                    msg = "All targets must have 'weight' set when mode is 'weighted'"
                    raise ValueError(msg)
            total = sum(t.weight for t in self.targets if t.weight is not None)
            if abs(total - 1.0) > 0.01:
                msg = f"Weights must sum to 1.0 (±0.01), got {total}"
                raise ValueError(msg)


class FallbackStrategy(BaseModel):
    """Ordered list of fallback targets."""

    targets: list[Target] = Field(min_length=1)
    on_status_codes: list[int] = Field(default=[429, 500, 502, 503, 504])


class RetryConfig(BaseModel):
    """Client-side retry configuration sent to the gateway."""

    max_retries: int = Field(default=2, ge=0, le=10)
    retry_on_status: list[int] = Field(default=[429, 500, 502, 503])
    backoff_factor: float = 0.5
    backoff_max: float = 30.0
    backoff_jitter: float = 0.25
    respect_retry_after: bool = True


class CacheConfig(BaseModel):
    """Caching configuration sent to the gateway."""

    enabled: bool = True
    mode: Literal["exact", "semantic"] = "exact"
    ttl: str = "1h"
    namespace: str = "default"
    semantic_threshold: float = Field(default=0.92, ge=0.0, le=1.0)
    force_refresh: bool = False


class GuardrailRule(BaseModel):
    """A single guardrail rule."""

    name: str
    action: Literal["block", "warn", "log", "mask"] = "block"
    threshold: float = Field(default=0.8, ge=0.0, le=1.0)


class GuardrailConfig(BaseModel):
    """Pre- and post-request guardrail rules."""

    pre: list[GuardrailRule] = Field(default_factory=list)
    post: list[GuardrailRule] = Field(default_factory=list)


class RouteCondition(BaseModel):
    """A single condition for conditional routing."""

    field: str
    operator: Literal[
        "$eq", "$ne", "$in", "$nin", "$regex",
        "$gt", "$lt", "$gte", "$lte", "$exists",
    ]
    value: str | int | float | bool | list[str]


class ConditionalRoute(BaseModel):
    """A target selected when a condition matches."""

    condition: RouteCondition
    target: Target


class GatewayConfig(BaseModel):
    """Top-level gateway configuration object (Pydantic version).

    For the lightweight dataclass version, use ``agentcc.GatewayConfig``
    (from ``_gateway_config.py``).
    """

    routing: LoadBalanceStrategy | None = None
    fallback: FallbackStrategy | None = None
    retry: RetryConfig | None = None
    cache: CacheConfig | None = None
    guardrails: GuardrailConfig | None = None
    conditional_routes: list[ConditionalRoute] | None = None

    def to_headers(self) -> dict[str, str]:
        """Emit gateway configuration as HTTP headers."""
        headers: dict[str, str] = {}

        # Simple cache headers
        if self.cache is not None:
            if self.cache.ttl != "1h":
                headers["x-agentcc-cache-ttl"] = self.cache.ttl
            if self.cache.namespace != "default":
                headers["x-agentcc-cache-namespace"] = self.cache.namespace
            if self.cache.force_refresh:
                headers["x-agentcc-cache-force-refresh"] = "true"
            if not self.cache.enabled:
                headers["x-agentcc-cache-enabled"] = "false"

        # Complex config -> single JSON header
        complex_config: dict[str, Any] = {}
        if self.routing is not None:
            complex_config["routing"] = self.routing.model_dump(exclude_none=True)
        if self.fallback is not None:
            complex_config["fallback"] = self.fallback.model_dump(exclude_none=True)
        if self.retry is not None:
            complex_config["retry"] = self.retry.model_dump(exclude_none=True)
        if self.cache is not None:
            complex_config["cache"] = self.cache.model_dump(exclude_none=True)
        if self.guardrails is not None:
            complex_config["guardrails"] = self.guardrails.model_dump(exclude_none=True)
        if self.conditional_routes:
            complex_config["conditional_routes"] = [
                cr.model_dump(exclude_none=True) for cr in self.conditional_routes
            ]

        if complex_config:
            headers["x-agentcc-config"] = json.dumps(complex_config, separators=(",", ":"))

        return headers

    def to_json(self) -> str:
        """Serialize the full config to JSON (excluding None fields)."""
        return self.model_dump_json(exclude_none=True)


__all__ = [
    "CacheConfig",
    "ConditionalRoute",
    "ConditionalRoutingConfig",
    "DataclassCacheConfig",
    "DataclassGatewayConfig",
    "DataclassGuardrailConfig",
    "DataclassRetryConfig",
    "FallbackConfig",
    "FallbackStrategy",
    "FallbackTarget",
    "GatewayConfig",
    "GuardrailCheck",
    "GuardrailConfig",
    "GuardrailRule",
    "LoadBalanceConfig",
    "LoadBalanceStrategy",
    "LoadBalanceTarget",
    "RetryConfig",
    "RouteCondition",
    "RoutingCondition",
    "Target",
    "TimeoutConfig",
    "TrafficMirrorConfig",
    "create_headers",
]
