"""Chat completions: current overloads/decomposition with released request adapters."""

from __future__ import annotations

from typing import Any, Literal as _Literal, cast as _cast, overload as _overload

from fi.gateway._constants import NOT_GIVEN, _NotGiven
from fi.gateway._streaming import Stream as _Stream
from fi.gateway._streaming._manager import StreamManager
from fi.gateway.resources.chat._async_completions import AsyncChatCompletions
from fi.gateway.resources.chat._params import (
    _arguments, _build_body_and_agentcc_params, _check_pre_call_rules,
    _maybe_validate_json_schema, _mock_result, _mock_stream_generator, _prepare, _wants_stream,
)
from fi.gateway.types.chat.chat_completion import ChatCompletion
from fi.gateway.types.chat.chat_completion_chunk import ChatCompletionChunk

__all__ = [
    "AsyncChatCompletions", "ChatCompletions", "_build_body_and_agentcc_params",
    "_maybe_validate_json_schema", "_mock_stream_generator",
]


class ChatCompletions:
    """Sync chat completions resource."""

    def __init__(self, client: Any) -> None:
        self._client = client

    @_overload
    def create(self, *, model: str, messages: list[dict[str, Any]],
               stream: _Literal[False] | _NotGiven | None = NOT_GIVEN,
               mock_response: str | None = None,
               properties: dict[str, str] | None = None,
               user_id: str | None = None, request_id: str | None = None,
               extra_headers: dict[str, str] | None = None,
               extra_body: dict[str, Any] | None = None,
               **kwargs: Any) -> ChatCompletion: ...

    @_overload
    def create(self, *, model: str, messages: list[dict[str, Any]],
               stream: _Literal[True], mock_response: None = None,
               properties: dict[str, str] | None = None,
               user_id: str | None = None, request_id: str | None = None,
               extra_headers: dict[str, str] | None = None,
               extra_body: dict[str, Any] | None = None,
               **kwargs: Any) -> _Stream: ...

    @_overload
    def create(self, *, model: str, messages: list[dict[str, Any]],
               stream: _Literal[True], mock_response: str,
               properties: dict[str, str] | None = None,
               user_id: str | None = None, request_id: str | None = None,
               extra_headers: dict[str, str] | None = None,
               extra_body: dict[str, Any] | None = None,
               **kwargs: Any) -> StreamManager: ...

    @_overload
    def create(self, *, model: str, messages: list[dict[str, Any]],
               stream: bool | _NotGiven | None,
               mock_response: str | None = None,
               properties: dict[str, str] | None = None,
               user_id: str | None = None, request_id: str | None = None,
               extra_headers: dict[str, str] | None = None,
               extra_body: dict[str, Any] | None = None,
               **kwargs: Any) -> ChatCompletion | _Stream | StreamManager: ...

    def create(
        self, *, model: str, messages: list[dict[str, Any]],
        temperature: Any = NOT_GIVEN, top_p: Any = NOT_GIVEN, n: Any = NOT_GIVEN,
        stream: Any = NOT_GIVEN, stream_options: Any = NOT_GIVEN, stop: Any = NOT_GIVEN,
        max_tokens: Any = NOT_GIVEN, max_completion_tokens: Any = NOT_GIVEN,
        presence_penalty: Any = NOT_GIVEN, frequency_penalty: Any = NOT_GIVEN,
        logit_bias: Any = NOT_GIVEN, logprobs: Any = NOT_GIVEN, top_logprobs: Any = NOT_GIVEN,
        user: Any = NOT_GIVEN, seed: Any = NOT_GIVEN, tools: Any = NOT_GIVEN,
        tool_choice: Any = NOT_GIVEN, response_format: Any = NOT_GIVEN,
        service_tier: Any = NOT_GIVEN, thinking: Any = NOT_GIVEN,
        reasoning_effort: Any = NOT_GIVEN, drop_params: Any = NOT_GIVEN,
        session_id: Any = NOT_GIVEN, trace_id: Any = NOT_GIVEN,
        request_metadata: Any = NOT_GIVEN, request_timeout: Any = NOT_GIVEN,
        cache_ttl: Any = NOT_GIVEN, cache_namespace: Any = NOT_GIVEN,
        cache_force_refresh: Any = NOT_GIVEN, cache_control: Any = NOT_GIVEN,
        guardrail_policy: Any = NOT_GIVEN, properties: dict[str, str] | None = None,
        user_id: str | None = None, request_id: str | None = None,
        extra_headers: dict[str, str] | None = None, extra_body: dict[str, Any] | None = None,
        timeout: Any = NOT_GIVEN, mock_response: str | None = None, **kwargs: Any,
    ) -> ChatCompletion | _Stream | StreamManager:
        args = _arguments(locals())
        _check_pre_call_rules(self._client, model, messages, kwargs)
        if mock_response is not None:
            return _mock_result(self._client, model, mock_response, stream, response_format)
        opts, agentcc_params = _prepare(self._client, args)
        if _wants_stream(stream):
            return self._client._get_base_client()._open_stream(opts, agentcc_params, ChatCompletionChunk)
        result = self._client._get_base_client()._request_with_retry(opts, ChatCompletion, agentcc_params)
        if getattr(self._client, "_enable_json_schema_validation", False):
            _maybe_validate_json_schema(result, response_format)
        return _cast(ChatCompletion, result)

    def stream(
        self, *, model: str, messages: list[dict[str, Any]],
        temperature: Any = NOT_GIVEN, top_p: Any = NOT_GIVEN, n: Any = NOT_GIVEN,
        stream_options: Any = NOT_GIVEN, stop: Any = NOT_GIVEN,
        max_tokens: Any = NOT_GIVEN, max_completion_tokens: Any = NOT_GIVEN,
        presence_penalty: Any = NOT_GIVEN, frequency_penalty: Any = NOT_GIVEN,
        logit_bias: Any = NOT_GIVEN, logprobs: Any = NOT_GIVEN, top_logprobs: Any = NOT_GIVEN,
        user: Any = NOT_GIVEN, seed: Any = NOT_GIVEN, tools: Any = NOT_GIVEN,
        tool_choice: Any = NOT_GIVEN, response_format: Any = NOT_GIVEN,
        service_tier: Any = NOT_GIVEN, thinking: Any = NOT_GIVEN,
        reasoning_effort: Any = NOT_GIVEN, drop_params: Any = NOT_GIVEN,
        session_id: Any = NOT_GIVEN, trace_id: Any = NOT_GIVEN,
        request_metadata: Any = NOT_GIVEN, request_timeout: Any = NOT_GIVEN,
        cache_ttl: Any = NOT_GIVEN, cache_namespace: Any = NOT_GIVEN,
        cache_force_refresh: Any = NOT_GIVEN, cache_control: Any = NOT_GIVEN,
        guardrail_policy: Any = NOT_GIVEN, properties: dict[str, str] | None = None,
        user_id: str | None = None, request_id: str | None = None,
        extra_headers: dict[str, str] | None = None, extra_body: dict[str, Any] | None = None,
        timeout: Any = NOT_GIVEN, **kwargs: Any,
    ) -> StreamManager:
        """Return an accumulating event/text stream manager."""
        args = _arguments(locals(), stream=True)
        _check_pre_call_rules(self._client, model, messages, kwargs)
        opts, agentcc_params = _prepare(self._client, args)
        stream = self._client._get_base_client()._open_stream(opts, agentcc_params, ChatCompletionChunk)
        return StreamManager(stream)
