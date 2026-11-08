"""Request building shared by the sync and async chat completions resources."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from fi.gateway._agentcc_params import merge_session_headers
from fi.gateway._constants import NOT_GIVEN
from fi.gateway._transport._base import RequestOptions
from fi.gateway._streaming._manager import StreamManager as _StreamManager
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
    """Run the released blocking rules before mocks or network calls."""
    from fi.gateway._exceptions import AgentCCError

    for rule in getattr(client, "_pre_call_rules", None) or []:
        if not rule(model, messages, kwargs):
            name = getattr(rule, "__name__", type(rule).__name__)
            raise AgentCCError(f"Request blocked by pre-call rule: {name}")


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


def _wants_stream(stream: Any) -> bool:
    return stream is True or (stream is not NOT_GIVEN and bool(stream))


def _arguments(local_vars: dict[str, Any], **overrides: Any) -> dict[str, Any]:
    """A create()/stream() call's arguments for :func:`_build_body_and_agentcc_params`.

    Each method passes ``locals()`` as its first statement, so this is exactly its
    named parameters plus the free-form ``**kwargs`` (merged in, as 1.0 did).
    """
    args = {
        k: v
        for k, v in local_vars.items()
        if k not in {"self", "kwargs", "mock_response"}
    }
    args.update(local_vars.get("kwargs") or {})
    args.update(overrides)
    return args


def _prepare(
    client: Any, args: dict[str, Any]
) -> tuple[RequestOptions, dict[str, Any]]:
    """The POST /v1/chat/completions request and its AgentCC header params."""
    from fi.gateway._utils import parse_timeout

    body, agentcc_params, extra_hdrs = _build_body_and_agentcc_params(**args)
    if getattr(client, "_modify_params", False):
        from fi.gateway._param_modifier import modify_params_for_provider

        modify_params_for_provider(args["model"], body)
    # Merge session headers if an active session is set on the client
    extra_hdrs = merge_session_headers(client, extra_hdrs, agentcc_params, defer=True)
    timeout = args.get("timeout", NOT_GIVEN)
    opts = RequestOptions(
        method="POST",
        url="/v1/chat/completions",
        body=body,
        headers=extra_hdrs,
        timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
    )
    return opts, agentcc_params


def _mock_result(
    client: Any, model: str, mock_response: str, stream: Any, response_format: Any
) -> ChatCompletion | _StreamManager:
    """What ``create(mock_response=...)`` returns: a StreamManager or a ChatCompletion, no request."""
    if _wants_stream(stream):
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
    if getattr(client, "_enable_json_schema_validation", False):
        _maybe_validate_json_schema(result, response_format)
    return result
