"""Deprecated released gateway config adapters and header serialization.

The released full config is serialized without dropping fields. Cache
TTL/namespace/force_refresh and timeout.total also retain the lane's wire headers.
Serialization does not promise that a particular gateway supports every override;
unsupported legacy options warn, and response config_ignored remains observable.
"""

from __future__ import annotations

import json
import warnings
from dataclasses import dataclass, field
from typing import Any

from fi.gateway._constants import HEADER_GUARDRAIL_POLICY
from fi.gateway._deprecation import deprecated, deprecated_options


@deprecated
@dataclass
class FallbackTarget:
    model: str
    provider: str | None = None
    override_params: dict[str, Any] | None = None


@deprecated
@dataclass
class FallbackConfig:
    targets: list[FallbackTarget] = field(default_factory=list)
    on_status_codes: list[int] | None = None

    def __post_init__(self) -> None:
        if self.on_status_codes is None:
            self.on_status_codes = [429, 500, 502, 503, 504]


@deprecated
@dataclass
class LoadBalanceTarget:
    model: str
    provider: str | None = None
    weight: float = 1.0
    virtual_key: str | None = None


@deprecated
@dataclass
class LoadBalanceConfig:
    strategy: str = "round_robin"
    targets: list[LoadBalanceTarget] | None = None


@deprecated_options("enabled", "strategy", "semantic_threshold", "cache_by_model", "ignore_keys", positional=True)
@dataclass
class CacheConfig:
    # Released positional order is intentional.
    enabled: bool = True
    strategy: str = "exact"
    ttl: int | None = None
    namespace: str | None = None
    force_refresh: bool = False
    semantic_threshold: float | None = None
    cache_by_model: bool = True
    ignore_keys: list[str] | None = None


@deprecated
@dataclass
class GuardrailCheck:
    name: str
    enabled: bool = True
    action: str = "block"
    confidence_threshold: float = 0.8
    config: dict[str, Any] | None = None


@deprecated
@dataclass
class GuardrailConfig:
    input_guardrails: list[str] | None = None
    output_guardrails: list[str] | None = None
    deny: bool = True
    async_mode: bool = False
    sequential: bool = False
    checks: list[GuardrailCheck] | None = None
    pipeline_mode: str | None = None
    fail_open: bool = False
    timeout_ms: int | None = None


@deprecated
@dataclass
class RoutingCondition:
    field: str
    operator: str
    value: Any
    target: str


@deprecated
@dataclass
class ConditionalRoutingConfig:
    conditions: list[RoutingCondition] = field(default_factory=list)
    default_target: str | None = None


@deprecated
@dataclass
class TrafficMirrorConfig:
    enabled: bool = True
    target_model: str | None = None
    target_provider: str | None = None
    sample_rate: float = 1.0


@deprecated
@dataclass
class RetryConfig:
    max_retries: int = 2
    on_status_codes: list[int] | None = None
    backoff_factor: float = 0.5
    backoff_max: float = 30.0
    backoff_jitter: float = 0.25
    respect_retry_after: bool = True
    max_retry_wait: float = 60.0

    def __post_init__(self) -> None:
        if self.on_status_codes is None:
            self.on_status_codes = [429, 500, 502, 503]


@deprecated_options("connect", "read", "write", "pool", positional=True)
@dataclass
class TimeoutConfig:
    """Released field order; only total controls the gateway request timeout.

    For client-side timeouts use fi.gateway.Timeout via the client's timeout=.
    """

    connect: float | None = None
    read: float | None = None
    write: float | None = None
    pool: float | None = None
    total: float | None = None


