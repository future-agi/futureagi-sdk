"""Tests for gateway configuration dataclasses, serialization, and create_headers."""

from __future__ import annotations

import json

# ============================================================================
# Config construction tests
# ============================================================================


class TestGatewayConfigConstruction:
    def test_gateway_config_empty(self) -> None:
        from fi.gateway._gateway_config import GatewayConfig

        cfg = GatewayConfig()
        assert cfg.fallback is None
        assert cfg.load_balance is None
        assert cfg.cache is None
        assert cfg.guardrails is None
        assert cfg.routing is None
        assert cfg.mirror is None

    def test_gateway_config_with_fallback(self) -> None:
        from fi.gateway._gateway_config import FallbackConfig, FallbackTarget, GatewayConfig

        cfg = GatewayConfig(
            fallback=FallbackConfig(
                targets=[FallbackTarget(model="gpt-4o-mini")],
            )
        )
        assert cfg.fallback is not None
        assert len(cfg.fallback.targets) == 1
        assert cfg.fallback.targets[0].model == "gpt-4o-mini"

    def test_gateway_config_with_load_balance(self) -> None:
        from fi.gateway._gateway_config import GatewayConfig, LoadBalanceConfig, LoadBalanceTarget

        cfg = GatewayConfig(
            load_balance=LoadBalanceConfig(
                strategy="weighted",
                targets=[
                    LoadBalanceTarget(model="gpt-4o", weight=0.7),
                    LoadBalanceTarget(model="gpt-4o-mini", weight=0.3),
                ],
            )
        )
        assert cfg.load_balance is not None
        assert cfg.load_balance.strategy == "weighted"
        assert len(cfg.load_balance.targets) == 2

    def test_gateway_config_with_cache(self) -> None:
        from fi.gateway._gateway_config import CacheConfig, GatewayConfig

        cfg = GatewayConfig(cache=CacheConfig(ttl=300, namespace="prod"))
        assert cfg.cache is not None
        assert cfg.cache.ttl == 300
        assert cfg.cache.namespace == "prod"
        assert cfg.cache.enabled is True

    def test_gateway_config_with_guardrails(self) -> None:
        from fi.gateway._gateway_config import GatewayConfig, GuardrailConfig

        cfg = GatewayConfig(
            guardrails=GuardrailConfig(
                input_guardrails=["prompt-guard", "pii-filter"],
                deny=True,
            )
        )
        assert cfg.guardrails is not None
        assert cfg.guardrails.input_guardrails == ["prompt-guard", "pii-filter"]
        assert cfg.guardrails.deny is True

    def test_gateway_config_with_routing(self) -> None:
        from fi.gateway._gateway_config import ConditionalRoutingConfig, GatewayConfig, RoutingCondition

        cfg = GatewayConfig(
            routing=ConditionalRoutingConfig(
                conditions=[
                    RoutingCondition(
                        field="metadata.tier",
                        operator="$eq",
                        value="premium",
                        target="gpt-4o",
                    )
                ],
                default_target="gpt-4o-mini",
            )
        )
        assert cfg.routing is not None
        assert len(cfg.routing.conditions) == 1
        assert cfg.routing.default_target == "gpt-4o-mini"

    def test_gateway_config_with_mirror(self) -> None:
        from fi.gateway._gateway_config import GatewayConfig, TrafficMirrorConfig

        cfg = GatewayConfig(
            mirror=TrafficMirrorConfig(
                target_model="claude-3-haiku",
                sample_rate=0.1,
            )
        )
        assert cfg.mirror is not None
        assert cfg.mirror.target_model == "claude-3-haiku"
        assert cfg.mirror.sample_rate == 0.1
        assert cfg.mirror.enabled is True

    def test_gateway_config_full(self) -> None:
        from fi.gateway._gateway_config import (
            CacheConfig,
            ConditionalRoutingConfig,
            FallbackConfig,
            FallbackTarget,
            GatewayConfig,
            GuardrailConfig,
            LoadBalanceConfig,
            LoadBalanceTarget,
            RoutingCondition,
            TrafficMirrorConfig,
        )

        cfg = GatewayConfig(
            fallback=FallbackConfig(
                targets=[FallbackTarget(model="gpt-4o-mini")],
            ),
            load_balance=LoadBalanceConfig(
                strategy="weighted",
                targets=[LoadBalanceTarget(model="gpt-4o", weight=0.8)],
            ),
            cache=CacheConfig(ttl=300, namespace="prod"),
            guardrails=GuardrailConfig(
                input_guardrails=["prompt-guard"],
                output_guardrails=["content-filter"],
            ),
            routing=ConditionalRoutingConfig(
                conditions=[
                    RoutingCondition(
                        field="metadata.tier",
                        operator="$eq",
                        value="premium",
                        target="gpt-4o",
                    )
                ],
                default_target="gpt-4o-mini",
            ),
            mirror=TrafficMirrorConfig(target_model="claude-3-haiku", sample_rate=0.05),
        )
        assert cfg.fallback is not None
        assert cfg.load_balance is not None
        assert cfg.cache is not None
        assert cfg.guardrails is not None
        assert cfg.routing is not None
        assert cfg.mirror is not None


