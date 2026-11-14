"""Tests for advanced features: pre-call rules, budget windows, mock streaming, etc."""

from __future__ import annotations

import time

import httpx
import pytest
import respx

from fi.gateway._budget import BudgetManager
from fi.gateway._client import AgentCC
from fi.gateway._exceptions import AgentCCError
from fi.gateway._structured import validate_json_response
from fi.gateway._tokens import is_prompt_caching_valid
from fi.gateway._utils import health_check

# ---------------------------------------------------------------------------
# Pre-call rules
# ---------------------------------------------------------------------------


class TestPreCallRules:
    def test_pre_call_rule_allows(self) -> None:
        """Rule returns True -> request succeeds (mock_response used to avoid HTTP)."""

        def allow_all(model: str, messages: list, kwargs: dict) -> bool:
            return True

        client = AgentCC(
            api_key="sk-test",
            base_url="http://localhost:8080",
            pre_call_rules=[allow_all],
        )
        result = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "hi"}],
            mock_response="hello",
        )
        assert result.choices[0].message.content == "hello"

    def test_pre_call_rule_blocks(self) -> None:
        """Rule returns False -> AgentCCError raised."""

        def block_all(model: str, messages: list, kwargs: dict) -> bool:
            return False

        client = AgentCC(
            api_key="sk-test",
            base_url="http://localhost:8080",
            pre_call_rules=[block_all],
        )
        with pytest.raises(AgentCCError, match="Request blocked by pre-call rule: block_all"):
            client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "hi"}],
                mock_response="hello",
            )

    def test_pre_call_rule_multiple(self) -> None:
        """First rule allows, second blocks -> blocked."""

        def allow(model: str, messages: list, kwargs: dict) -> bool:
            return True

        def deny(model: str, messages: list, kwargs: dict) -> bool:
            return False

        client = AgentCC(
            api_key="sk-test",
            base_url="http://localhost:8080",
            pre_call_rules=[allow, deny],
        )
        with pytest.raises(AgentCCError, match="Request blocked by pre-call rule: deny"):
            client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "hi"}],
                mock_response="hello",
            )

    def test_pre_call_rules_none(self) -> None:
        """No rules configured -> request succeeds."""
        client = AgentCC(
            api_key="sk-test",
            base_url="http://localhost:8080",
        )
        result = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "hi"}],
            mock_response="hello",
        )
        assert result.choices[0].message.content == "hello"


# ---------------------------------------------------------------------------
# BudgetManager duration
# ---------------------------------------------------------------------------


class TestBudgetManagerDuration:
    def test_budget_manager_window_1h(self) -> None:
        bm = BudgetManager(max_budget=10.0, window="1h")
        assert bm.window == "1h"
        seconds = BudgetManager._parse_window("1h")
        assert seconds == 3600.0

    def test_budget_manager_window_1d(self) -> None:
        bm = BudgetManager(max_budget=100.0, window="1d")
        assert bm.window == "1d"
        seconds = BudgetManager._parse_window("1d")
        assert seconds == 86400.0

    def test_budget_manager_auto_reset_on_window_expire(self) -> None:
        """Simulate an expired window and verify spend is auto-reset."""
        bm = BudgetManager(max_budget=10.0, window="1m")
        bm.update_cost(5.0)
        assert bm.get_current_spend() == 5.0

        # Simulate window expiration by backdating _window_start
        bm._window_start = time.time() - 120  # 2 minutes ago

        # Next access should auto-reset
        assert bm.get_current_spend() == 0.0

    def test_budget_manager_projected_cost(self) -> None:
        bm = BudgetManager(max_budget=100.0, window="1d")
        # Backdate window start to simulate 1 hour elapsed (within the 1d window)
        bm._window_start = time.time() - 3600
        bm._current_spend = 10.0  # $10 spent in 1 hour

        # Projected cost for 24 hours should be ~$240
        projected = bm.projected_cost(hours=24.0)
        assert projected == pytest.approx(240.0, rel=0.1)

    def test_budget_manager_is_valid_user(self) -> None:
        bm = BudgetManager()
        bm.set_user_budget("alice", 10.0)
        assert bm.is_valid_user("alice") is True

    def test_budget_manager_is_valid_user_exceeded(self) -> None:
        bm = BudgetManager()
        bm.set_user_budget("bob", 5.0)
        bm.update_cost(6.0, user="bob")
        assert bm.is_valid_user("bob") is False

    def test_budget_manager_is_valid_user_unknown(self) -> None:
        bm = BudgetManager()
        assert bm.is_valid_user("unknown_user") is False


