"""Gateway configuration dataclasses and header-serialization helpers.

These config objects let users configure gateway behaviour (fallback, load
balancing, caching, guardrails, routing, traffic mirroring, retry, timeouts)
from SDK code.  Each sub-config serialises to ``x-agentcc-*`` headers that the
AgentCC Gateway interprets on the hot path.

The gateway uses a multi-tenant OrgConfig model.  Per-org config (providers,
guardrails, routing) is pushed from Django to the gateway at deploy time.
SDK config objects represent **per-request overrides** that layer on top:

    request header  >  per-key  >  per-org  >  global
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Fallback
# ---------------------------------------------------------------------------


@dataclass
class FallbackTarget:
    """A single fallback model target."""

    model: str
    provider: str | None = None
    override_params: dict[str, Any] | None = None


@dataclass
class FallbackConfig:
    """Configuration for automatic model fallback on errors.

    Maps to the gateway's ``RoutingConfig.FallbackEnabled``,
    ``FallbackStatusCodes``, and ``ModelFallbacks`` fields.
    """

    targets: list[FallbackTarget] = field(default_factory=list)
    on_status_codes: list[int] | None = None

    def __post_init__(self) -> None:
        if self.on_status_codes is None:
            self.on_status_codes = [429, 500, 502, 503, 504]


# ---------------------------------------------------------------------------
# Load balancing
# ---------------------------------------------------------------------------


@dataclass
class LoadBalanceTarget:
    """A single target in a load-balanced pool."""

    model: str
    provider: str | None = None
    weight: float = 1.0
    virtual_key: str | None = None


@dataclass
class LoadBalanceConfig:
    """Configuration for load balancing across multiple models/providers.

    Maps to the gateway's ``RoutingConfig.Strategy`` field.

    Strategies: ``round_robin``, ``weighted``, ``least_latency``,
    ``cost_optimized``.
    """

    strategy: str = "round_robin"
    targets: list[LoadBalanceTarget] | None = None


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------


@dataclass
class CacheConfig:
    """Configuration for the gateway response cache."""

    enabled: bool = True
    strategy: str = "exact"  # "exact" or "semantic"
    ttl: int | None = None  # seconds
    namespace: str | None = None
    force_refresh: bool = False
    semantic_threshold: float | None = None  # 0-1
    cache_by_model: bool = True
    ignore_keys: list[str] | None = None


# ---------------------------------------------------------------------------
# Guardrails
# ---------------------------------------------------------------------------


@dataclass
class GuardrailCheck:
    """A single guardrail check configuration.

    Maps to the gateway's ``GuardrailCheck`` struct with ``enabled``,
    ``action``, ``confidence_threshold``, and ``config`` fields.
    """

    name: str
    enabled: bool = True
    action: str = "block"  # "block", "warn", "mask", "log"
    confidence_threshold: float = 0.8
    config: dict[str, Any] | None = None


@dataclass
class GuardrailConfig:
    """Configuration for input/output guardrails.

    Supports both simple policy-ID mode (``input_guardrails`` /
    ``output_guardrails``) and structured check mode (``checks``) that
    matches the gateway's ``GuardrailConfig`` with per-check settings.
    """

    input_guardrails: list[str] | None = None  # guardrail policy IDs
    output_guardrails: list[str] | None = None
    deny: bool = True  # True=block, False=warn
    async_mode: bool = False
    sequential: bool = False
    # Structured checks (maps to gateway's checks map)
    checks: list[GuardrailCheck] | None = None
    pipeline_mode: str | None = None  # "parallel" or "sequential"
    fail_open: bool = False
    timeout_ms: int | None = None


# ---------------------------------------------------------------------------
# Conditional routing
# ---------------------------------------------------------------------------


@dataclass
class RoutingCondition:
    """A single conditional routing rule.

    ``operator`` is one of: ``$eq``, ``$ne``, ``$in``, ``$nin``, ``$regex``,
    ``$gt``, ``$gte``, ``$lt``, ``$lte``.

    Maps to the gateway's ``ConditionalRoute`` struct.
    """

    field: str  # e.g. "metadata.tier"
    operator: str  # e.g. "$eq"
    value: Any
    target: str


@dataclass
class ConditionalRoutingConfig:
    """Configuration for conditional (rule-based) routing.

    Maps to the gateway's ``RoutingConfig.ConditionalRoutes`` and
    ``DefaultModel`` fields.
    """

    conditions: list[RoutingCondition] = field(default_factory=list)
    default_target: str | None = None


# ---------------------------------------------------------------------------
# Traffic mirroring
# ---------------------------------------------------------------------------


@dataclass
class TrafficMirrorConfig:
    """Configuration for traffic mirroring (shadow traffic)."""

    enabled: bool = True
    target_model: str | None = None
    target_provider: str | None = None
    sample_rate: float = 1.0  # 0-1


# ---------------------------------------------------------------------------
# Retry
# ---------------------------------------------------------------------------


@dataclass
class RetryConfig:
    """Per-request retry configuration.

    Controls how many times the gateway retries failed requests and under
    what conditions.
    """

    max_retries: int = 2
    on_status_codes: list[int] | None = None
    backoff_factor: float = 0.5
    backoff_max: float = 30.0
    backoff_jitter: float = 0.25
    respect_retry_after: bool = True
    max_retry_wait: float = 60.0  # max cumulative wait seconds

    def __post_init__(self) -> None:
        if self.on_status_codes is None:
            self.on_status_codes = [429, 500, 502, 503]


# ---------------------------------------------------------------------------
# Timeout
# ---------------------------------------------------------------------------


@dataclass
class TimeoutConfig:
    """Granular per-request timeout configuration.

    All values are in seconds.
    """

    connect: float | None = None
    read: float | None = None
    write: float | None = None
    pool: float | None = None
    total: float | None = None


# ---------------------------------------------------------------------------
# Top-level gateway config
# ---------------------------------------------------------------------------


def _to_serializable(obj: Any) -> Any:
    """Recursively convert dataclass instances to plain dicts."""
    if hasattr(obj, "__dataclass_fields__"):
        result: dict[str, Any] = {}
        for k in obj.__dataclass_fields__:
            v = getattr(obj, k)
            if v is not None:
                result[k] = _to_serializable(v)
        return result
    if isinstance(obj, list):
        return [_to_serializable(item) for item in obj]
    return obj


@dataclass
class GatewayConfig:
    """Top-level gateway configuration aggregating all sub-configs.

    These are **per-request overrides** that layer on top of the org-level
    config stored in the gateway.  The gateway applies them with priority::

        request header  >  per-key  >  per-org  >  global

    Usage::

        config = GatewayConfig(
            cache=CacheConfig(ttl=300, namespace="prod"),
            fallback=FallbackConfig(targets=[
                FallbackTarget(model="gpt-4o-mini"),
            ]),
            retry=RetryConfig(max_retries=3),
        )
        headers = config.to_headers()
    """

    fallback: FallbackConfig | None = None
    load_balance: LoadBalanceConfig | None = None
    cache: CacheConfig | None = None
    guardrails: GuardrailConfig | None = None
    routing: ConditionalRoutingConfig | None = None
    mirror: TrafficMirrorConfig | None = None
    retry: RetryConfig | None = None
    timeout: TimeoutConfig | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to a JSON-serialisable dictionary, omitting None values."""
        return _to_serializable(self)  # type: ignore[return-value]

    def to_headers(self) -> dict[str, str]:
        """Serialise config to ``x-agentcc-*`` HTTP headers.

        The full config is placed in ``x-agentcc-config`` as JSON. Individual
        backward-compatible headers are also emitted for cache, guardrail,
        retry, and timeout settings.
        """
        headers: dict[str, str] = {}
        config_dict = self.to_dict()

        if not config_dict:
            return headers

        # Full JSON blob
        headers["x-agentcc-config"] = json.dumps(config_dict, separators=(",", ":"))

        # Backward-compatible individual headers
        if self.cache is not None:
            if self.cache.ttl is not None:
                headers["x-agentcc-cache-ttl"] = str(self.cache.ttl)
            if self.cache.namespace is not None:
                headers["x-agentcc-cache-namespace"] = self.cache.namespace
            if self.cache.force_refresh:
                headers["x-agentcc-cache-force-refresh"] = "true"

        if self.guardrails is not None:
            policies: list[str] = []
            if self.guardrails.input_guardrails:
                policies.extend(self.guardrails.input_guardrails)
            if self.guardrails.output_guardrails:
                policies.extend(self.guardrails.output_guardrails)
            if policies:
                headers["x-agentcc-guardrail-policy"] = ",".join(policies)

        if self.timeout is not None and self.timeout.total is not None:
            headers["x-agentcc-request-timeout"] = str(int(self.timeout.total * 1000))

        return headers


