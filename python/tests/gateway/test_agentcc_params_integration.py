"""Tests for AgentCC-specific params (session_id, trace_id, cache_ttl, etc.) across all resources."""

from __future__ import annotations

import json

import pytest
import respx

from fi.gateway._client import AsyncAgentCC, AgentCC

# --- Fixtures ---

COMPLETION_RESPONSE = {
    "id": "cmpl-001",
    "object": "text_completion",
    "created": 1700000000,
    "model": "gpt-3.5-turbo-instruct",
    "choices": [{"text": "Hello!", "index": 0, "logprobs": None, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
}

RESPONSE_OBJECT = {
    "id": "resp-001",
    "object": "response",
    "model": "gpt-4o",
    "created_at": 1700000000,
    "status": "completed",
    "output": [{"type": "message", "content": [{"type": "output_text", "text": "Hi!"}]}],
    "usage": {"input_tokens": 5, "output_tokens": 2, "total_tokens": 7},
}

TRANSCRIPTION_RESPONSE = {"text": "Hello, world!"}
TRANSLATION_RESPONSE = {"text": "Bonjour le monde!"}

FILE_OBJECT = {
    "id": "file-abc",
    "object": "file",
    "bytes": 512,
    "created_at": 1700000000,
    "filename": "data.jsonl",
    "purpose": "batch",
}


# --- AgentCC params helper tests ---


class TestAgentCCParamsModule:
    def test_collect_agentcc_params_empty(self) -> None:
        from fi.gateway._agentcc_params import collect_agentcc_params

        result = collect_agentcc_params()
        assert result == {}

    def test_collect_agentcc_params_partial(self) -> None:
        from fi.gateway._agentcc_params import collect_agentcc_params

        result = collect_agentcc_params(session_id="sess-1", cache_ttl=300)
        assert result == {"session_id": "sess-1", "cache_ttl": 300}

    def test_collect_agentcc_params_full(self) -> None:
        from fi.gateway._agentcc_params import collect_agentcc_params

        result = collect_agentcc_params(
            session_id="s",
            trace_id="t",
            request_metadata={"k": "v"},
            request_timeout=30,
            cache_ttl=60,
            cache_namespace="ns",
            cache_force_refresh=True,
            cache_control="no-cache",
            guardrail_policy="strict",
        )
        assert len(result) == 9

    def test_build_extra_headers_empty(self) -> None:
        from fi.gateway._agentcc_params import build_extra_headers

        result = build_extra_headers()
        assert result == {}

    def test_build_extra_headers_with_properties(self) -> None:
        from fi.gateway._agentcc_params import build_extra_headers

        result = build_extra_headers(properties={"env": "prod", "team": "ml"})
        assert result == {"x-agentcc-property-env": "prod", "x-agentcc-property-team": "ml"}

    def test_build_extra_headers_with_user_and_request_id(self) -> None:
        from fi.gateway._agentcc_params import build_extra_headers

        result = build_extra_headers(user_id="user-1", request_id="req-1")
        assert result == {"x-agentcc-user-id": "user-1", "x-agentcc-request-id": "req-1"}

    def test_build_extra_headers_merges_extra_headers(self) -> None:
        from fi.gateway._agentcc_params import build_extra_headers

        result = build_extra_headers(
            extra_headers={"X-Custom": "value"},
            user_id="u1",
        )
        assert result["X-Custom"] == "value"
        assert result["x-agentcc-user-id"] == "u1"

    def test_merge_session_headers_no_session(self) -> None:
        from fi.gateway._agentcc_params import merge_session_headers

        class MockClient:
            _active_session = None

        result = merge_session_headers(MockClient(), {"X-Existing": "v"})
        assert result == {"X-Existing": "v"}


# --- Completions with AgentCC params ---


class TestCompletionsAgentCCParams:
    @respx.mock
    def test_completions_with_session_id(self) -> None:
        route = respx.post("http://gw.test/v1/completions").respond(200, json=COMPLETION_RESPONSE)
        client = AgentCC(api_key="sk-test", base_url="http://gw.test")
        client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt="Hello",
            session_id="sess-abc",
        )
        req = route.calls[0].request
        assert req.headers.get("x-agentcc-session-id") == "sess-abc"

    @respx.mock
    def test_completions_with_all_agentcc_params(self) -> None:
        route = respx.post("http://gw.test/v1/completions").respond(200, json=COMPLETION_RESPONSE)
        client = AgentCC(api_key="sk-test", base_url="http://gw.test")
        client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt="Hello",
            session_id="sess-1",
            trace_id="trace-1",
            cache_ttl=120,
            guardrail_policy="strict",
            user_id="user-42",
            request_id="req-99",
            properties={"env": "prod"},
        )
        req = route.calls[0].request
        assert req.headers.get("x-agentcc-session-id") == "sess-1"
        assert req.headers.get("x-agentcc-trace-id") == "trace-1"
        assert req.headers.get("x-agentcc-user-id") == "user-42"
        assert req.headers.get("x-agentcc-request-id") == "req-99"
        assert req.headers.get("x-agentcc-property-env") == "prod"

    @respx.mock
    def test_completions_body_does_not_contain_agentcc_params(self) -> None:
        route = respx.post("http://gw.test/v1/completions").respond(200, json=COMPLETION_RESPONSE)
        client = AgentCC(api_key="sk-test", base_url="http://gw.test")
        client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt="Hello",
            session_id="sess-1",
            trace_id="trace-1",
        )
        body = json.loads(route.calls[0].request.content)
        assert "session_id" not in body
        assert "trace_id" not in body
        assert body["model"] == "gpt-3.5-turbo-instruct"
        assert body["prompt"] == "Hello"