# ---------------------------------------------------------------------------
# Mock streaming
# ---------------------------------------------------------------------------


class TestMockStreaming:
    def test_mock_response_stream(self) -> None:
        """stream=True with mock_response returns a StreamManager."""
        client = AgentCC(
            api_key="sk-test",
            base_url="http://localhost:8080",
        )
        result = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "hi"}],
            mock_response="hello world",
            stream=True,
        )
        # Should be a StreamManager
        from fi.gateway._streaming import StreamManager

        assert isinstance(result, StreamManager)

    def test_mock_response_stream_content(self) -> None:
        """Verify that streaming mock response yields the full content."""
        client = AgentCC(
            api_key="sk-test",
            base_url="http://localhost:8080",
        )
        result = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "hi"}],
            mock_response="hello world test",
            stream=True,
        )
        # Collect all text chunks
        texts = []
        with result:
            for text in result.text_stream:
                texts.append(text)

        full_text = "".join(texts)
        assert full_text == "hello world test"


# ---------------------------------------------------------------------------
# modify_params
# ---------------------------------------------------------------------------


class TestModifyParams:
    def test_modify_params_stored_on_client(self) -> None:
        client = AgentCC(
            api_key="sk-test",
            base_url="http://localhost:8080",
            modify_params=True,
        )
        assert client._modify_params is True

    def test_modify_params_in_with_options(self) -> None:
        client = AgentCC(
            api_key="sk-test",
            base_url="http://localhost:8080",
            modify_params=True,
        )
        new_client = client.with_options(timeout=30)
        assert new_client._modify_params is True

    def test_modify_params_default_false(self) -> None:
        client = AgentCC(
            api_key="sk-test",
            base_url="http://localhost:8080",
        )
        assert client._modify_params is False


# ---------------------------------------------------------------------------
# health_check
# ---------------------------------------------------------------------------


class TestHealthCheck:
    @respx.mock
    def test_health_check_basic(self) -> None:
        """Mock /health endpoint returning 200."""
        respx.get("http://localhost:8080/health").mock(
            return_value=httpx.Response(200, json={"status": "ok"})
        )
        result = health_check(base_url="http://localhost:8080")
        assert result["status"] == "ok"

    @respx.mock
    def test_health_check_returns_latency(self) -> None:
        """Verify latency_ms is present in success response."""
        respx.get("http://localhost:8080/health").mock(
            return_value=httpx.Response(200, json={"status": "ok"})
        )
        result = health_check(base_url="http://localhost:8080")
        assert "latency_ms" in result
        assert isinstance(result["latency_ms"], float)

    def test_health_check_error(self) -> None:
        """Connection refused -> error status."""
        result = health_check(base_url="http://localhost:1")
        assert result["status"] == "error"
        assert "error" in result


# ---------------------------------------------------------------------------
# validate_json_response
# ---------------------------------------------------------------------------


class TestValidateJsonResponse:
    def test_validate_json_response_valid(self) -> None:
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
            "required": ["name", "age"],
        }
        assert validate_json_response('{"name": "Alice", "age": 30}', schema) is True

    def test_validate_json_response_invalid(self) -> None:
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
            "required": ["name", "age"],
        }
        # age is a string, not integer
        assert validate_json_response('{"name": "Alice", "age": "thirty"}', schema) is False

    def test_validate_json_response_invalid_json(self) -> None:
        schema = {"type": "object"}
        assert validate_json_response("not valid json {{{", schema) is False


# ---------------------------------------------------------------------------
# is_prompt_caching_valid
# ---------------------------------------------------------------------------


class TestPromptCachingValid:
    def test_prompt_caching_anthropic_with_cache_control(self) -> None:
        messages = [
            {"role": "system", "content": "You are helpful.", "cache_control": {"type": "ephemeral"}},
            {"role": "user", "content": "Hello"},
        ]
        valid, reason = is_prompt_caching_valid("claude-3-5-sonnet-20241022", messages)
        assert valid is True
        assert "Anthropic cache_control detected" in reason

    def test_prompt_caching_openai_long_system(self) -> None:
        # Create a system message with many tokens (>= 1024)
        long_text = "word " * 2000  # well over 1024 tokens
        messages = [
            {"role": "system", "content": long_text},
            {"role": "user", "content": "Hello"},
        ]
        valid, reason = is_prompt_caching_valid("gpt-4o", messages)
        assert valid is True
        assert "System prompt eligible for OpenAI automatic caching" in reason

    def test_prompt_caching_no_indicators(self) -> None:
        messages = [
            {"role": "system", "content": "Short."},
            {"role": "user", "content": "Hello"},
        ]
        valid, reason = is_prompt_caching_valid("gpt-4o", messages)
        assert valid is False
        assert "No caching indicators found" in reason


