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
        # D-21: only the sections the gateway applies (1.0 also had fallback,
        # load_balance, guardrails, routing, mirror and retry)
        assert cfg.cache is None
        assert cfg.timeout is None

    def test_gateway_config_with_cache(self) -> None:
        from fi.gateway._gateway_config import CacheConfig, GatewayConfig

        cfg = GatewayConfig(cache=CacheConfig(ttl=300, namespace="prod"))
        assert cfg.cache is not None
        assert cfg.cache.ttl == 300
        assert cfg.cache.namespace == "prod"
        assert cfg.cache.force_refresh is False  # D-21: 1.0 asserted enabled is True


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

        cfg = GatewayConfig(
            cache=CacheConfig(ttl=300, namespace="prod", force_refresh=True)
        )
        headers = cfg.to_headers()
        assert "x-agentcc-config" in headers
        assert headers["x-agentcc-cache-ttl"] == "300"
        assert headers["x-agentcc-cache-namespace"] == "prod"
        assert headers["x-agentcc-cache-force-refresh"] == "true"

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

        cfg = GatewayConfig(cache=CacheConfig())  # D-21: 1.0 passed enabled=True
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
        from fi.gateway._gateway_config import (
            CacheConfig,
            GatewayConfig,
            create_headers,
        )

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
        from fi.gateway._gateway_config import (
            CacheConfig,
            GatewayConfig,
            create_headers,
        )

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


# ============================================================================
# LoadBalanceConfig tests
# ============================================================================


# ============================================================================
# CacheConfig tests
# ============================================================================


# ============================================================================
# GuardrailConfig tests
# ============================================================================


# ============================================================================
# RoutingCondition tests
# ============================================================================


# ============================================================================
# RetryConfig tests
# ============================================================================


# ============================================================================
# TimeoutConfig tests
# ============================================================================


class TestTimeoutConfig:
    def test_timeout_config_empty(self) -> None:
        from fi.gateway._gateway_config import TimeoutConfig

        cfg = TimeoutConfig()
        # D-21: only total, the field the gateway applies (1.0 also had connect,
        # read, write and pool, sent in x-agentcc-config and ignored)
        assert cfg.total is None

    def test_timeout_config_total(self) -> None:
        from fi.gateway._gateway_config import TimeoutConfig

        cfg = TimeoutConfig(total=60.0)
        assert cfg.total == 60.0

    def test_timeout_total_emits_header(self) -> None:
        from fi.gateway._gateway_config import GatewayConfig, TimeoutConfig

        cfg = GatewayConfig(timeout=TimeoutConfig(total=30.0))
        headers = cfg.to_headers()
        assert headers.get("x-agentcc-request-timeout") == "30000"


# ============================================================================
# GuardrailCheck tests
# ============================================================================


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


# ============================================================================
# Full config with all sub-configs (including retry + timeout)
# ============================================================================


# ============================================================================
# Lazy import tests
# ============================================================================


class TestLazyImports:
    def test_gateway_config_importable(self) -> None:
        from fi.gateway import GatewayConfig

        cfg = GatewayConfig()
        assert cfg.cache is None  # D-21: 1.0 asserted cfg.fallback is None

    def test_create_headers_importable(self) -> None:
        from fi.gateway import create_headers

        headers = create_headers(api_key="sk-test")
        assert "Authorization" in headers

    def test_timeout_config_importable(self) -> None:
        from fi.gateway import TimeoutConfig

        cfg = TimeoutConfig()
        assert cfg.total is None  # D-21: 1.0 asserted cfg.connect is None