# ============================================================================
# Serialization tests
# ============================================================================


class TestGatewayConfigSerialization:
    def test_gateway_config_to_headers_empty(self) -> None:
        from fi.gateway._gateway_config import GatewayConfig

        cfg = GatewayConfig()
        headers = cfg.to_headers()
        assert headers == {}

    def test_gateway_config_to_headers_cache(self) -> None:
        from fi.gateway._gateway_config import CacheConfig, GatewayConfig

        cfg = GatewayConfig(cache=CacheConfig(ttl=300, namespace="prod", force_refresh=True))
        headers = cfg.to_headers()
        assert "x-agentcc-config" in headers
        assert headers["x-agentcc-cache-ttl"] == "300"
        assert headers["x-agentcc-cache-namespace"] == "prod"
        assert headers["x-agentcc-cache-force-refresh"] == "true"

    def test_gateway_config_to_headers_full(self) -> None:
        from fi.gateway._gateway_config import (
            CacheConfig,
            FallbackConfig,
            FallbackTarget,
            GatewayConfig,
            GuardrailConfig,
        )

        cfg = GatewayConfig(
            fallback=FallbackConfig(targets=[FallbackTarget(model="gpt-4o-mini")]),
            cache=CacheConfig(ttl=600),
            guardrails=GuardrailConfig(input_guardrails=["pii-filter"]),
        )
        headers = cfg.to_headers()
        assert "x-agentcc-config" in headers
        config_data = json.loads(headers["x-agentcc-config"])
        assert "fallback" in config_data
        assert "cache" in config_data
        assert "guardrails" in config_data
        assert headers["x-agentcc-cache-ttl"] == "600"
        assert headers["x-agentcc-guardrail-policy"] == "pii-filter"

    def test_gateway_config_to_dict(self) -> None:
        from fi.gateway._gateway_config import CacheConfig, GatewayConfig

        cfg = GatewayConfig(cache=CacheConfig(ttl=300, namespace="prod"))
        d = cfg.to_dict()
        assert isinstance(d, dict)
        assert "cache" in d
        assert d["cache"]["ttl"] == 300
        assert d["cache"]["namespace"] == "prod"

    def test_gateway_config_to_headers_skips_none(self) -> None:
        from fi.gateway._gateway_config import CacheConfig, GatewayConfig

        cfg = GatewayConfig(cache=CacheConfig(enabled=True))
        headers = cfg.to_headers()
        # x-agentcc-config should exist (because cache has non-None fields)
        assert "x-agentcc-config" in headers
        config_data = json.loads(headers["x-agentcc-config"])
        # ttl is None so it should not be in the serialised dict
        assert "ttl" not in config_data.get("cache", {})
        # namespace is None, so no individual header
        assert "x-agentcc-cache-namespace" not in headers
        assert "x-agentcc-cache-ttl" not in headers
        # force_refresh is False so no individual header
        assert "x-agentcc-cache-force-refresh" not in headers