# --- Responses with AgentCC params ---


class TestResponsesAgentCCParams:
    @respx.mock
    def test_responses_with_session_id(self) -> None:
        route = respx.post("http://gw.test/v1/responses").respond(200, json=RESPONSE_OBJECT)
        client = AgentCC(api_key="sk-test", base_url="http://gw.test")
        client.responses.create(
            model="gpt-4o",
            input="Hi",
            session_id="sess-resp",
        )
        req = route.calls[0].request
        assert req.headers.get("x-agentcc-session-id") == "sess-resp"

    @respx.mock
    def test_responses_with_all_agentcc_params(self) -> None:
        route = respx.post("http://gw.test/v1/responses").respond(200, json=RESPONSE_OBJECT)
        client = AgentCC(api_key="sk-test", base_url="http://gw.test")
        client.responses.create(
            model="gpt-4o",
            input="Hello",
            session_id="s",
            trace_id="t",
            cache_ttl=60,
            guardrail_policy="warn",
            user_id="u1",
            request_id="r1",
            properties={"team": "backend"},
        )
        req = route.calls[0].request
        assert req.headers.get("x-agentcc-session-id") == "s"
        assert req.headers.get("x-agentcc-trace-id") == "t"
        assert req.headers.get("x-agentcc-user-id") == "u1"
        assert req.headers.get("x-agentcc-request-id") == "r1"
        assert req.headers.get("x-agentcc-property-team") == "backend"

    @respx.mock
    def test_responses_body_does_not_contain_agentcc_params(self) -> None:
        route = respx.post("http://gw.test/v1/responses").respond(200, json=RESPONSE_OBJECT)
        client = AgentCC(api_key="sk-test", base_url="http://gw.test")
        client.responses.create(
            model="gpt-4o",
            input="Hi",
            session_id="s1",
        )
        body = json.loads(route.calls[0].request.content)
        assert "session_id" not in body
        assert body["model"] == "gpt-4o"


# --- Audio Transcriptions with AgentCC params ---