# ---------------------------------------------------------------------------
# create_headers() helper
# ---------------------------------------------------------------------------


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
    """Build a dict of ``x-agentcc-*`` headers suitable for any OpenAI SDK.

    This is the primary entry point for users who want to use AgentCC gateway
    features without migrating away from the ``openai`` package::

        from openai import OpenAI
        import fi.gateway as agentcc

        headers = agentcc.create_headers(
            api_key="sk-...",
            config=agentcc.GatewayConfig(
                cache=agentcc.CacheConfig(ttl=300),
                retry=agentcc.RetryConfig(max_retries=3),
            ),
            trace_id="abc",
            user_id="user-42",
        )
        client = OpenAI(
            base_url=agentcc.AGENTCC_GATEWAY_URL,
            default_headers=headers,
        )
    """
    headers: dict[str, str] = {}

    if api_key is not None:
        headers["Authorization"] = f"Bearer {api_key}"

    if trace_id is not None:
        headers["x-agentcc-trace-id"] = trace_id

    if session_id is not None:
        headers["x-agentcc-session-id"] = session_id

    if session_name is not None:
        headers["x-agentcc-session-name"] = session_name

    if session_path is not None:
        headers["x-agentcc-session-path"] = session_path

    if metadata is not None:
        headers["x-agentcc-metadata"] = json.dumps(metadata, separators=(",", ":"))

    if user_id is not None:
        headers["x-agentcc-user-id"] = user_id

    if request_id is not None:
        headers["x-agentcc-request-id"] = request_id

    if cache_ttl is not None:
        headers["x-agentcc-cache-ttl"] = str(cache_ttl)

    if cache_namespace is not None:
        headers["x-agentcc-cache-namespace"] = cache_namespace

    if cache_force_refresh is not None and cache_force_refresh:
        headers["x-agentcc-cache-force-refresh"] = "true"

    if guardrail_policy is not None:
        headers["x-agentcc-guardrail-policy"] = guardrail_policy

    if properties is not None:
        for key, value in properties.items():
            headers[f"x-agentcc-property-{key}"] = value

    # Merge config headers (config.to_headers() takes precedence for overlaps)
    if config is not None:
        config_headers = config.to_headers()
        headers.update(config_headers)

    return headers