# ============================================================================
# create_headers tests
# ============================================================================


class TestCreateHeaders:
    def test_create_headers_basic(self) -> None:
        from fi.gateway._gateway_config import create_headers

        headers = create_headers(api_key="sk-test-123")
        assert headers["Authorization"] == "Bearer sk-test-123"
        assert len(headers) == 1

    def test_create_headers_with_config(self) -> None:
        from fi.gateway._gateway_config import CacheConfig, GatewayConfig, create_headers

        cfg = GatewayConfig(cache=CacheConfig(ttl=120))
        headers = create_headers(api_key="sk-test", config=cfg)
        assert headers["Authorization"] == "Bearer sk-test"
        assert "x-agentcc-config" in headers
        assert headers["x-agentcc-cache-ttl"] == "120"

    def test_create_headers_with_trace_and_session(self) -> None:
        from fi.gateway._gateway_config import create_headers

        headers = create_headers(
            api_key="sk-test",
            trace_id="trace-abc",
            session_id="sess-xyz",
        )
        assert headers["x-agentcc-trace-id"] == "trace-abc"
        assert headers["x-agentcc-session-id"] == "sess-xyz"

    def test_create_headers_with_metadata(self) -> None:
        from fi.gateway._gateway_config import create_headers

        headers = create_headers(
            api_key="sk-test",
            metadata={"env": "production", "tier": "premium"},
        )
        meta = json.loads(headers["x-agentcc-metadata"])
        assert meta["env"] == "production"
        assert meta["tier"] == "premium"

    def test_create_headers_with_properties(self) -> None:
        from fi.gateway._gateway_config import create_headers

        headers = create_headers(
            api_key="sk-test",
            properties={"team": "ml", "project": "chatbot"},
        )
        assert headers["x-agentcc-property-team"] == "ml"
        assert headers["x-agentcc-property-project"] == "chatbot"

    def test_create_headers_with_user_id(self) -> None:
        from fi.gateway._gateway_config import create_headers

        headers = create_headers(api_key="sk-test", user_id="user-42")
        assert headers["x-agentcc-user-id"] == "user-42"

    def test_create_headers_with_cache_params(self) -> None:
        from fi.gateway._gateway_config import create_headers

        headers = create_headers(
            cache_ttl=600,
            cache_namespace="staging",
            cache_force_refresh=True,
        )
        assert headers["x-agentcc-cache-ttl"] == "600"
        assert headers["x-agentcc-cache-namespace"] == "staging"
        assert headers["x-agentcc-cache-force-refresh"] == "true"

    def test_create_headers_all_params(self) -> None:
        from fi.gateway._gateway_config import CacheConfig, GatewayConfig, create_headers

        cfg = GatewayConfig(cache=CacheConfig(ttl=300))
        headers = create_headers(
            api_key="sk-all",
            config=cfg,
            trace_id="t-1",
            session_id="s-1",
            session_name="my-session",
            session_path="/path/to/session",
            metadata={"key": "value"},
            user_id="u-1",
            cache_ttl=100,
            cache_namespace="ns",
            cache_force_refresh=True,
            guardrail_policy="pg-1",
            properties={"org": "acme"},
        )
        assert headers["Authorization"] == "Bearer sk-all"
        assert headers["x-agentcc-trace-id"] == "t-1"
        assert headers["x-agentcc-session-id"] == "s-1"
        assert headers["x-agentcc-session-name"] == "my-session"
        assert headers["x-agentcc-session-path"] == "/path/to/session"
        assert "x-agentcc-metadata" in headers
        assert headers["x-agentcc-user-id"] == "u-1"
        assert headers["x-agentcc-property-org"] == "acme"
        # Config headers override individual params for cache
        assert headers["x-agentcc-cache-ttl"] == "300"
        assert "x-agentcc-config" in headers


# ============================================================================
# FallbackConfig tests
# ============================================================================


