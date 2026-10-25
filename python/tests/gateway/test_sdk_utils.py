"""Tests for SDK utility features -- supports_*, to_response_format, thinking/reasoning params,
return_raw_request, check_valid_key, privacy toggle, and lazy imports."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# supports_*() convenience functions
# ---------------------------------------------------------------------------


class TestSupportsVision:
    def test_gpt4o_supports_vision(self) -> None:
        from fi.gateway._models_info import supports_vision

        assert supports_vision("gpt-4o") is True

    def test_gpt35_no_vision(self) -> None:
        from fi.gateway._models_info import supports_vision

        assert supports_vision("gpt-3.5-turbo") is False

    def test_unknown_model(self) -> None:
        from fi.gateway._models_info import supports_vision

        assert supports_vision("unknown-model-xyz") is False


class TestSupportsFunctionCalling:
    def test_gpt4o_supports(self) -> None:
        from fi.gateway._models_info import supports_function_calling

        assert supports_function_calling("gpt-4o") is True

    def test_llama_8b_no_function_calling(self) -> None:
        from fi.gateway._models_info import supports_function_calling

        assert supports_function_calling("llama-3.1-8b") is False

    def test_unknown_model(self) -> None:
        from fi.gateway._models_info import supports_function_calling

        assert supports_function_calling("unknown-model") is False


class TestSupportsJsonMode:
    def test_gpt4o_supports(self) -> None:
        from fi.gateway._models_info import supports_json_mode

        assert supports_json_mode("gpt-4o") is True

    def test_gpt4_no_json_mode(self) -> None:
        from fi.gateway._models_info import supports_json_mode

        assert supports_json_mode("gpt-4") is False

    def test_unknown_model(self) -> None:
        from fi.gateway._models_info import supports_json_mode

        assert supports_json_mode("unknown-model") is False


class TestSupportsResponseSchema:
    def test_is_alias_for_json_mode(self) -> None:
        from fi.gateway._models_info import supports_json_mode, supports_response_schema

        assert supports_response_schema("gpt-4o") == supports_json_mode("gpt-4o")
        assert supports_response_schema("gpt-4") == supports_json_mode("gpt-4")
        assert supports_response_schema("unknown") == supports_json_mode("unknown")

    def test_gpt4o_supports(self) -> None:
        from fi.gateway._models_info import supports_response_schema

        assert supports_response_schema("gpt-4o") is True


# ---------------------------------------------------------------------------
# to_response_format
# ---------------------------------------------------------------------------


class TestToResponseFormat:
    def test_pydantic_model(self) -> None:
        from pydantic import BaseModel

        from fi.gateway._structured import to_response_format

        class Event(BaseModel):
            name: str
            date: str
            attendees: int

        result = to_response_format(Event)

        assert result["type"] == "json_schema"
        assert result["json_schema"]["name"] == "Event"
        assert result["json_schema"]["strict"] is True
        schema = result["json_schema"]["schema"]
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "date" in schema["properties"]
        assert "attendees" in schema["properties"]

    def test_non_pydantic_raises_type_error(self) -> None:
        from fi.gateway._structured import to_response_format

        with pytest.raises(TypeError, match="Expected a Pydantic model class"):
            to_response_format(dict)  # type: ignore[arg-type]

    def test_non_class_raises_type_error(self) -> None:
        from fi.gateway._structured import to_response_format

        with pytest.raises(TypeError, match="Expected a Pydantic model class"):
            to_response_format("not a class")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# thinking / reasoning_effort / drop_params in body
# ---------------------------------------------------------------------------


class TestThinkingReasoningParams:
    def test_thinking_in_body(self) -> None:
        from fi.gateway.resources.chat.completions import _build_body_and_agentcc_params

        thinking_config = {"type": "enabled", "budget_tokens": 4096}
        body, _agentcc, _headers = _build_body_and_agentcc_params(
            model="o1",
            messages=[{"role": "user", "content": "Hello"}],
            thinking=thinking_config,
        )
        assert body["thinking"] == thinking_config

    def test_reasoning_effort_in_body(self) -> None:
        from fi.gateway.resources.chat.completions import _build_body_and_agentcc_params

        body, _agentcc, _headers = _build_body_and_agentcc_params(
            model="o1",
            messages=[{"role": "user", "content": "Hello"}],
            reasoning_effort="high",
        )
        assert body["reasoning_effort"] == "high"

    def test_drop_params_in_body(self) -> None:
        from fi.gateway.resources.chat.completions import _build_body_and_agentcc_params

        body, _agentcc, _headers = _build_body_and_agentcc_params(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
            drop_params=True,
        )
        assert body["drop_params"] is True

    def test_not_given_excluded(self) -> None:
        from fi.gateway.resources.chat.completions import _build_body_and_agentcc_params

        body, _agentcc, _headers = _build_body_and_agentcc_params(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
        )
        assert "thinking" not in body
        assert "reasoning_effort" not in body
        assert "drop_params" not in body


# ---------------------------------------------------------------------------
# return_raw_request
# ---------------------------------------------------------------------------


class TestReturnRawRequest:
    def test_basic_structure(self) -> None:
        from fi.gateway._utils import return_raw_request

        result = return_raw_request(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
        )
        assert result["method"] == "POST"
        assert result["url"] == "https://gateway.futureagi.com/v1/chat/completions"
        assert "Content-Type" in result["headers"]
        assert result["headers"]["Content-Type"] == "application/json"
        assert "Authorization" in result["headers"]
        assert "[REDACTED]" in result["headers"]["Authorization"]
        assert result["body"]["model"] == "gpt-4o"
        assert result["body"]["messages"] == [{"role": "user", "content": "Hello"}]

    def test_custom_base_url(self) -> None:
        from fi.gateway._utils import return_raw_request

        result = return_raw_request(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hi"}],
            base_url="https://my-gateway.example.com",
        )
        assert result["url"] == "https://my-gateway.example.com/v1/chat/completions"

    def test_trailing_slash_stripped(self) -> None:
        from fi.gateway._utils import return_raw_request

        result = return_raw_request(
            model="gpt-4o",
            messages=[],
            base_url="https://example.com/",
        )
        assert result["url"] == "https://example.com/v1/chat/completions"

    def test_extra_kwargs_included(self) -> None:
        from fi.gateway._utils import return_raw_request

        result = return_raw_request(
            model="gpt-4o",
            messages=[],
            temperature=0.7,
            max_tokens=100,
        )
        assert result["body"]["temperature"] == 0.7
        assert result["body"]["max_tokens"] == 100

    def test_not_given_excluded(self) -> None:
        from fi.gateway._constants import NOT_GIVEN
        from fi.gateway._utils import return_raw_request

        result = return_raw_request(
            model="gpt-4o",
            messages=[],
            temperature=NOT_GIVEN,
        )
        assert "temperature" not in result["body"]

    def test_user_agent_contains_version(self) -> None:
        from fi.gateway._constants import __version__
        from fi.gateway._utils import return_raw_request

        result = return_raw_request(model="gpt-4o", messages=[])
        assert result["headers"]["User-Agent"] == f"agentcc-python/{__version__}"


# ---------------------------------------------------------------------------
# check_valid_key
# ---------------------------------------------------------------------------


class TestCheckValidKey:
    def test_returns_true_on_200(self) -> None:
        from fi.gateway._utils import check_valid_key

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("fi.gateway._utils.httpx.get", return_value=mock_response):
            assert check_valid_key("sk-test", "https://api.agentcc.ai") is True

    def test_returns_false_on_401(self) -> None:
        from fi.gateway._utils import check_valid_key

        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch("fi.gateway._utils.httpx.get", return_value=mock_response):
            assert check_valid_key("bad-key", "https://api.agentcc.ai") is False

    def test_returns_false_on_exception(self) -> None:
        from fi.gateway._utils import check_valid_key

        with patch("fi.gateway._utils.httpx.get", side_effect=Exception("network error")):
            assert check_valid_key("sk-test", "https://api.agentcc.ai") is False

    def test_return_type_is_bool(self) -> None:
        from fi.gateway._utils import check_valid_key

        with patch("fi.gateway._utils.httpx.get", side_effect=Exception("timeout")):
            result = check_valid_key("sk-test", "https://api.agentcc.ai")
            assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# Privacy toggle (redact_messages)
# ---------------------------------------------------------------------------


class TestRedactMessages:
    def test_default_is_false(self) -> None:
        from fi.gateway._client import AgentCC

        client = AgentCC(api_key="sk-test", base_url="http://localhost:8080")
        assert client.redact_messages is False

    def test_set_via_constructor(self) -> None:
        from fi.gateway._client import AgentCC

        client = AgentCC(api_key="sk-test", base_url="http://localhost:8080", redact_messages=True)
        assert client.redact_messages is True

    def test_setter(self) -> None:
        from fi.gateway._client import AgentCC

        client = AgentCC(api_key="sk-test", base_url="http://localhost:8080")
        assert client.redact_messages is False
        client.redact_messages = True
        assert client.redact_messages is True

    def test_async_default_is_false(self) -> None:
        from fi.gateway._client import AsyncAgentCC

        client = AsyncAgentCC(api_key="sk-test", base_url="http://localhost:8080")
        assert client.redact_messages is False

    def test_async_set_via_constructor(self) -> None:
        from fi.gateway._client import AsyncAgentCC

        client = AsyncAgentCC(api_key="sk-test", base_url="http://localhost:8080", redact_messages=True)
        assert client.redact_messages is True

    def test_async_setter(self) -> None:
        from fi.gateway._client import AsyncAgentCC

        client = AsyncAgentCC(api_key="sk-test", base_url="http://localhost:8080")
        client.redact_messages = True
        assert client.redact_messages is True


# ---------------------------------------------------------------------------
# Lazy imports from fi.gateway module
# ---------------------------------------------------------------------------


class TestLazyImports:
    def test_supports_vision(self) -> None:
        import fi.gateway as agentcc

        assert callable(agentcc.supports_vision)
        assert agentcc.supports_vision("gpt-4o") is True

    def test_supports_function_calling(self) -> None:
        import fi.gateway as agentcc

        assert callable(agentcc.supports_function_calling)

    def test_supports_json_mode(self) -> None:
        import fi.gateway as agentcc

        assert callable(agentcc.supports_json_mode)

    def test_supports_response_schema(self) -> None:
        import fi.gateway as agentcc

        assert callable(agentcc.supports_response_schema)

    def test_to_response_format(self) -> None:
        import fi.gateway as agentcc

        assert callable(agentcc.to_response_format)

    def test_return_raw_request(self) -> None:
        import fi.gateway as agentcc

        assert callable(agentcc.return_raw_request)
        result = agentcc.return_raw_request(model="gpt-4o", messages=[])
        assert result["method"] == "POST"

    def test_check_valid_key(self) -> None:
        import fi.gateway as agentcc

        assert callable(agentcc.check_valid_key)

    def test_all_new_functions_in_all(self) -> None:
        import fi.gateway as agentcc

        new_names = [
            "supports_vision",
            "supports_function_calling",
            "supports_json_mode",
            "supports_response_schema",
            "to_response_format",
            "return_raw_request",
            "check_valid_key",
        ]
        for name in new_names:
            assert name in agentcc.__all__, f"{name!r} not in agentcc.__all__"
