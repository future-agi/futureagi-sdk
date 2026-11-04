"""Tests for AgentCC and AsyncAgentCC client classes (Steps 6+7)."""

from __future__ import annotations

import os

import pytest
import respx

from fi.gateway._client import AgentCC, AsyncAgentCC

GATEWAY_RESPONSE = {
    "id": "chatcmpl-abc123",
    "object": "chat.completion",
    "created": 1709000000,
    "model": "gpt-4o",
    "choices": [
        {
            "index": 0,
            "message": {"role": "assistant", "content": "Hello!"},
            "finish_reason": "stop",
        }
    ],
    "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
}

GATEWAY_HEADERS = {
    "x-agentcc-request-id": "req-abc",
    "x-agentcc-trace-id": "trace-xyz",
    "x-agentcc-provider": "openai",
    "x-agentcc-latency-ms": "42",
}


# --- Client construction tests ---


class TestClientConstruction:
    def test_basic_construction(self) -> None:
        client = AgentCC(api_key="sk-test-key", base_url="http://localhost:8080")
        assert repr(client) == "AgentCC(base_url='http://localhost:8080', api_key='***')"

    def test_long_api_key_redacted(self) -> None:
        client = AgentCC(api_key="sk-agentcc-1234567890abcdef", base_url="http://localhost:8080")
        r = repr(client)
        assert "sk-agentcc..." in r
        assert "cdef" in r

    def test_no_api_key_raises(self) -> None:
        from fi.gateway._exceptions import AgentCCError

        env = {k: v for k, v in os.environ.items() if k != "AGENTCC_API_KEY"}
        with pytest.raises(AgentCCError, match="api_key is required"):
            os_environ = os.environ.copy()
            os.environ.clear()
            os.environ.update(env)
            try:
                AgentCC(base_url="http://localhost:8080")
            finally:
                os.environ.clear()
                os.environ.update(os_environ)

    def test_no_base_url_raises(self) -> None:
        from fi.gateway._exceptions import AgentCCError

        env = {k: v for k, v in os.environ.items() if k != "AGENTCC_BASE_URL"}
        with pytest.raises(AgentCCError, match="base_url is required"):
            os_environ = os.environ.copy()
            os.environ.clear()
            os.environ.update(env)
            try:
                AgentCC(api_key="sk-test")
            finally:
                os.environ.clear()
                os.environ.update(os_environ)

    def test_env_var_construction(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AGENTCC_API_KEY", "sk-from-env")
        monkeypatch.setenv("AGENTCC_BASE_URL", "http://env-gateway:8080")
        client = AgentCC()
        assert "env-gateway" in repr(client)

    def test_chat_property_returns_chat(self) -> None:
        client = AgentCC(api_key="sk-test", base_url="http://localhost:8080")
        from fi.gateway.resources.chat import Chat

        assert isinstance(client.chat, Chat)

    def test_chat_property_cached(self) -> None:
        client = AgentCC(api_key="sk-test", base_url="http://localhost:8080")
        chat1 = client.chat
        chat2 = client.chat
        assert chat1 is chat2

    def test_context_manager(self) -> None:
        with AgentCC(api_key="sk-test", base_url="http://localhost:8080") as client:
            assert isinstance(client, AgentCC)

    def test_with_options_returns_new_client(self) -> None:
        client = AgentCC(api_key="sk-test", base_url="http://localhost:8080")
        new = client.with_options(timeout=30.0, session_id="new-session")
        assert new is not client
        assert new._session_id == "new-session"
        assert new._user_copied is True

    def test_with_options_shares_pool(self) -> None:
        client = AgentCC(api_key="sk-test", base_url="http://localhost:8080")
        # Force base client creation
        _ = client._get_base_client()
        new = client.with_options(timeout=30.0)
        # The pool is shared; the base client is not, so the overrides take effect.
        assert new._get_base_client() is not client._base_client
        assert new._get_base_client()._ensure_client() is client._base_client._ensure_client()
        assert new._get_base_client()._timeout.read == 30.0


# --- End-to-end tests with mocked gateway ---


class TestEndToEnd:
    @respx.mock
    def test_chat_completions_create(self) -> None:
        respx.post("http://gateway.test/v1/chat/completions").respond(
            200, json=GATEWAY_RESPONSE, headers=GATEWAY_HEADERS,
        )
        client = AgentCC(api_key="sk-test-key", base_url="http://gateway.test")
        result = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
        )
        assert result.id == "chatcmpl-abc123"
        assert result.choices[0].message.content == "Hello!"
        assert result.agentcc is not None
        assert result.agentcc.request_id == "req-abc"
        assert result.agentcc.provider == "openai"

    @respx.mock
    def test_agentcc_params_sent_as_headers(self) -> None:
        route = respx.post("http://gateway.test/v1/chat/completions").respond(
            200, json=GATEWAY_RESPONSE, headers=GATEWAY_HEADERS,
        )
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
            session_id="sess-123",
            cache_ttl="10m",
        )
        request = route.calls[0].request
        assert request.headers["x-agentcc-session-id"] == "sess-123"
        assert request.headers["x-agentcc-cache-ttl"] == "10m"

    @respx.mock
    def test_extra_headers_sent(self) -> None:
        route = respx.post("http://gateway.test/v1/chat/completions").respond(
            200, json=GATEWAY_RESPONSE, headers=GATEWAY_HEADERS,
        )
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
            extra_headers={"x-custom-header": "value"},
        )
        request = route.calls[0].request
        assert request.headers["x-custom-header"] == "value"

    @respx.mock
    def test_extra_body_merged(self) -> None:
        route = respx.post("http://gateway.test/v1/chat/completions").respond(
            200, json=GATEWAY_RESPONSE, headers=GATEWAY_HEADERS,
        )
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
            extra_body={"custom_field": "custom_value"},
        )
        import json
        request = route.calls[0].request
        body = json.loads(request.content)
        assert body["custom_field"] == "custom_value"

    @respx.mock
    def test_not_given_params_excluded_from_body(self) -> None:
        route = respx.post("http://gateway.test/v1/chat/completions").respond(
            200, json=GATEWAY_RESPONSE, headers=GATEWAY_HEADERS,
        )
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
            # temperature, top_p, etc. are NOT_GIVEN — should NOT appear in body
        )
        import json
        request = route.calls[0].request
        body = json.loads(request.content)
        assert "temperature" not in body
        assert "top_p" not in body
        assert "model" in body
        assert "messages" in body

    @respx.mock
    def test_400_raises_bad_request(self) -> None:
        from fi.gateway._exceptions import BadRequestError

        respx.post("http://gateway.test/v1/chat/completions").respond(
            400, json={"error": {"message": "Invalid model"}},
        )
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        with pytest.raises(BadRequestError):
            client.chat.completions.create(
                model="nonexistent", messages=[{"role": "user", "content": "Hi"}],
            )

    @respx.mock
    def test_446_raises_guardrail_blocked(self) -> None:
        from fi.gateway._exceptions import GuardrailBlockedError

        respx.post("http://gateway.test/v1/chat/completions").respond(
            446,
            json={"error": {"message": "Content blocked"}},
            headers={"x-agentcc-guardrail-name": "prompt-guard"},
        )
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        with pytest.raises(GuardrailBlockedError) as exc_info:
            client.chat.completions.create(
                model="gpt-4o", messages=[{"role": "user", "content": "bad content"}],
            )
        assert exc_info.value.guardrail_name == "prompt-guard"

    @respx.mock
    def test_246_raises_guardrail_warning(self) -> None:
        from fi.gateway._exceptions import GuardrailWarning

        body = {
            **GATEWAY_RESPONSE,
            "error": {"message": "Sensitive content detected"},
        }
        respx.post("http://gateway.test/v1/chat/completions").respond(
            246, json=body,
            headers={
                **GATEWAY_HEADERS,
                "x-agentcc-guardrail-name": "content-filter",
                "x-agentcc-guardrail-action": "warn",
            },
        )
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        with pytest.raises(GuardrailWarning) as exc_info:
            client.chat.completions.create(
                model="gpt-4o", messages=[{"role": "user", "content": "borderline content"}],
            )
        assert exc_info.value.completion is not None
        assert exc_info.value.guardrail_name == "content-filter"


# --- AsyncAgentCC tests ---


class TestAsyncClient:
    def test_async_construction(self) -> None:
        client = AsyncAgentCC(api_key="sk-test", base_url="http://localhost:8080")
        assert "AsyncAgentCC" in repr(client)

    def test_async_chat_property(self) -> None:
        client = AsyncAgentCC(api_key="sk-test", base_url="http://localhost:8080")
        from fi.gateway.resources.chat import AsyncChat

        assert isinstance(client.chat, AsyncChat)

    @respx.mock
    @pytest.mark.anyio
    async def test_async_create(self) -> None:
        respx.post("http://gateway.test/v1/chat/completions").respond(
            200, json=GATEWAY_RESPONSE, headers=GATEWAY_HEADERS,
        )
        client = AsyncAgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
        )
        assert result.id == "chatcmpl-abc123"
        assert result.agentcc is not None

    @pytest.mark.anyio
    async def test_async_context_manager(self) -> None:
        async with AsyncAgentCC(api_key="sk-test", base_url="http://localhost:8080") as client:
            assert isinstance(client, AsyncAgentCC)