class TestFallbackConfig:
    def test_fallback_config_with_targets(self) -> None:
        from fi.gateway._gateway_config import FallbackConfig, FallbackTarget

        cfg = FallbackConfig(
            targets=[
                FallbackTarget(model="gpt-4o-mini"),
                FallbackTarget(model="claude-3-haiku", provider="anthropic"),
            ]
        )
        assert len(cfg.targets) == 2
        assert cfg.targets[0].model == "gpt-4o-mini"
        assert cfg.targets[0].provider is None
        assert cfg.targets[1].provider == "anthropic"
        # Default status codes
        assert cfg.on_status_codes == [429, 500, 502, 503, 504]

    def test_fallback_config_custom_status_codes(self) -> None:
        from fi.gateway._gateway_config import FallbackConfig, FallbackTarget

        cfg = FallbackConfig(
            targets=[FallbackTarget(model="gpt-4o-mini")],
            on_status_codes=[500, 503],
        )
        assert cfg.on_status_codes == [500, 503]

    def test_fallback_target_with_override_params(self) -> None:
        from fi.gateway._gateway_config import FallbackTarget

        target = FallbackTarget(
            model="gpt-4o-mini",
            override_params={"temperature": 0.5, "max_tokens": 100},
        )
        assert target.override_params is not None
        assert target.override_params["temperature"] == 0.5
        assert target.override_params["max_tokens"] == 100


# ============================================================================
# LoadBalanceConfig tests
# ============================================================================


class TestLoadBalanceConfig:
    def test_load_balance_weighted(self) -> None:
        from fi.gateway._gateway_config import LoadBalanceConfig, LoadBalanceTarget

        cfg = LoadBalanceConfig(
            strategy="weighted",
            targets=[
                LoadBalanceTarget(model="gpt-4o", weight=0.7),
                LoadBalanceTarget(model="gpt-4o-mini", weight=0.3),
            ],
        )
        assert cfg.strategy == "weighted"
        assert cfg.targets is not None
        assert len(cfg.targets) == 2
        assert cfg.targets[0].weight == 0.7
        assert cfg.targets[1].weight == 0.3

    def test_load_balance_least_latency(self) -> None:
        from fi.gateway._gateway_config import LoadBalanceConfig, LoadBalanceTarget

        cfg = LoadBalanceConfig(
            strategy="least_latency",
            targets=[
                LoadBalanceTarget(model="gpt-4o"),
                LoadBalanceTarget(model="claude-3-sonnet"),
            ],
        )
        assert cfg.strategy == "least_latency"
        assert cfg.targets is not None
        assert len(cfg.targets) == 2

    def test_load_balance_cost_optimized(self) -> None:
        from fi.gateway._gateway_config import LoadBalanceConfig, LoadBalanceTarget

        cfg = LoadBalanceConfig(
            strategy="cost_optimized",
            targets=[
                LoadBalanceTarget(model="gpt-4o", provider="openai"),
                LoadBalanceTarget(model="gpt-4o", provider="azure"),
            ],
        )
        assert cfg.strategy == "cost_optimized"
        assert cfg.targets is not None
        assert cfg.targets[0].provider == "openai"
        assert cfg.targets[1].provider == "azure"


# ============================================================================
# CacheConfig tests
# ============================================================================


class TestCacheConfig:
    def test_cache_config_exact(self) -> None:
        from fi.gateway._gateway_config import CacheConfig

        cfg = CacheConfig(ttl=300)
        assert cfg.strategy == "exact"
        assert cfg.ttl == 300
        assert cfg.enabled is True
        assert cfg.cache_by_model is True
        assert cfg.semantic_threshold is None

    def test_cache_config_semantic_with_threshold(self) -> None:
        from fi.gateway._gateway_config import CacheConfig

        cfg = CacheConfig(strategy="semantic", semantic_threshold=0.85, ttl=600)
        assert cfg.strategy == "semantic"
        assert cfg.semantic_threshold == 0.85
        assert cfg.ttl == 600

    def test_cache_config_with_ignore_keys(self) -> None:
        from fi.gateway._gateway_config import CacheConfig

        cfg = CacheConfig(ignore_keys=["timestamp", "request_id"])
        assert cfg.ignore_keys == ["timestamp", "request_id"]


