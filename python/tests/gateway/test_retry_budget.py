"""Tests for RetryPolicy, BudgetManager, context/content fallbacks, and lazy imports."""

from __future__ import annotations

from typing import Any

import httpx
import pytest
import respx
from pydantic import BaseModel, ConfigDict

from fi.gateway._base_client import RequestOptions, RetryConfig, SyncBaseClient
from fi.gateway._budget import BudgetManager
from fi.gateway._exceptions import AgentCCError
from fi.gateway._retry_policy import RetryPolicy
from fi.gateway._tokens import (
    CONTENT_POLICY_FALLBACKS,
    CONTEXT_WINDOW_FALLBACKS,
    get_content_policy_fallback,
    get_context_window_fallback,
)

# --- Test helpers ---


class _MockResponse(BaseModel):
    """Simple Pydantic model for testing."""

    model_config = ConfigDict(extra="allow")
    id: str
    content: str


def _make_sync_client(**kwargs: Any) -> SyncBaseClient:
    defaults: dict[str, Any] = {"api_key": "sk-test-key-12345"}
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
            httpx.Response(200, json={"id": "abc", "content": "hello"}, headers={
                "x-agentcc-request-id": "req-1",
                "x-agentcc-trace-id": "trace-1",
                "x-agentcc-provider": "openai",
                "x-agentcc-latency-ms": "50",
            }),
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


class TestBudgetManager:
    def test_check_budget_passes_under_limit(self) -> None:
        budget = BudgetManager(max_budget=10.0)
        budget.check_budget(5.0)  # should not raise

    def test_check_budget_raises_on_exceed(self) -> None:
        budget = BudgetManager(max_budget=1.0)
        budget.update_cost(0.8)
        with pytest.raises(AgentCCError, match="Budget exceeded"):
            budget.check_budget(0.3)

    def test_check_budget_exact_boundary(self) -> None:
        budget = BudgetManager(max_budget=1.0)
        budget.update_cost(0.5)
        budget.check_budget(0.5)  # exactly at limit, should not raise

    def test_update_cost_accumulates(self) -> None:
        budget = BudgetManager(max_budget=10.0)
        budget.update_cost(1.0)
        budget.update_cost(2.0)
        assert budget.get_current_spend() == 3.0

    def test_user_budget_set_and_check(self) -> None:
        budget = BudgetManager()
        budget.set_user_budget("alice", 5.0)
        budget.update_cost(3.0, user="alice")
        budget.check_budget(1.0, user="alice")  # should not raise

    def test_user_budget_exceeded(self) -> None:
        budget = BudgetManager()
        budget.set_user_budget("bob", 2.0)
        budget.update_cost(1.5, user="bob")
        with pytest.raises(AgentCCError, match="User budget exceeded for 'bob'"):
            budget.check_budget(1.0, user="bob")

    def test_get_current_spend_global(self) -> None:
        budget = BudgetManager()
        budget.update_cost(1.5)
        assert budget.get_current_spend() == 1.5

    def test_get_current_spend_user(self) -> None:
        budget = BudgetManager()
        budget.update_cost(1.0, user="alice")
        budget.update_cost(2.0, user="bob")
        assert budget.get_current_spend(user="alice") == 1.0
        assert budget.get_current_spend(user="bob") == 2.0

    def test_get_current_spend_unknown_user(self) -> None:
        budget = BudgetManager()
        assert budget.get_current_spend(user="unknown") == 0.0

    def test_get_remaining_budget_global(self) -> None:
        budget = BudgetManager(max_budget=10.0)
        budget.update_cost(3.0)
        assert budget.get_remaining_budget() == 7.0

    def test_get_remaining_budget_user(self) -> None:
        budget = BudgetManager()
        budget.set_user_budget("alice", 5.0)
        budget.update_cost(2.0, user="alice")
        assert budget.get_remaining_budget(user="alice") == 3.0

    def test_get_remaining_budget_no_budget_set(self) -> None:
        budget = BudgetManager()
        assert budget.get_remaining_budget() is None

    def test_reset_global(self) -> None:
        budget = BudgetManager(max_budget=10.0)
        budget.update_cost(5.0)
        budget.update_cost(2.0, user="alice")
        budget.reset()
        assert budget.get_current_spend() == 0.0
        assert budget.get_current_spend(user="alice") == 0.0

    def test_reset_user(self) -> None:
        budget = BudgetManager(max_budget=10.0)
        budget.update_cost(3.0)
        budget.update_cost(2.0, user="alice")
        budget.update_cost(1.0, user="bob")
        budget.reset(user="alice")
        assert budget.get_current_spend(user="alice") == 0.0
        assert budget.get_current_spend(user="bob") == 1.0
        # Global spend is not affected by user reset (3.0 + 2.0 + 1.0 = 6.0)
        assert budget.get_current_spend() == 6.0

    def test_no_global_budget_user_budget_only(self) -> None:
        """When max_budget is None, only user budgets are enforced."""
        budget = BudgetManager()
        budget.set_user_budget("alice", 1.0)
        budget.update_cost(100.0)  # global has no limit
        budget.check_budget(1000.0)  # should not raise (no global budget)
        budget.update_cost(0.5, user="alice")
        with pytest.raises(AgentCCError, match="User budget exceeded"):
            budget.check_budget(0.6, user="alice")