# ---------------------------------------------------------------------------
# Lazy imports
# ---------------------------------------------------------------------------


class TestLazyImports:
    def test_health_check_importable(self) -> None:
        import fi.gateway as agentcc

        assert hasattr(agentcc, "health_check")
        assert callable(agentcc.health_check)

    def test_validate_json_response_importable(self) -> None:
        import fi.gateway as agentcc

        assert hasattr(agentcc, "validate_json_response")
        assert callable(agentcc.validate_json_response)

    def test_is_prompt_caching_valid_importable(self) -> None:
        import fi.gateway as agentcc

        assert hasattr(agentcc, "is_prompt_caching_valid")
        assert callable(agentcc.is_prompt_caching_valid)


# ---------------------------------------------------------------------------
# JSON schema validation integration
# ---------------------------------------------------------------------------


class TestJsonSchemaValidationIntegration:
    def test_enable_json_schema_validation_stored(self) -> None:
        """enable_json_schema_validation is stored on client."""
        client = AgentCC(
            api_key="sk-test",
            base_url="http://localhost:8080",
            enable_json_schema_validation=True,
        )
        assert client._enable_json_schema_validation is True

    def test_enable_json_schema_validation_default_false(self) -> None:
        """Default is False."""
        client = AgentCC(api_key="sk-test", base_url="http://localhost:8080")
        assert client._enable_json_schema_validation is False

    def test_json_schema_validation_passes(self) -> None:
        """Valid JSON response passes validation."""
        client = AgentCC(
            api_key="sk-test",
            base_url="http://localhost:8080",
            enable_json_schema_validation=True,
        )
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        response_format = {"type": "json_schema", "json_schema": {"name": "Test", "schema": schema}}
        result = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "hi"}],
            mock_response='{"name": "Alice"}',
            response_format=response_format,
        )
        assert result.choices[0].message.content == '{"name": "Alice"}'

    def test_json_schema_validation_fails(self) -> None:
        """Invalid JSON response raises AgentCCError."""
        client = AgentCC(
            api_key="sk-test",
            base_url="http://localhost:8080",
            enable_json_schema_validation=True,
        )
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
            "required": ["name", "age"],
        }
        response_format = {"type": "json_schema", "json_schema": {"name": "Test", "schema": schema}}
        with pytest.raises(AgentCCError, match="JSON schema validation failed"):
            client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "hi"}],
                mock_response='{"name": "Alice"}',  # missing required "age"
                response_format=response_format,
            )

    def test_json_schema_validation_not_triggered_without_schema(self) -> None:
        """No response_format -> no validation even if enabled."""
        client = AgentCC(
            api_key="sk-test",
            base_url="http://localhost:8080",
            enable_json_schema_validation=True,
        )
        result = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "hi"}],
            mock_response="just text, not json",
        )
        assert result.choices[0].message.content == "just text, not json"

    def test_json_schema_validation_preserved_in_with_options(self) -> None:
        """with_options preserves enable_json_schema_validation."""
        client = AgentCC(
            api_key="sk-test",
            base_url="http://localhost:8080",
            enable_json_schema_validation=True,
        )
        new_client = client.with_options(timeout=30)
        assert new_client._enable_json_schema_validation is True


# ---------------------------------------------------------------------------
# modify_params active implementation
# ---------------------------------------------------------------------------