# ============================================================================
# GuardrailConfig tests
# ============================================================================


class TestGuardrailConfig:
    def test_guardrail_config_input_only(self) -> None:
        from fi.gateway._gateway_config import GuardrailConfig

        cfg = GuardrailConfig(input_guardrails=["prompt-guard", "pii-filter"])
        assert cfg.input_guardrails == ["prompt-guard", "pii-filter"]
        assert cfg.output_guardrails is None
        assert cfg.deny is True

    def test_guardrail_config_input_and_output(self) -> None:
        from fi.gateway._gateway_config import GuardrailConfig

        cfg = GuardrailConfig(
            input_guardrails=["prompt-guard"],
            output_guardrails=["content-filter", "toxicity-check"],
        )
        assert cfg.input_guardrails == ["prompt-guard"]
        assert cfg.output_guardrails == ["content-filter", "toxicity-check"]

    def test_guardrail_config_warn_mode(self) -> None:
        from fi.gateway._gateway_config import GuardrailConfig

        cfg = GuardrailConfig(
            input_guardrails=["prompt-guard"],
            deny=False,
        )
        assert cfg.deny is False

    def test_guardrail_config_async(self) -> None:
        from fi.gateway._gateway_config import GuardrailConfig

        cfg = GuardrailConfig(
            input_guardrails=["prompt-guard"],
            async_mode=True,
            sequential=True,
        )
        assert cfg.async_mode is True
        assert cfg.sequential is True


# ============================================================================
# RoutingCondition tests
# ============================================================================


class TestRoutingCondition:
    def test_routing_condition_eq(self) -> None:
        from fi.gateway._gateway_config import RoutingCondition

        cond = RoutingCondition(
            field="metadata.tier",
            operator="$eq",
            value="premium",
            target="gpt-4o",
        )
        assert cond.field == "metadata.tier"
        assert cond.operator == "$eq"
        assert cond.value == "premium"
        assert cond.target == "gpt-4o"

    def test_routing_condition_in(self) -> None:
        from fi.gateway._gateway_config import RoutingCondition

        cond = RoutingCondition(
            field="metadata.region",
            operator="$in",
            value=["us-east", "us-west"],
            target="gpt-4o",
        )
        assert cond.operator == "$in"
        assert cond.value == ["us-east", "us-west"]

    def test_routing_condition_regex(self) -> None:
        from fi.gateway._gateway_config import RoutingCondition

        cond = RoutingCondition(
            field="metadata.user_agent",
            operator="$regex",
            value="^Mozilla.*",
            target="gpt-4o-mini",
        )
        assert cond.operator == "$regex"
        assert cond.value == "^Mozilla.*"


# ============================================================================
# RetryConfig tests
# ============================================================================