# =====================================================================
# Context window fallback tests
# =====================================================================


class TestContextWindowFallbacks:
    def test_known_fallback_gpt4(self) -> None:
        assert get_context_window_fallback("gpt-4") == "gpt-4-turbo"

    def test_known_fallback_gpt4_turbo(self) -> None:
        assert get_context_window_fallback("gpt-4-turbo") == "gpt-4o"

    def test_known_fallback_gpt35_turbo(self) -> None:
        assert get_context_window_fallback("gpt-3.5-turbo") == "gpt-4o-mini"

    def test_known_fallback_claude_haiku(self) -> None:
        assert get_context_window_fallback("claude-3-haiku-20240307") == "claude-3-5-haiku-20241022"

    def test_known_fallback_claude_opus(self) -> None:
        assert get_context_window_fallback("claude-3-opus-20240229") == "claude-sonnet-4-20250514"

    def test_unknown_model_returns_none(self) -> None:
        assert get_context_window_fallback("totally-unknown-model") is None

    def test_fallback_map_is_dict(self) -> None:
        assert isinstance(CONTEXT_WINDOW_FALLBACKS, dict)
        assert len(CONTEXT_WINDOW_FALLBACKS) > 0


# =====================================================================
# Content policy fallback tests
# =====================================================================


class TestContentPolicyFallbacks:
    def test_known_fallback_gpt4o(self) -> None:
        assert get_content_policy_fallback("gpt-4o") == "gpt-4-turbo"

    def test_known_fallback_gpt4o_mini(self) -> None:
        assert get_content_policy_fallback("gpt-4o-mini") == "gpt-3.5-turbo"

    def test_unknown_model_returns_none(self) -> None:
        assert get_content_policy_fallback("unknown-model") is None

    def test_fallback_map_is_dict(self) -> None:
        assert isinstance(CONTENT_POLICY_FALLBACKS, dict)
        assert len(CONTENT_POLICY_FALLBACKS) > 0


# =====================================================================
# Lazy import tests
# =====================================================================


class TestLazyImports:
    def test_import_retry_policy(self) -> None:
        import fi.gateway as agentcc

        assert hasattr(agentcc, "RetryPolicy")
        rp = agentcc.RetryPolicy()
        assert rp.RateLimitErrorRetries == 2

    def test_import_budget_manager(self) -> None:
        import fi.gateway as agentcc

        assert hasattr(agentcc, "BudgetManager")
        bm = agentcc.BudgetManager(max_budget=10.0)
        assert bm.max_budget == 10.0

    def test_import_context_window_fallback(self) -> None:
        import fi.gateway as agentcc

        assert hasattr(agentcc, "get_context_window_fallback")
        assert hasattr(agentcc, "CONTEXT_WINDOW_FALLBACKS")
        assert agentcc.get_context_window_fallback("gpt-4") == "gpt-4-turbo"

    def test_import_content_policy_fallback(self) -> None:
        import fi.gateway as agentcc

        assert hasattr(agentcc, "get_content_policy_fallback")
        assert hasattr(agentcc, "CONTENT_POLICY_FALLBACKS")
        assert agentcc.get_content_policy_fallback("gpt-4o") == "gpt-4-turbo"

    def test_all_new_exports_in___all__(self) -> None:
        import fi.gateway as agentcc

        for name in [
            "RetryPolicy",
            "BudgetManager",
            "get_context_window_fallback",
            "get_content_policy_fallback",
            "CONTEXT_WINDOW_FALLBACKS",
            "CONTENT_POLICY_FALLBACKS",
        ]:
            assert name in agentcc.__all__, f"{name} not in agentcc.__all__"