def _to_serializable(obj: Any) -> Any:
    if hasattr(obj, "__dataclass_fields__"):
        return {
            k: _to_serializable(getattr(obj, k))
            for k in obj.__dataclass_fields__ if getattr(obj, k) is not None
        }
    if isinstance(obj, list):
        return [_to_serializable(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    return obj


@deprecated_options("fallback", "load_balance", "guardrails", "routing", "mirror", "retry", positional=True)
@dataclass
class GatewayConfig:
    """Released constructor and inspection API; safe serialization on lane transports."""

    fallback: FallbackConfig | None = None
    load_balance: LoadBalanceConfig | None = None
    cache: CacheConfig | None = None
    guardrails: GuardrailConfig | None = None
    routing: ConditionalRoutingConfig | None = None
    mirror: TrafficMirrorConfig | None = None
    retry: RetryConfig | None = None
    timeout: TimeoutConfig | None = None

    def to_dict(self) -> dict[str, Any]:
        return _to_serializable(self)

    def to_headers(self) -> dict[str, str]:
        ignored = [
            name for name in ("fallback", "load_balance", "guardrails", "routing", "mirror", "retry")
            if getattr(self, name) is not None
        ]
        if self.cache is not None:
            defaults = CacheConfig()
            ignored.extend(
                f"cache.{name}" for name in
                ("enabled", "strategy", "semantic_threshold", "cache_by_model", "ignore_keys")
                if getattr(self.cache, name) != getattr(defaults, name)
            )
        if self.timeout is not None:
            ignored.extend(
                f"timeout.{name}" for name in ("connect", "read", "write", "pool")
                if getattr(self.timeout, name) is not None
            )
        if ignored:
            warnings.warn(
                "Deprecated gateway config adapter: legacy fields are serialized "
                "as released, but backend support is not guaranteed: "
                + ", ".join(ignored)
                + ". Check response config_ignored; configure unsupported features "
                "on the gateway instead.",
                DeprecationWarning, stacklevel=2,
            )
        headers: dict[str, str] = {}
        config_dict = self.to_dict()
        if not config_dict:
            return headers
        headers["x-agentcc-config"] = json.dumps(config_dict, separators=(",", ":"))
        if self.cache is not None:
            if self.cache.ttl is not None:
                headers["x-agentcc-cache-ttl"] = str(self.cache.ttl)
            if self.cache.namespace is not None:
                headers["x-agentcc-cache-namespace"] = self.cache.namespace
            if self.cache.force_refresh:
                headers["x-agentcc-cache-force-refresh"] = "true"
        if self.guardrails is not None:
            policies = list(self.guardrails.input_guardrails or [])
            policies.extend(self.guardrails.output_guardrails or [])
            if policies:
                headers["x-agentcc-guardrail-policy"] = ",".join(policies)
        if self.timeout is not None and self.timeout.total is not None:
            headers["x-agentcc-request-timeout"] = str(int(self.timeout.total * 1000))
        return headers


def create_headers(
    api_key: str | None = None,
    config: GatewayConfig | None = None,
    trace_id: str | None = None,
    session_id: str | None = None,
    session_name: str | None = None,
    session_path: str | None = None,
    metadata: dict[str, Any] | None = None,
    user_id: str | None = None,
    request_id: str | None = None,
    cache_ttl: int | None = None,
    cache_namespace: str | None = None,
    cache_force_refresh: bool | None = None,
    guardrail_policy: str | None = None,
    properties: dict[str, str] | None = None,
) -> dict[str, str]:
    """Build gateway headers for an OpenAI-compatible client without sending them.

    Only gateway virtual keys are allowed; platform FI key pair values are refused.
    """
    headers: dict[str, str] = {}
    if api_key is not None:
        from fi.gateway._env import guard_fi_key_pair

        guard_fi_key_pair(api_key)
        headers["Authorization"] = f"Bearer {api_key}"
    for name, value in (
        ("x-agentcc-trace-id", trace_id), ("x-agentcc-session-id", session_id),
        ("x-agentcc-session-name", session_name), ("x-agentcc-session-path", session_path),
        ("x-agentcc-user-id", user_id), ("x-agentcc-request-id", request_id),
        ("x-agentcc-cache-namespace", cache_namespace),
    ):
        if value is not None:
            headers[name] = value
    if metadata is not None:
        headers["x-agentcc-metadata"] = json.dumps(metadata, separators=(",", ":"))
    if cache_ttl is not None:
        headers["x-agentcc-cache-ttl"] = str(cache_ttl)
    if cache_force_refresh:
        headers["x-agentcc-cache-force-refresh"] = "true"
    if guardrail_policy is not None:
        headers[HEADER_GUARDRAIL_POLICY] = guardrail_policy
    if properties is not None:
        for key, value in properties.items():
            headers[f"x-agentcc-property-{key}"] = value
    if config is not None:
        headers.update(config.to_headers())
    return headers