class TestRetryConfig:
    def test_retry_config_defaults(self) -> None:
        from fi.gateway._gateway_config import RetryConfig

        cfg = RetryConfig()
        assert cfg.max_retries == 2
        assert cfg.on_status_codes == [429, 500, 502, 503]
        assert cfg.backoff_factor == 0.5
        assert cfg.backoff_max == 30.0
        assert cfg.backoff_jitter == 0.25
        assert cfg.respect_retry_after is True
        assert cfg.max_retry_wait == 60.0

    def test_retry_config_custom(self) -> None:
        from fi.gateway._gateway_config import RetryConfig

        cfg = RetryConfig(
            max_retries=5,
            on_status_codes=[500, 503],
            backoff_factor=1.0,
            max_retry_wait=120.0,
        )
        assert cfg.max_retries == 5
        assert cfg.on_status_codes == [500, 503]
        assert cfg.backoff_factor == 1.0
        assert cfg.max_retry_wait == 120.0

    def test_retry_config_no_retries(self) -> None:
        from fi.gateway._gateway_config import RetryConfig

        cfg = RetryConfig(max_retries=0)
        assert cfg.max_retries == 0

    def test_retry_config_in_gateway_config(self) -> None:
        from fi.gateway._gateway_config import GatewayConfig, RetryConfig

        cfg = GatewayConfig(retry=RetryConfig(max_retries=3))
        assert cfg.retry is not None
        assert cfg.retry.max_retries == 3

    def test_retry_config_serializes_to_headers(self) -> None:
        from fi.gateway._gateway_config import GatewayConfig, RetryConfig

        cfg = GatewayConfig(retry=RetryConfig(max_retries=4, backoff_factor=1.0))
        headers = cfg.to_headers()
        assert "x-agentcc-config" in headers
        config_data = json.loads(headers["x-agentcc-config"])
        assert "retry" in config_data
        assert config_data["retry"]["max_retries"] == 4
        assert config_data["retry"]["backoff_factor"] == 1.0

    def test_retry_config_to_dict(self) -> None:
        from fi.gateway._gateway_config import GatewayConfig, RetryConfig

        cfg = GatewayConfig(retry=RetryConfig(max_retries=3))
        d = cfg.to_dict()
        assert "retry" in d
        assert d["retry"]["max_retries"] == 3


# ============================================================================
# TimeoutConfig tests
# ============================================================================


class TestTimeoutConfig:
    def test_timeout_config_empty(self) -> None:
        from fi.gateway._gateway_config import TimeoutConfig

        cfg = TimeoutConfig()
        assert cfg.connect is None
        assert cfg.read is None
        assert cfg.write is None
        assert cfg.pool is None
        assert cfg.total is None

    def test_timeout_config_partial(self) -> None:
        from fi.gateway._gateway_config import TimeoutConfig

        cfg = TimeoutConfig(connect=5.0, read=30.0)
        assert cfg.connect == 5.0
        assert cfg.read == 30.0
        assert cfg.write is None

    def test_timeout_config_total(self) -> None:
        from fi.gateway._gateway_config import TimeoutConfig

        cfg = TimeoutConfig(total=60.0)
        assert cfg.total == 60.0

    def test_timeout_config_in_gateway_config(self) -> None:
        from fi.gateway._gateway_config import GatewayConfig, TimeoutConfig

        cfg = GatewayConfig(timeout=TimeoutConfig(total=120.0, connect=5.0))
        assert cfg.timeout is not None
        assert cfg.timeout.total == 120.0
        assert cfg.timeout.connect == 5.0

    def test_timeout_total_emits_header(self) -> None:
        from fi.gateway._gateway_config import GatewayConfig, TimeoutConfig

        cfg = GatewayConfig(timeout=TimeoutConfig(total=30.0))
        headers = cfg.to_headers()
        assert headers.get("x-agentcc-request-timeout") == "30000"

    def test_timeout_without_total_no_header(self) -> None:
        from fi.gateway._gateway_config import GatewayConfig, TimeoutConfig

        cfg = GatewayConfig(timeout=TimeoutConfig(connect=5.0))
        headers = cfg.to_headers()
        assert "x-agentcc-request-timeout" not in headers
        # But x-agentcc-config should still contain the timeout
        assert "x-agentcc-config" in headers
        config_data = json.loads(headers["x-agentcc-config"])
        assert config_data["timeout"]["connect"] == 5.0

    def test_timeout_config_to_dict(self) -> None:
        from fi.gateway._gateway_config import GatewayConfig, TimeoutConfig

        cfg = GatewayConfig(timeout=TimeoutConfig(connect=5.0, read=30.0, total=60.0))
        d = cfg.to_dict()
        assert "timeout" in d
        assert d["timeout"]["connect"] == 5.0
        assert d["timeout"]["read"] == 30.0
        assert d["timeout"]["total"] == 60.0


# ============================================================================
# GuardrailCheck tests
# ============================================================================