class TestAudioAgentCCParams:
    @respx.mock
    def test_transcriptions_with_agentcc_params(self) -> None:
        route = respx.post("http://gw.test/v1/audio/transcriptions").respond(
            200, json=TRANSCRIPTION_RESPONSE
        )
        client = AgentCC(api_key="sk-test", base_url="http://gw.test")
        client.audio.transcriptions.create(
            file="audio-data",
            model="whisper-1",
            session_id="sess-audio",
            trace_id="trace-audio",
        )
        req = route.calls[0].request
        assert req.headers.get("x-agentcc-session-id") == "sess-audio"
        assert req.headers.get("x-agentcc-trace-id") == "trace-audio"

    @respx.mock
    def test_translations_with_agentcc_params(self) -> None:
        route = respx.post("http://gw.test/v1/audio/translations").respond(
            200, json=TRANSLATION_RESPONSE
        )
        client = AgentCC(api_key="sk-test", base_url="http://gw.test")
        client.audio.translations.create(
            file="audio-data",
            model="whisper-1",
            session_id="sess-trans",
            user_id="user-lang",
        )
        req = route.calls[0].request
        assert req.headers.get("x-agentcc-session-id") == "sess-trans"
        assert req.headers.get("x-agentcc-user-id") == "user-lang"

    @respx.mock
    def test_speech_with_agentcc_params(self) -> None:
        route = respx.post("http://gw.test/v1/audio/speech").respond(200, content=b"audio-bytes")
        client = AgentCC(api_key="sk-test", base_url="http://gw.test")
        result = client.audio.speech.create(
            model="tts-1",
            input="Hello world",
            voice="alloy",
            session_id="sess-tts",
            trace_id="trace-tts",
        )
        assert isinstance(result, bytes)
        req = route.calls[0].request
        assert req.headers.get("x-agentcc-session-id") == "sess-tts"
        assert req.headers.get("x-agentcc-trace-id") == "trace-tts"


# --- Files with AgentCC params ---


class TestFilesAgentCCParams:
    @respx.mock
    def test_files_create_with_agentcc_params(self) -> None:
        route = respx.post("http://gw.test/v1/files").respond(200, json=FILE_OBJECT)
        client = AgentCC(api_key="sk-test", base_url="http://gw.test")
        client.files.create(
            file="data",
            purpose="batch",
            session_id="sess-file",
            trace_id="trace-file",
            user_id="user-file",
        )
        req = route.calls[0].request
        assert req.headers.get("x-agentcc-session-id") == "sess-file"
        assert req.headers.get("x-agentcc-trace-id") == "trace-file"
        assert req.headers.get("x-agentcc-user-id") == "user-file"


# --- Async variants ---


class TestAsyncAgentCCParams:
    @respx.mock
    @pytest.mark.anyio
    async def test_async_completions_with_agentcc_params(self) -> None:
        route = respx.post("http://gw.test/v1/completions").respond(200, json=COMPLETION_RESPONSE)
        client = AsyncAgentCC(api_key="sk-test", base_url="http://gw.test")
        await client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt="Hi",
            session_id="async-sess",
        )
        req = route.calls[0].request
        assert req.headers.get("x-agentcc-session-id") == "async-sess"

    @respx.mock
    @pytest.mark.anyio
    async def test_async_responses_with_agentcc_params(self) -> None:
        route = respx.post("http://gw.test/v1/responses").respond(200, json=RESPONSE_OBJECT)
        client = AsyncAgentCC(api_key="sk-test", base_url="http://gw.test")
        await client.responses.create(
            model="gpt-4o",
            input="Hi",
            session_id="async-resp",
            trace_id="async-trace",
        )
        req = route.calls[0].request
        assert req.headers.get("x-agentcc-session-id") == "async-resp"
        assert req.headers.get("x-agentcc-trace-id") == "async-trace"

    @respx.mock
    @pytest.mark.anyio
    async def test_async_transcriptions_with_agentcc_params(self) -> None:
        route = respx.post("http://gw.test/v1/audio/transcriptions").respond(
            200, json=TRANSCRIPTION_RESPONSE
        )
        client = AsyncAgentCC(api_key="sk-test", base_url="http://gw.test")
        await client.audio.transcriptions.create(
            file="data",
            model="whisper-1",
            session_id="async-audio",
        )
        req = route.calls[0].request
        assert req.headers.get("x-agentcc-session-id") == "async-audio"

    @respx.mock
    @pytest.mark.anyio
    async def test_async_files_create_with_agentcc_params(self) -> None:
        route = respx.post("http://gw.test/v1/files").respond(200, json=FILE_OBJECT)
        client = AsyncAgentCC(api_key="sk-test", base_url="http://gw.test")
        await client.files.create(
            file="data",
            purpose="batch",
            session_id="async-file",
        )
        req = route.calls[0].request
        assert req.headers.get("x-agentcc-session-id") == "async-file"