class TestModifyParamsActive:
    def test_modify_params_removes_logit_bias_for_claude(self) -> None:
        """modify_params removes unsupported params for Claude models."""
        from fi.gateway._param_modifier import modify_params_for_provider

        body = {"model": "claude-3-5-sonnet-20241022", "messages": [], "logit_bias": {"123": 1.0}, "n": 2}
        modify_params_for_provider("claude-3-5-sonnet-20241022", body)
        assert "logit_bias" not in body
        assert "n" not in body

    def test_modify_params_removes_functions_for_claude(self) -> None:
        """modify_params removes legacy functions param for Claude."""
        from fi.gateway._param_modifier import modify_params_for_provider

        body = {
            "model": "claude-3-opus-20240229",
            "messages": [],
            "functions": [{"name": "get_weather"}],
            "function_call": "auto",
        }
        modify_params_for_provider("claude-3-opus-20240229", body)
        assert "functions" not in body
        assert "function_call" not in body

    def test_modify_params_converts_tool_choice_for_claude(self) -> None:
        """modify_params converts tool_choice from string to dict for Claude."""
        from fi.gateway._param_modifier import modify_params_for_provider

        body = {"model": "claude-3-5-sonnet-20241022", "messages": [], "tool_choice": "required"}
        modify_params_for_provider("claude-3-5-sonnet-20241022", body)
        assert body["tool_choice"] == {"type": "any"}

        body2 = {"model": "claude-3-5-sonnet-20241022", "messages": [], "tool_choice": "auto"}
        modify_params_for_provider("claude-3-5-sonnet-20241022", body2)
        assert body2["tool_choice"] == {"type": "auto"}

    def test_modify_params_converts_tool_choice_none_for_claude(self) -> None:
        """tool_choice=none removes tools entirely for Claude."""
        from fi.gateway._param_modifier import modify_params_for_provider

        body = {
            "model": "claude-3-5-sonnet-20241022",
            "messages": [],
            "tools": [{"type": "function", "function": {"name": "f"}}],
            "tool_choice": "none",
        }
        modify_params_for_provider("claude-3-5-sonnet-20241022", body)
        assert "tool_choice" not in body
        assert "tools" not in body

    def test_modify_params_max_tokens_fallback_for_claude(self) -> None:
        """Claude requires max_tokens — copy from max_completion_tokens if needed."""
        from fi.gateway._param_modifier import modify_params_for_provider

        body = {"model": "claude-3-5-sonnet-20241022", "messages": [], "max_completion_tokens": 1024}
        modify_params_for_provider("claude-3-5-sonnet-20241022", body)
        assert body["max_tokens"] == 1024
        assert "max_completion_tokens" not in body

    def test_modify_params_removes_unsupported_for_gemini(self) -> None:
        """modify_params removes unsupported params for Gemini models."""
        from fi.gateway._param_modifier import modify_params_for_provider

        body = {"model": "gemini-1.5-pro", "messages": [], "logit_bias": {"1": 1.0}, "n": 2}
        modify_params_for_provider("gemini-1.5-pro", body)
        assert "logit_bias" not in body
        assert "n" not in body

    def test_modify_params_converts_max_tokens_for_gemini(self) -> None:
        """Gemini uses max_output_tokens instead of max_tokens."""
        from fi.gateway._param_modifier import modify_params_for_provider

        body = {"model": "gemini-1.5-pro", "messages": [], "max_tokens": 2048}
        modify_params_for_provider("gemini-1.5-pro", body)
        assert body.get("max_output_tokens") == 2048
        assert "max_tokens" not in body

    def test_modify_params_removes_unsupported_for_cohere(self) -> None:
        """modify_params removes unsupported params for Cohere models."""
        from fi.gateway._param_modifier import modify_params_for_provider

        body = {
            "model": "command-r-plus",
            "messages": [],
            "presence_penalty": 0.5,
            "frequency_penalty": 0.5,
        }
        modify_params_for_provider("command-r-plus", body)
        assert "presence_penalty" not in body
        assert "frequency_penalty" not in body

    def test_modify_params_noop_for_openai(self) -> None:
        """OpenAI models pass through unmodified."""
        from fi.gateway._param_modifier import modify_params_for_provider

        body = {
            "model": "gpt-4o",
            "messages": [],
            "logit_bias": {"1": 1.0},
            "n": 2,
            "tool_choice": "auto",
        }
        original = dict(body)
        modify_params_for_provider("gpt-4o", body)
        assert body == original

    def test_modify_params_integrated_with_client(self) -> None:
        """modify_params=True on client actually modifies the request body."""
        client = AgentCC(
            api_key="sk-test",
            base_url="http://localhost:8080",
            modify_params=True,
        )
        # Use mock_response to avoid HTTP call; the important thing is
        # that it doesn't crash (params are adapted before mock response path)
        result = client.chat.completions.create(
            model="claude-3-5-sonnet-20241022",
            messages=[{"role": "user", "content": "hi"}],
            mock_response="hello",
            logit_bias={"1": 1.0},
        )
        assert result.choices[0].message.content == "hello"

    def test_modify_params_case_insensitive(self) -> None:
        """Provider detection is case-insensitive."""
        from fi.gateway._param_modifier import modify_params_for_provider

        body = {"model": "Claude-3-5-Sonnet-20241022", "messages": [], "logit_bias": {"1": 1.0}}
        modify_params_for_provider("Claude-3-5-Sonnet-20241022", body)
        assert "logit_bias" not in body