class TestGuardrailCheck:
    def test_guardrail_check_defaults(self) -> None:
        from fi.gateway._gateway_config import GuardrailCheck

        check = GuardrailCheck(name="pii-filter")
        assert check.name == "pii-filter"
        assert check.enabled is True
        assert check.action == "block"
        assert check.confidence_threshold == 0.8
        assert check.config is None

    def test_guardrail_check_custom(self) -> None:
        from fi.gateway._gateway_config import GuardrailCheck

        check = GuardrailCheck(
            name="toxicity",
            action="warn",
            confidence_threshold=0.9,
            config={"categories": ["hate", "violence"]},
        )
        assert check.action == "warn"
        assert check.confidence_threshold == 0.9
        assert check.config == {"categories": ["hate", "violence"]}

    def test_guardrail_config_with_checks(self) -> None:
        from fi.gateway._gateway_config import GuardrailCheck, GuardrailConfig

        cfg = GuardrailConfig(
            checks=[
                GuardrailCheck(name="pii-filter", action="mask"),
                GuardrailCheck(name="toxicity", action="block", confidence_threshold=0.9),
            ],
            pipeline_mode="parallel",
            fail_open=True,
            timeout_ms=5000,
        )
        assert cfg.checks is not None
        assert len(cfg.checks) == 2
        assert cfg.pipeline_mode == "parallel"
        assert cfg.fail_open is True
        assert cfg.timeout_ms == 5000

    def test_guardrail_checks_serialize(self) -> None:
        from fi.gateway._gateway_config import GatewayConfig, GuardrailCheck, GuardrailConfig

        cfg = GatewayConfig(
            guardrails=GuardrailConfig(
                checks=[GuardrailCheck(name="pii", action="mask")],
                pipeline_mode="sequential",
            )
        )
        headers = cfg.to_headers()
        config_data = json.loads(headers["x-agentcc-config"])
        guardrails = config_data["guardrails"]
        assert guardrails["pipeline_mode"] == "sequential"
        assert len(guardrails["checks"]) == 1
        assert guardrails["checks"][0]["name"] == "pii"
        assert guardrails["checks"][0]["action"] == "mask"


# ============================================================================
# create_headers with request_id test
# ============================================================================


class TestCreateHeadersRequestId:
    def test_create_headers_with_request_id(self) -> None:
        from fi.gateway._gateway_config import create_headers

        headers = create_headers(api_key="sk-test", request_id="req-123")
        assert headers["x-agentcc-request-id"] == "req-123"

    def test_create_headers_without_request_id(self) -> None:
        from fi.gateway._gateway_config import create_headers

        headers = create_headers(api_key="sk-test")
        assert "x-agentcc-request-id" not in headers


# ============================================================================
# LoadBalanceTarget with virtual_key test
# ============================================================================


class TestLoadBalanceTargetVirtualKey:
    def test_target_with_virtual_key(self) -> None:
        from fi.gateway._gateway_config import LoadBalanceTarget

        target = LoadBalanceTarget(model="gpt-4o", virtual_key="vk-openai-1")
        assert target.virtual_key == "vk-openai-1"

    def test_target_without_virtual_key(self) -> None:
        from fi.gateway._gateway_config import LoadBalanceTarget

        target = LoadBalanceTarget(model="gpt-4o")
        assert target.virtual_key is None


# ============================================================================
# Full config with all sub-configs (including retry + timeout)
# ============================================================================


