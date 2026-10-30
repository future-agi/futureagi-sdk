"""Tests for Step 10 — Gateway configuration models."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from fi.gateway.config import (
    CacheConfig,
    ConditionalRoute,
    FallbackStrategy,
    GatewayConfig,
    GuardrailConfig,
    GuardrailRule,
    LoadBalanceStrategy,
    RetryConfig,
    RouteCondition,
    Target,
)


class TestTarget:
    def test_basic_target(self) -> None:
        t = Target(provider="openai")
        assert t.provider == "openai"
        assert t.model is None
        assert t.weight is None

    def test_target_with_all_fields(self) -> None:
        t = Target(provider="openai", model="gpt-4o", weight=0.5, virtual_key="vk-123")
        assert t.model == "gpt-4o"
        assert t.weight == 0.5
        assert t.virtual_key == "vk-123"


class TestLoadBalanceStrategy:
    def test_round_robin(self) -> None:
        strategy = LoadBalanceStrategy(
            mode="round-robin",
            targets=[Target(provider="openai"), Target(provider="anthropic")],
        )
        assert strategy.mode == "round-robin"
        assert len(strategy.targets) == 2

    def test_weighted_valid(self) -> None:
        strategy = LoadBalanceStrategy(
            mode="weighted",
            targets=[
                Target(provider="openai", weight=0.7),
                Target(provider="anthropic", weight=0.3),
            ],
        )
        assert strategy.mode == "weighted"

    def test_weighted_weights_sum_to_one_tolerance(self) -> None:
        """Weights within ±0.01 of 1.0 should be accepted."""
        strategy = LoadBalanceStrategy(
            mode="weighted",
            targets=[
                Target(provider="openai", weight=0.333),
                Target(provider="anthropic", weight=0.333),
                Target(provider="google", weight=0.335),
            ],
        )
        assert strategy.mode == "weighted"

    def test_weighted_wrong_sum_raises(self) -> None:
        with pytest.raises(ValueError, match=r"Weights must sum to 1\.0"):
            LoadBalanceStrategy(
                mode="weighted",
                targets=[
                    Target(provider="openai", weight=0.5),
                    Target(provider="anthropic", weight=0.3),
                ],
            )

    def test_weighted_missing_weight_raises(self) -> None:
        with pytest.raises(ValueError, match="weight"):
            LoadBalanceStrategy(
                mode="weighted",
                targets=[
                    Target(provider="openai", weight=0.7),
                    Target(provider="anthropic"),  # missing weight
                ],
            )

    def test_least_latency(self) -> None:
        strategy = LoadBalanceStrategy(
            mode="least-latency",
            targets=[Target(provider="openai")],
        )
        assert strategy.mode == "least-latency"


class TestFallbackStrategy:
    def test_basic_fallback(self) -> None:
        fb = FallbackStrategy(targets=[Target(provider="openai")])
        assert len(fb.targets) == 1
        assert fb.on_status_codes == [429, 500, 502, 503, 504]

    def test_custom_status_codes(self) -> None:
        fb = FallbackStrategy(
            targets=[Target(provider="openai")],
            on_status_codes=[500, 503],
        )
        assert fb.on_status_codes == [500, 503]

    def test_empty_targets_raises(self) -> None:
        with pytest.raises(ValidationError):
            FallbackStrategy(targets=[])


class TestRetryConfig:
    def test_defaults(self) -> None:
        rc = RetryConfig()
        assert rc.max_retries == 2
        assert rc.retry_on_status == [429, 500, 502, 503]
        assert rc.backoff_factor == 0.5
        assert rc.backoff_max == 30.0
        assert rc.backoff_jitter == 0.25
        assert rc.respect_retry_after is True

    def test_max_retries_constrained_low(self) -> None:
        with pytest.raises(ValidationError):
            RetryConfig(max_retries=-1)

    def test_max_retries_constrained_high(self) -> None:
        with pytest.raises(ValidationError):
            RetryConfig(max_retries=11)

    def test_max_retries_at_boundary(self) -> None:
        rc = RetryConfig(max_retries=0)
        assert rc.max_retries == 0
        rc2 = RetryConfig(max_retries=10)
        assert rc2.max_retries == 10


class TestCacheConfig:
    def test_defaults(self) -> None:
        cc = CacheConfig()
        assert cc.enabled is True
        assert cc.mode == "exact"
        assert cc.ttl == "1h"
        assert cc.namespace == "default"
        assert cc.semantic_threshold == 0.92
        assert cc.force_refresh is False

    def test_semantic_threshold_constrained_low(self) -> None:
        with pytest.raises(ValidationError):
            CacheConfig(semantic_threshold=-0.1)

    def test_semantic_threshold_constrained_high(self) -> None:
        with pytest.raises(ValidationError):
            CacheConfig(semantic_threshold=1.1)

    def test_semantic_threshold_at_boundary(self) -> None:
        cc = CacheConfig(semantic_threshold=0.0)
        assert cc.semantic_threshold == 0.0
        cc2 = CacheConfig(semantic_threshold=1.0)
        assert cc2.semantic_threshold == 1.0


class TestGuardrailConfig:
    def test_defaults(self) -> None:
        gc = GuardrailConfig()
        assert gc.pre == []
        assert gc.post == []

    def test_with_rules(self) -> None:
        gc = GuardrailConfig(
            pre=[GuardrailRule(name="pii-filter", action="mask")],
            post=[GuardrailRule(name="toxicity", action="block", threshold=0.9)],
        )
        assert len(gc.pre) == 1
        assert gc.pre[0].action == "mask"
        assert gc.post[0].threshold == 0.9

    def test_guardrail_rule_threshold_constrained(self) -> None:
        with pytest.raises(ValidationError):
            GuardrailRule(name="test", threshold=1.5)
        with pytest.raises(ValidationError):
            GuardrailRule(name="test", threshold=-0.1)


class TestGatewayConfigToHeaders:
    def test_empty_config_no_headers(self) -> None:
        cfg = GatewayConfig()
        assert cfg.to_headers() == {}

    def test_cache_emits_individual_headers(self) -> None:
        cfg = GatewayConfig(cache=CacheConfig(ttl="30m", namespace="prod", force_refresh=True))
        headers = cfg.to_headers()
        assert headers["x-agentcc-cache-ttl"] == "30m"
        assert headers["x-agentcc-cache-namespace"] == "prod"
        assert headers["x-agentcc-cache-force-refresh"] == "true"

    def test_cache_defaults_skip_individual_headers(self) -> None:
        cfg = GatewayConfig(cache=CacheConfig())
        headers = cfg.to_headers()
        # Default ttl and namespace should not emit individual headers
        assert "x-agentcc-cache-ttl" not in headers
        assert "x-agentcc-cache-namespace" not in headers
        assert "x-agentcc-cache-force-refresh" not in headers
        # But the full cache object is in x-agentcc-config JSON
        assert "x-agentcc-config" in headers

    def test_routing_emits_x_agentcc_config_json(self) -> None:
        cfg = GatewayConfig(
            routing=LoadBalanceStrategy(
                mode="round-robin",
                targets=[Target(provider="openai"), Target(provider="anthropic")],
            )
        )
        headers = cfg.to_headers()
        assert "x-agentcc-config" in headers
        parsed = json.loads(headers["x-agentcc-config"])
        assert parsed["routing"]["mode"] == "round-robin"
        assert len(parsed["routing"]["targets"]) == 2

    def test_cache_disabled_emits_header(self) -> None:
        cfg = GatewayConfig(cache=CacheConfig(enabled=False))
        headers = cfg.to_headers()
        assert headers["x-agentcc-cache-enabled"] == "false"

    def test_full_config_emits_all(self) -> None:
        cfg = GatewayConfig(
            routing=LoadBalanceStrategy(
                mode="round-robin",
                targets=[Target(provider="openai")],
            ),
            fallback=FallbackStrategy(targets=[Target(provider="anthropic")]),
            retry=RetryConfig(max_retries=3),
            cache=CacheConfig(ttl="5m"),
            guardrails=GuardrailConfig(pre=[GuardrailRule(name="pii")]),
        )
        headers = cfg.to_headers()
        parsed = json.loads(headers["x-agentcc-config"])
        assert "routing" in parsed
        assert "fallback" in parsed
        assert "retry" in parsed
        assert "cache" in parsed
        assert "guardrails" in parsed


class TestGatewayConfigToJson:
    def test_round_trip(self) -> None:
        cfg = GatewayConfig(
            routing=LoadBalanceStrategy(
                mode="round-robin",
                targets=[Target(provider="openai")],
            ),
            retry=RetryConfig(max_retries=5),
        )
        json_str = cfg.to_json()
        parsed = json.loads(json_str)
        assert parsed["routing"]["mode"] == "round-robin"
        assert parsed["retry"]["max_retries"] == 5
        # None fields excluded
        assert "fallback" not in parsed
        assert "cache" not in parsed
        assert "guardrails" not in parsed

    def test_empty_config_round_trip(self) -> None:
        cfg = GatewayConfig()
        json_str = cfg.to_json()
        parsed = json.loads(json_str)
        assert parsed == {}

    def test_full_config_round_trip(self) -> None:
        cfg = GatewayConfig(
            routing=LoadBalanceStrategy(
                mode="weighted",
                targets=[
                    Target(provider="openai", weight=0.6),
                    Target(provider="anthropic", weight=0.4),
                ],
            ),
            cache=CacheConfig(mode="semantic", semantic_threshold=0.85),
            conditional_routes=[
                ConditionalRoute(
                    condition=RouteCondition(field="model", operator="$eq", value="gpt-4o"),
                    target=Target(provider="openai"),
                )
            ],
        )
        json_str = cfg.to_json()
        roundtripped = GatewayConfig.model_validate_json(json_str)
        assert roundtripped.routing is not None
        assert roundtripped.routing.mode == "weighted"
        assert roundtripped.cache is not None
        assert roundtripped.cache.semantic_threshold == 0.85
        assert roundtripped.conditional_routes is not None
        assert len(roundtripped.conditional_routes) == 1
