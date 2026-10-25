"""Chat completions resource — non-streaming and streaming create methods."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from fi.gateway._base_client import RequestOptions
from fi.gateway._constants import NOT_GIVEN
from fi.gateway._agentcc_params import AGENTCC_PARAM_KEYS as _AGENTCC_PARAM_KEYS
from fi.gateway._agentcc_params import merge_session_headers as _merge_session_headers
from fi.gateway.types.chat.chat_completion import ChatCompletion


def _build_body_and_agentcc_params(
    *,
    model: str,
    messages: list[dict[str, Any]],
    temperature: Any = NOT_GIVEN,
    top_p: Any = NOT_GIVEN,
    n: Any = NOT_GIVEN,
    stream: Any = NOT_GIVEN,
    stream_options: Any = NOT_GIVEN,
    stop: Any = NOT_GIVEN,
    max_tokens: Any = NOT_GIVEN,
    max_completion_tokens: Any = NOT_GIVEN,
    presence_penalty: Any = NOT_GIVEN,
    frequency_penalty: Any = NOT_GIVEN,
    logit_bias: Any = NOT_GIVEN,
    logprobs: Any = NOT_GIVEN,
    top_logprobs: Any = NOT_GIVEN,
    user: Any = NOT_GIVEN,
    seed: Any = NOT_GIVEN,
    tools: Any = NOT_GIVEN,
    tool_choice: Any = NOT_GIVEN,
    response_format: Any = NOT_GIVEN,
    service_tier: Any = NOT_GIVEN,
    thinking: Any = NOT_GIVEN,
    reasoning_effort: Any = NOT_GIVEN,
    drop_params: Any = NOT_GIVEN,
    session_id: Any = NOT_GIVEN,
    trace_id: Any = NOT_GIVEN,
    request_metadata: Any = NOT_GIVEN,
    request_timeout: Any = NOT_GIVEN,
    cache_ttl: Any = NOT_GIVEN,
    cache_namespace: Any = NOT_GIVEN,
    cache_force_refresh: Any = NOT_GIVEN,
    cache_control: Any = NOT_GIVEN,
    guardrail_policy: Any = NOT_GIVEN,
    properties: dict[str, str] | None = None,
    user_id: str | None = None,
    request_id: str | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_body: dict[str, Any] | None = None,
    timeout: Any = NOT_GIVEN,
    **kwargs: Any,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    """Build the request body, agentcc params dict, and extra headers."""
    body: dict[str, Any] = {"model": model, "messages": messages}

    # Add standard OpenAI params (only if not NOT_GIVEN)
    _locals = {
        "temperature": temperature,
        "top_p": top_p,
        "n": n,
        "stream": stream,
        "stream_options": stream_options,
        "stop": stop,
        "max_tokens": max_tokens,
        "max_completion_tokens": max_completion_tokens,
        "presence_penalty": presence_penalty,
        "frequency_penalty": frequency_penalty,
        "logit_bias": logit_bias,
        "logprobs": logprobs,
        "top_logprobs": top_logprobs,
        "user": user,
        "seed": seed,
        "tools": tools,
        "tool_choice": tool_choice,
        "response_format": response_format,
        "service_tier": service_tier,
        "thinking": thinking,
        "reasoning_effort": reasoning_effort,
        "drop_params": drop_params,
    }
    for key, val in _locals.items():
        if val is not NOT_GIVEN:
            body[key] = val

    # Merge extra_body
    if extra_body:
        body.update(extra_body)

    # Merge kwargs
    if kwargs:
        body.update(kwargs)

    # Collect agentcc params (sent as headers, not body)
    agentcc_params: dict[str, Any] = {}
    _agentcc_locals = {
        "session_id": session_id,
        "trace_id": trace_id,
        "request_metadata": request_metadata,
        "request_timeout": request_timeout,
        "cache_ttl": cache_ttl,
        "cache_namespace": cache_namespace,
        "cache_force_refresh": cache_force_refresh,
        "cache_control": cache_control,
        "guardrail_policy": guardrail_policy,
    }
    for key, val in _agentcc_locals.items():
        if val is not NOT_GIVEN:
            agentcc_params[key] = val

    # Build extra headers with new params
    hdrs: dict[str, str] = dict(extra_headers) if extra_headers else {}

    # Custom properties -> x-agentcc-property-{key}
    if properties:
        for key, val in properties.items():
            hdrs[f"x-agentcc-property-{key}"] = val

    # User ID -> x-agentcc-user-id (separate from OpenAI's `user` body param)
    if user_id is not None:
        hdrs["x-agentcc-user-id"] = user_id

    # Request ID -> x-agentcc-request-id
    if request_id is not None:
        hdrs["x-agentcc-request-id"] = request_id

    return body, agentcc_params, hdrs


def _maybe_validate_json_schema(result: Any, response_format: Any) -> None:
    """Validate the response content against JSON schema if response_format contains one."""
    if response_format is NOT_GIVEN or response_format is None:
        return
    schema = None
    if isinstance(response_format, dict):
        json_schema = response_format.get("json_schema", {})
        schema = json_schema.get("schema") if isinstance(json_schema, dict) else None
    if schema is None:
        return
    content = None
    if hasattr(result, "choices") and result.choices:
        msg = result.choices[0].message
        content = getattr(msg, "content", None) if msg else None
    if content is None:
        return
    from fi.gateway._structured import validate_json_response

    if not validate_json_response(content, schema):
        from fi.gateway._exceptions import AgentCCError

        raise AgentCCError(
            "JSON schema validation failed: response does not match the provided schema."
        )


def _check_pre_call_rules(client: Any, model: str, messages: list[dict[str, Any]], kwargs: dict[str, Any]) -> None:
    """Run pre-call rules registered on the client. Raises AgentCCError if any rule blocks."""
    rules = getattr(client, "_pre_call_rules", None)
    if not rules:
        return
    from fi.gateway._exceptions import AgentCCError

    for rule in rules:
        if not rule(model, messages, kwargs):
            raise AgentCCError(f"Request blocked by pre-call rule: {rule.__name__}")


def _mock_stream_generator(model: str, mock_response: str) -> Iterator[Any]:
    """Generate mock ChatCompletionChunk objects that spell out the response word-by-word."""
    from fi.gateway.types.chat.chat_completion_chunk import (
        ChatCompletionChunk,
        Delta,
        StreamChoice,
    )

    words = mock_response.split(" ")
    for i, word in enumerate(words):
        # Add space before words except the first
        content = word if i == 0 else f" {word}"
        chunk = ChatCompletionChunk(
            id="chatcmpl-mock",
            object="chat.completion.chunk",
            created=0,
            model=model,
            choices=[
                StreamChoice(
                    index=0,
                    delta=Delta(role="assistant" if i == 0 else None, content=content),
                    finish_reason=None,
                )
            ],
        )
        yield chunk

    # Final chunk with finish_reason
    from fi.gateway.types.shared import Usage

    yield ChatCompletionChunk(
        id="chatcmpl-mock",
        object="chat.completion.chunk",
        created=0,
        model=model,
        choices=[
            StreamChoice(
                index=0,
                delta=Delta(),
                finish_reason="stop",
            )
        ],
        usage=Usage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
    )


class ChatCompletions:
    """Sync chat completions resource."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def create(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        temperature: Any = NOT_GIVEN,
        top_p: Any = NOT_GIVEN,
        n: Any = NOT_GIVEN,
        stream: Any = NOT_GIVEN,
        stream_options: Any = NOT_GIVEN,
        stop: Any = NOT_GIVEN,
        max_tokens: Any = NOT_GIVEN,
        max_completion_tokens: Any = NOT_GIVEN,
        presence_penalty: Any = NOT_GIVEN,
        frequency_penalty: Any = NOT_GIVEN,
        logit_bias: Any = NOT_GIVEN,
        logprobs: Any = NOT_GIVEN,
        top_logprobs: Any = NOT_GIVEN,
        user: Any = NOT_GIVEN,
        seed: Any = NOT_GIVEN,
        tools: Any = NOT_GIVEN,
        tool_choice: Any = NOT_GIVEN,
        response_format: Any = NOT_GIVEN,
        service_tier: Any = NOT_GIVEN,
        thinking: Any = NOT_GIVEN,
        reasoning_effort: Any = NOT_GIVEN,
        drop_params: Any = NOT_GIVEN,
        session_id: Any = NOT_GIVEN,
        trace_id: Any = NOT_GIVEN,
        request_metadata: Any = NOT_GIVEN,
        request_timeout: Any = NOT_GIVEN,
        cache_ttl: Any = NOT_GIVEN,
        cache_namespace: Any = NOT_GIVEN,
        cache_force_refresh: Any = NOT_GIVEN,
        cache_control: Any = NOT_GIVEN,
        guardrail_policy: Any = NOT_GIVEN,
        properties: dict[str, str] | None = None,
        user_id: str | None = None,
        request_id: str | None = None,
        extra_headers: dict[str, str] | None = None,
        extra_body: dict[str, Any] | None = None,
        timeout: Any = NOT_GIVEN,
        mock_response: str | None = None,
        **kwargs: Any,
    ) -> ChatCompletion | Any:
        # Check pre-call rules
        _check_pre_call_rules(self._client, model, messages, kwargs)

        if mock_response is not None:
            # Handle mock streaming
            if stream is True or (stream is not NOT_GIVEN and stream):
                from fi.gateway._streaming import MockStream, StreamManager

                return StreamManager(MockStream(_mock_stream_generator(model, mock_response)))

            from fi.gateway.types.chat.chat_completion import Choice
            from fi.gateway.types.chat.chat_completion_message import ChatCompletionMessage
            from fi.gateway.types.shared import Usage

            result = ChatCompletion(
                id="chatcmpl-mock",
                object="chat.completion",
                created=0,
                model=model,
                choices=[
                    Choice(
                        index=0,
                        message=ChatCompletionMessage(role="assistant", content=mock_response),
                        finish_reason="stop",
                    )
                ],
                usage=Usage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
            )

            if getattr(self._client, "_enable_json_schema_validation", False):
                _maybe_validate_json_schema(result, response_format)

            return result

        body, agentcc_params, extra_hdrs = _build_body_and_agentcc_params(
            model=model, messages=messages,
            temperature=temperature, top_p=top_p, n=n,
            stream=stream, stream_options=stream_options, stop=stop,
            max_tokens=max_tokens, max_completion_tokens=max_completion_tokens,
            presence_penalty=presence_penalty, frequency_penalty=frequency_penalty,
            logit_bias=logit_bias, logprobs=logprobs, top_logprobs=top_logprobs,
            user=user, seed=seed, tools=tools, tool_choice=tool_choice,
            response_format=response_format, service_tier=service_tier,
            thinking=thinking, reasoning_effort=reasoning_effort,
            drop_params=drop_params,
            session_id=session_id, trace_id=trace_id,
            request_metadata=request_metadata, request_timeout=request_timeout,
            cache_ttl=cache_ttl, cache_namespace=cache_namespace,
            cache_force_refresh=cache_force_refresh, cache_control=cache_control,
            guardrail_policy=guardrail_policy,
            properties=properties, user_id=user_id, request_id=request_id,
            extra_headers=extra_headers, extra_body=extra_body, timeout=timeout,
            **kwargs,
        )

        # Apply modify_params if enabled on the client
        if getattr(self._client, "_modify_params", False):
            from fi.gateway._param_modifier import modify_params_for_provider

            modify_params_for_provider(model, body)

        # Merge session headers if an active session is set on the client
        extra_hdrs = _merge_session_headers(self._client, extra_hdrs)

        from fi.gateway._utils import parse_timeout

        opts = RequestOptions(
            method="POST",
            url="/v1/chat/completions",
            body=body,
            headers=extra_hdrs,
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )

        if stream is True or (stream is not NOT_GIVEN and stream):
            from fi.gateway._streaming import Stream
            response = self._client._get_base_client()._stream_request(opts, agentcc_params)
            return Stream(response)

        result = self._client._get_base_client()._request_with_retry(opts, ChatCompletion, agentcc_params)

        # Auto-validate JSON schema if enabled
        if getattr(self._client, "_enable_json_schema_validation", False):
            _maybe_validate_json_schema(result, response_format)

        return result

    def stream(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        temperature: Any = NOT_GIVEN,
        top_p: Any = NOT_GIVEN,
        n: Any = NOT_GIVEN,
        stream_options: Any = NOT_GIVEN,
        stop: Any = NOT_GIVEN,
        max_tokens: Any = NOT_GIVEN,
        max_completion_tokens: Any = NOT_GIVEN,
        presence_penalty: Any = NOT_GIVEN,
        frequency_penalty: Any = NOT_GIVEN,
        logit_bias: Any = NOT_GIVEN,
        logprobs: Any = NOT_GIVEN,
        top_logprobs: Any = NOT_GIVEN,
        user: Any = NOT_GIVEN,
        seed: Any = NOT_GIVEN,
        tools: Any = NOT_GIVEN,
        tool_choice: Any = NOT_GIVEN,
        response_format: Any = NOT_GIVEN,
        service_tier: Any = NOT_GIVEN,
        thinking: Any = NOT_GIVEN,
        reasoning_effort: Any = NOT_GIVEN,
        drop_params: Any = NOT_GIVEN,
        session_id: Any = NOT_GIVEN,
        trace_id: Any = NOT_GIVEN,
        request_metadata: Any = NOT_GIVEN,
        request_timeout: Any = NOT_GIVEN,
        cache_ttl: Any = NOT_GIVEN,
        cache_namespace: Any = NOT_GIVEN,
        cache_force_refresh: Any = NOT_GIVEN,
        cache_control: Any = NOT_GIVEN,
        guardrail_policy: Any = NOT_GIVEN,
        properties: dict[str, str] | None = None,
        user_id: str | None = None,
        request_id: str | None = None,
        extra_headers: dict[str, str] | None = None,
        extra_body: dict[str, Any] | None = None,
        timeout: Any = NOT_GIVEN,
        **kwargs: Any,
    ) -> Any:
        """Return a StreamManager context manager for consuming a streaming response.

        Usage::

            with client.chat.completions.stream(model="gpt-4o", messages=[...]) as stream:
                for text in stream.text_stream:
                    print(text, end="")
                final = stream.get_final_completion()
        """
        # Check pre-call rules
        _check_pre_call_rules(self._client, model, messages, kwargs)

        from fi.gateway._streaming import Stream, StreamManager

        body, agentcc_params, extra_hdrs = _build_body_and_agentcc_params(
            model=model, messages=messages,
            stream=True, stream_options=stream_options,
            temperature=temperature, top_p=top_p, n=n, stop=stop,
            max_tokens=max_tokens, max_completion_tokens=max_completion_tokens,
            presence_penalty=presence_penalty, frequency_penalty=frequency_penalty,
            logit_bias=logit_bias, logprobs=logprobs, top_logprobs=top_logprobs,
            user=user, seed=seed, tools=tools, tool_choice=tool_choice,
            response_format=response_format, service_tier=service_tier,
            thinking=thinking, reasoning_effort=reasoning_effort,
            drop_params=drop_params,
            session_id=session_id, trace_id=trace_id,
            request_metadata=request_metadata, request_timeout=request_timeout,
            cache_ttl=cache_ttl, cache_namespace=cache_namespace,
            cache_force_refresh=cache_force_refresh, cache_control=cache_control,
            guardrail_policy=guardrail_policy,
            properties=properties, user_id=user_id, request_id=request_id,
            extra_headers=extra_headers, extra_body=extra_body, timeout=timeout,
            **kwargs,
        )

        # Apply modify_params if enabled on the client
        if getattr(self._client, "_modify_params", False):
            from fi.gateway._param_modifier import modify_params_for_provider

            modify_params_for_provider(model, body)

        # Merge session headers if an active session is set on the client
        extra_hdrs = _merge_session_headers(self._client, extra_hdrs)

        from fi.gateway._utils import parse_timeout
        opts = RequestOptions(
            method="POST",
            url="/v1/chat/completions",
            body=body,
            headers=extra_hdrs,
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        response = self._client._get_base_client()._stream_request(opts, agentcc_params)
        return StreamManager(Stream(response))


class AsyncChatCompletions:
    """Async chat completions resource."""

    def __init__(self, client: Any) -> None:
        self._client = client

    async def create(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        temperature: Any = NOT_GIVEN,
        top_p: Any = NOT_GIVEN,
        n: Any = NOT_GIVEN,
        stream: Any = NOT_GIVEN,
        stream_options: Any = NOT_GIVEN,
        stop: Any = NOT_GIVEN,
        max_tokens: Any = NOT_GIVEN,
        max_completion_tokens: Any = NOT_GIVEN,
        presence_penalty: Any = NOT_GIVEN,
        frequency_penalty: Any = NOT_GIVEN,
        logit_bias: Any = NOT_GIVEN,
        logprobs: Any = NOT_GIVEN,
        top_logprobs: Any = NOT_GIVEN,
        user: Any = NOT_GIVEN,
        seed: Any = NOT_GIVEN,
        tools: Any = NOT_GIVEN,
        tool_choice: Any = NOT_GIVEN,
        response_format: Any = NOT_GIVEN,
        service_tier: Any = NOT_GIVEN,
        thinking: Any = NOT_GIVEN,
        reasoning_effort: Any = NOT_GIVEN,
        drop_params: Any = NOT_GIVEN,
        session_id: Any = NOT_GIVEN,
        trace_id: Any = NOT_GIVEN,
        request_metadata: Any = NOT_GIVEN,
        request_timeout: Any = NOT_GIVEN,
        cache_ttl: Any = NOT_GIVEN,
        cache_namespace: Any = NOT_GIVEN,
        cache_force_refresh: Any = NOT_GIVEN,
        cache_control: Any = NOT_GIVEN,
        guardrail_policy: Any = NOT_GIVEN,
        properties: dict[str, str] | None = None,
        user_id: str | None = None,
        request_id: str | None = None,
        extra_headers: dict[str, str] | None = None,
        extra_body: dict[str, Any] | None = None,
        timeout: Any = NOT_GIVEN,
        mock_response: str | None = None,
        **kwargs: Any,
    ) -> ChatCompletion | Any:
        # Check pre-call rules
        _check_pre_call_rules(self._client, model, messages, kwargs)

        if mock_response is not None:
            # Handle mock streaming
            if stream is True or (stream is not NOT_GIVEN and stream):
                from fi.gateway._streaming import MockStream, StreamManager

                return StreamManager(MockStream(_mock_stream_generator(model, mock_response)))

            from fi.gateway.types.chat.chat_completion import Choice
            from fi.gateway.types.chat.chat_completion_message import ChatCompletionMessage
            from fi.gateway.types.shared import Usage

            result = ChatCompletion(
                id="chatcmpl-mock",
                object="chat.completion",
                created=0,
                model=model,
                choices=[
                    Choice(
                        index=0,
                        message=ChatCompletionMessage(role="assistant", content=mock_response),
                        finish_reason="stop",
                    )
                ],
                usage=Usage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
            )

            if getattr(self._client, "_enable_json_schema_validation", False):
                _maybe_validate_json_schema(result, response_format)

            return result

        body, agentcc_params, extra_hdrs = _build_body_and_agentcc_params(
            model=model, messages=messages,
            temperature=temperature, top_p=top_p, n=n,
            stream=stream, stream_options=stream_options, stop=stop,
            max_tokens=max_tokens, max_completion_tokens=max_completion_tokens,
            presence_penalty=presence_penalty, frequency_penalty=frequency_penalty,
            logit_bias=logit_bias, logprobs=logprobs, top_logprobs=top_logprobs,
            user=user, seed=seed, tools=tools, tool_choice=tool_choice,
            response_format=response_format, service_tier=service_tier,
            thinking=thinking, reasoning_effort=reasoning_effort,
            drop_params=drop_params,
            session_id=session_id, trace_id=trace_id,
            request_metadata=request_metadata, request_timeout=request_timeout,
            cache_ttl=cache_ttl, cache_namespace=cache_namespace,
            cache_force_refresh=cache_force_refresh, cache_control=cache_control,
            guardrail_policy=guardrail_policy,
            properties=properties, user_id=user_id, request_id=request_id,
            extra_headers=extra_headers, extra_body=extra_body, timeout=timeout,
            **kwargs,
        )

        # Apply modify_params if enabled on the client
        if getattr(self._client, "_modify_params", False):
            from fi.gateway._param_modifier import modify_params_for_provider

            modify_params_for_provider(model, body)

        # Merge session headers if an active session is set on the client
        extra_hdrs = _merge_session_headers(self._client, extra_hdrs)

        from fi.gateway._utils import parse_timeout

        opts = RequestOptions(
            method="POST",
            url="/v1/chat/completions",
            body=body,
            headers=extra_hdrs,
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )

        if stream is True or (stream is not NOT_GIVEN and stream):
            from fi.gateway._streaming import AsyncStream
            response = await self._client._get_base_client()._stream_request(opts, agentcc_params)
            return AsyncStream(response)

        result = await self._client._get_base_client()._request_with_retry(opts, ChatCompletion, agentcc_params)

        # Auto-validate JSON schema if enabled
        if getattr(self._client, "_enable_json_schema_validation", False):
            _maybe_validate_json_schema(result, response_format)

        return result

    async def stream(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        temperature: Any = NOT_GIVEN,
        top_p: Any = NOT_GIVEN,
        n: Any = NOT_GIVEN,
        stream_options: Any = NOT_GIVEN,
        stop: Any = NOT_GIVEN,
        max_tokens: Any = NOT_GIVEN,
        max_completion_tokens: Any = NOT_GIVEN,
        presence_penalty: Any = NOT_GIVEN,
        frequency_penalty: Any = NOT_GIVEN,
        logit_bias: Any = NOT_GIVEN,
        logprobs: Any = NOT_GIVEN,
        top_logprobs: Any = NOT_GIVEN,
        user: Any = NOT_GIVEN,
        seed: Any = NOT_GIVEN,
        tools: Any = NOT_GIVEN,
        tool_choice: Any = NOT_GIVEN,
        response_format: Any = NOT_GIVEN,
        service_tier: Any = NOT_GIVEN,
        thinking: Any = NOT_GIVEN,
        reasoning_effort: Any = NOT_GIVEN,
        drop_params: Any = NOT_GIVEN,
        session_id: Any = NOT_GIVEN,
        trace_id: Any = NOT_GIVEN,
        request_metadata: Any = NOT_GIVEN,
        request_timeout: Any = NOT_GIVEN,
        cache_ttl: Any = NOT_GIVEN,
        cache_namespace: Any = NOT_GIVEN,
        cache_force_refresh: Any = NOT_GIVEN,
        cache_control: Any = NOT_GIVEN,
        guardrail_policy: Any = NOT_GIVEN,
        properties: dict[str, str] | None = None,
        user_id: str | None = None,
        request_id: str | None = None,
        extra_headers: dict[str, str] | None = None,
        extra_body: dict[str, Any] | None = None,
        timeout: Any = NOT_GIVEN,
        **kwargs: Any,
    ) -> Any:
        """Return an AsyncStreamManager context manager for consuming a streaming response.

        Usage::

            async with await client.chat.completions.stream(model="gpt-4o", messages=[...]) as stream:
                async for text in stream.text_stream():
                    print(text, end="")
                final = await stream.get_final_completion()
        """
        # Check pre-call rules
        _check_pre_call_rules(self._client, model, messages, kwargs)

        from fi.gateway._streaming import AsyncStream, AsyncStreamManager

        body, agentcc_params, extra_hdrs = _build_body_and_agentcc_params(
            model=model, messages=messages,
            stream=True, stream_options=stream_options,
            temperature=temperature, top_p=top_p, n=n, stop=stop,
            max_tokens=max_tokens, max_completion_tokens=max_completion_tokens,
            presence_penalty=presence_penalty, frequency_penalty=frequency_penalty,
            logit_bias=logit_bias, logprobs=logprobs, top_logprobs=top_logprobs,
            user=user, seed=seed, tools=tools, tool_choice=tool_choice,
            response_format=response_format, service_tier=service_tier,
            thinking=thinking, reasoning_effort=reasoning_effort,
            drop_params=drop_params,
            session_id=session_id, trace_id=trace_id,
            request_metadata=request_metadata, request_timeout=request_timeout,
            cache_ttl=cache_ttl, cache_namespace=cache_namespace,
            cache_force_refresh=cache_force_refresh, cache_control=cache_control,
            guardrail_policy=guardrail_policy,
            properties=properties, user_id=user_id, request_id=request_id,
            extra_headers=extra_headers, extra_body=extra_body, timeout=timeout,
            **kwargs,
        )

        # Apply modify_params if enabled on the client
        if getattr(self._client, "_modify_params", False):
            from fi.gateway._param_modifier import modify_params_for_provider

            modify_params_for_provider(model, body)

        # Merge session headers if an active session is set on the client
        extra_hdrs = _merge_session_headers(self._client, extra_hdrs)

        from fi.gateway._utils import parse_timeout
        opts = RequestOptions(
            method="POST",
            url="/v1/chat/completions",
            body=body,
            headers=extra_hdrs,
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        response = await self._client._get_base_client()._stream_request(opts, agentcc_params)
        return AsyncStreamManager(AsyncStream(response))