class TestGatewayConfigFull:
    def test_full_config_with_retry_and_timeout(self) -> None:
        from fi.gateway._gateway_config import (
            CacheConfig,
            FallbackConfig,
            FallbackTarget,
            GatewayConfig,
            GuardrailConfig,
            LoadBalanceConfig,
            LoadBalanceTarget,
            RetryConfig,
            TimeoutConfig,
            TrafficMirrorConfig,
        )

        cfg = GatewayConfig(
            fallback=FallbackConfig(targets=[FallbackTarget(model="gpt-4o-mini")]),
            load_balance=LoadBalanceConfig(strategy="weighted", targets=[
                LoadBalanceTarget(model="gpt-4o", weight=0.7),
                LoadBalanceTarget(model="gpt-4o-mini", weight=0.3),
            ]),
            cache=CacheConfig(ttl=300, namespace="prod"),
            guardrails=GuardrailConfig(input_guardrails=["pii-filter"]),
            retry=RetryConfig(max_retries=3),
            timeout=TimeoutConfig(total=60.0, connect=5.0),
            mirror=TrafficMirrorConfig(target_model="claude-3-haiku", sample_rate=0.1),
        )
        assert cfg.retry is not None
        assert cfg.timeout is not None

        # Serialize and check all sections present
        headers = cfg.to_headers()
        config_data = json.loads(headers["x-agentcc-config"])
        assert "fallback" in config_data
        assert "load_balance" in config_data
        assert "cache" in config_data
        assert "guardrails" in config_data
        assert "retry" in config_data
        assert "timeout" in config_data
        assert "mirror" in config_data

        # Individual headers
        assert headers["x-agentcc-cache-ttl"] == "300"
        assert headers["x-agentcc-cache-namespace"] == "prod"
        assert headers["x-agentcc-guardrail-policy"] == "pii-filter"
        assert headers["x-agentcc-request-timeout"] == "60000"


# ============================================================================
# AGENTCC_GATEWAY_URL test
# ============================================================================


class TestAgentCCGatewayUrl:
    def test_agentcc_gateway_url_constant(self) -> None:
        from fi.gateway._constants import AGENTCC_GATEWAY_URL

        assert isinstance(AGENTCC_GATEWAY_URL, str)
        assert len(AGENTCC_GATEWAY_URL) > 0
        # When AGENTCC_BASE_URL is not set, should default to https://api.agentcc.ai/v1
        # (It may already be set in the environment, so just check it is a string)


# ============================================================================
# Lazy import tests
# ============================================================================


class TestLazyImports:
    def test_gateway_config_importable(self) -> None:
        from fi.gateway import GatewayConfig

        cfg = GatewayConfig()
        assert cfg.fallback is None

    def test_create_headers_importable(self) -> None:
        from fi.gateway import create_headers

        headers = create_headers(api_key="sk-test")
        assert "Authorization" in headers

    def test_agentcc_gateway_url_importable(self) -> None:
        from fi.gateway import AGENTCC_GATEWAY_URL

        assert isinstance(AGENTCC_GATEWAY_URL, str)

    def test_retry_config_importable(self) -> None:
        from fi.gateway import RetryConfig

        cfg = RetryConfig()
        assert cfg.max_retries == 2

    def test_timeout_config_importable(self) -> None:
        from fi.gateway import TimeoutConfig

        cfg = TimeoutConfig()
        assert cfg.connect is None

    def test_guardrail_check_importable(self) -> None:
        from fi.gateway import GuardrailCheck

        check = GuardrailCheck(name="pii")
        assert check.name == "pii"

    def test_all_config_classes_importable(self) -> None:
        from fi.gateway import (
            CacheConfig,
            ConditionalRoutingConfig,
            FallbackConfig,
            FallbackTarget,
            GatewayConfig,
            GuardrailCheck,
            GuardrailConfig,
            LoadBalanceConfig,
            LoadBalanceTarget,
            RetryConfig,
            RoutingCondition,
            TimeoutConfig,
            TrafficMirrorConfig,
        )

        # Verify they are all constructible
        assert GatewayConfig() is not None
        assert FallbackConfig() is not None
        assert FallbackTarget(model="test") is not None
        assert LoadBalanceConfig() is not None
        assert LoadBalanceTarget(model="test") is not None
        assert CacheConfig() is not None
        assert GuardrailConfig() is not None
        assert GuardrailCheck(name="test") is not None
        assert ConditionalRoutingConfig() is not None
        assert RoutingCondition(field="f", operator="$eq", value="v", target="t") is not None
        assert TrafficMirrorConfig() is not None
        assert RetryConfig() is not None
        assert TimeoutConfig() is not None
