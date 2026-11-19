"""Tests for RetryPolicy and its lazy import (ported from agentcc 1.0)."""

from __future__ import annotations

from typing import Any

import httpx
import pytest
import respx
from pydantic import BaseModel, ConfigDict

from fi.gateway._base_client import RequestOptions, RetryConfig, SyncBaseClient
from fi.gateway._retry_policy import RetryPolicy

# --- Test helpers ---


class _MockResponse(BaseModel):
    """Simple Pydantic model for testing."""

    model_config = ConfigDict(extra="allow")
    id: str
    content: str


def _make_sync_client(**kwargs: Any) -> SyncBaseClient:
    # The transport has no default base URL (no hosted fallback).
    defaults: dict[str, Any] = {
        "api_key": "sk-test-key-12345",
        "base_url": "http://gateway.test",
    }
    defaults.update(kwargs)
    return SyncBaseClient(**defaults)


# =====================================================================
# RetryPolicy tests
# =====================================================================


class TestRetryPolicy:
    def test_default_values(self) -> None:
        policy = RetryPolicy()
        assert policy.RateLimitErrorRetries == 2
        assert policy.TimeoutRetries == 2
        assert policy.ConnectionErrorRetries == 2
        assert policy.InternalServerErrorRetries == 1
        assert policy.BadGatewayRetries == 1
        assert policy.ServiceUnavailableRetries == 1
        assert policy.GatewayTimeoutRetries == 1

    def test_custom_values(self) -> None:
        policy = RetryPolicy(RateLimitErrorRetries=5, TimeoutRetries=3)
        assert policy.RateLimitErrorRetries == 5
        assert policy.TimeoutRetries == 3
        # Others remain default
        assert policy.ConnectionErrorRetries == 2

    def test_get_retries_for_status_429(self) -> None:
        policy = RetryPolicy(RateLimitErrorRetries=5)
        assert policy.get_retries_for_status(429) == 5

    def test_get_retries_for_status_500(self) -> None:
        policy = RetryPolicy(InternalServerErrorRetries=3)
        assert policy.get_retries_for_status(500) == 3

    def test_get_retries_for_status_502(self) -> None:
        policy = RetryPolicy(BadGatewayRetries=4)
        assert policy.get_retries_for_status(502) == 4

    def test_get_retries_for_status_503(self) -> None:
        policy = RetryPolicy(ServiceUnavailableRetries=2)
        assert policy.get_retries_for_status(503) == 2

    def test_get_retries_for_status_504(self) -> None:
        policy = RetryPolicy(GatewayTimeoutRetries=3)
        assert policy.get_retries_for_status(504) == 3

    def test_get_retries_for_unknown_status(self) -> None:
        policy = RetryPolicy()
        assert policy.get_retries_for_status(400) == 0
        assert policy.get_retries_for_status(401) == 0
        assert policy.get_retries_for_status(404) == 0

    def test_get_retries_for_connection_error(self) -> None:
        policy = RetryPolicy(ConnectionErrorRetries=7)
        assert policy.get_retries_for_connection_error() == 7

    def test_get_retries_for_timeout(self) -> None:
        policy = RetryPolicy(TimeoutRetries=4)
        assert policy.get_retries_for_timeout() == 4


# =====================================================================
# RetryPolicy wired into base client
# =====================================================================


class TestRetryPolicyIntegration:
    @respx.mock
    def test_retry_policy_allows_more_retries_for_429(self) -> None:
        """With RateLimitErrorRetries=3, we should get 3 retries (4 total attempts)."""
        policy = RetryPolicy(RateLimitErrorRetries=3)
        client = _make_sync_client(
            base_url="https://gateway.test",
            max_retries=1,  # flat max_retries is low, but policy overrides for 429
            retry_policy=policy,
            retry_config=RetryConfig(backoff_factor=0.001, backoff_jitter=0.0),
        )
        route = respx.post("https://gateway.test/v1/test")
        route.side_effect = [
            httpx.Response(429, json={"error": {"message": "Rate limited"}}),
            httpx.Response(429, json={"error": {"message": "Rate limited"}}),
            httpx.Response(429, json={"error": {"message": "Rate limited"}}),
            httpx.Response(
                200,
                json={"id": "abc", "content": "hello"},
                headers={
                    "x-agentcc-request-id": "req-1",
                    "x-agentcc-trace-id": "trace-1",
                    "x-agentcc-provider": "openai",
                    "x-agentcc-latency-ms": "50",
                },
            ),
        ]
        opts = RequestOptions(method="POST", url="/v1/test", body={})
        result = client._request_with_retry(opts, _MockResponse)
        assert result.id == "abc"
        assert route.call_count == 4  # 1 initial + 3 retries

    @respx.mock
    def test_retry_policy_limits_500_retries(self) -> None:
        """With InternalServerErrorRetries=1, we should get exactly 1 retry for 500."""
        from fi.gateway._exceptions import InternalServerError

        policy = RetryPolicy(InternalServerErrorRetries=1)
        client = _make_sync_client(
            base_url="https://gateway.test",
            max_retries=5,  # high flat max, but policy limits 500 to 1
            retry_policy=policy,
            retry_config=RetryConfig(backoff_factor=0.001, backoff_jitter=0.0),
        )
        route = respx.post("https://gateway.test/v1/test")
        route.respond(500, json={"error": {"message": "Internal error"}})
        opts = RequestOptions(method="POST", url="/v1/test", body={})
        with pytest.raises(InternalServerError):
            client._request_with_retry(opts, _MockResponse)
        assert route.call_count == 2  # 1 initial + 1 retry

    @respx.mock
    def test_retry_policy_zero_for_non_retryable(self) -> None:
        """RetryPolicy returns 0 for 400, so no retries should happen."""
        from fi.gateway._exceptions import BadRequestError

        policy = RetryPolicy()
        client = _make_sync_client(
            base_url="https://gateway.test",
            max_retries=3,
            retry_policy=policy,
            retry_config=RetryConfig(backoff_factor=0.001, backoff_jitter=0.0),
        )
        route = respx.post("https://gateway.test/v1/test")
        route.respond(400, json={"error": {"message": "Bad request"}})
        opts = RequestOptions(method="POST", url="/v1/test", body={})
        with pytest.raises(BadRequestError):
            client._request_with_retry(opts, _MockResponse)
        assert route.call_count == 1

    @respx.mock
    def test_no_retry_policy_uses_flat_max_retries(self) -> None:
        """Without retry_policy, the old flat max_retries behavior applies."""
        from fi.gateway._exceptions import RateLimitError

        client = _make_sync_client(
            base_url="https://gateway.test",
            max_retries=1,
            retry_config=RetryConfig(backoff_factor=0.001, backoff_jitter=0.0),
        )
        route = respx.post("https://gateway.test/v1/test")
        route.respond(429, json={"error": {"message": "Rate limited"}})
        opts = RequestOptions(method="POST", url="/v1/test", body={})
        with pytest.raises(RateLimitError):
            client._request_with_retry(opts, _MockResponse)
        assert route.call_count == 2  # 1 initial + 1 retry (max_retries=1)


# =====================================================================
# BudgetManager tests
# =====================================================================


# =====================================================================
# Context window fallback tests
# =====================================================================


# =====================================================================
# Content policy fallback tests
# =====================================================================


# =====================================================================
# Lazy import tests
# =====================================================================


class TestLazyImports:
    def test_import_retry_policy(self) -> None:
        import fi.gateway as agentcc

        assert hasattr(agentcc, "RetryPolicy")
        rp = agentcc.RetryPolicy()
        assert rp.RateLimitErrorRetries == 2
