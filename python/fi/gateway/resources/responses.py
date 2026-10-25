"""Responses resource — OpenAI next-gen /v1/responses endpoint with full AgentCC integration."""

from __future__ import annotations

from typing import Any

from fi.gateway._agentcc_params import (
    build_extra_headers,
    collect_agentcc_params,
    merge_session_headers,
)
from fi.gateway._base_client import RequestOptions
from fi.gateway._constants import NOT_GIVEN
from fi.gateway.types.responses import ResponseObject


def _build_response_body(
    *,
    model: str,
    input: str | list[dict[str, Any]],
    instructions: Any = NOT_GIVEN,
    tools: Any = NOT_GIVEN,
    tool_choice: Any = NOT_GIVEN,
    temperature: Any = NOT_GIVEN,
    top_p: Any = NOT_GIVEN,
    max_output_tokens: Any = NOT_GIVEN,
    previous_response_id: Any = NOT_GIVEN,
    store: bool = True,
    metadata: Any = NOT_GIVEN,
    stream: bool = False,
    extra_body: dict[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    body: dict[str, Any] = {"model": model, "input": input}
    for key, val in {
        "instructions": instructions,
        "tools": tools,
        "tool_choice": tool_choice,
        "temperature": temperature,
        "top_p": top_p,
        "max_output_tokens": max_output_tokens,
        "previous_response_id": previous_response_id,
        "metadata": metadata,
    }.items():
        if val is not NOT_GIVEN:
            body[key] = val
    body["store"] = store
    if stream:
        body["stream"] = True
    if extra_body:
        body.update(extra_body)
    if kwargs:
        body.update(kwargs)
    return body


class Responses:
    """Sync responses resource."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def create(
        self,
        *,
        model: str,
        input: str | list[dict[str, Any]],
        instructions: Any = NOT_GIVEN,
        tools: Any = NOT_GIVEN,
        tool_choice: Any = NOT_GIVEN,
        temperature: Any = NOT_GIVEN,
        top_p: Any = NOT_GIVEN,
        max_output_tokens: Any = NOT_GIVEN,
        previous_response_id: Any = NOT_GIVEN,
        store: bool = True,
        metadata: Any = NOT_GIVEN,
        stream: bool = False,
        # AgentCC-specific params
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
    ) -> ResponseObject | Any:
        body = _build_response_body(
            model=model, input=input, instructions=instructions,
            tools=tools, tool_choice=tool_choice, temperature=temperature,
            top_p=top_p, max_output_tokens=max_output_tokens,
            previous_response_id=previous_response_id, store=store,
            metadata=metadata, stream=stream, extra_body=extra_body, **kwargs,
        )

        agentcc_params = collect_agentcc_params(
            session_id=session_id, trace_id=trace_id,
            request_metadata=request_metadata, request_timeout=request_timeout,
            cache_ttl=cache_ttl, cache_namespace=cache_namespace,
            cache_force_refresh=cache_force_refresh, cache_control=cache_control,
            guardrail_policy=guardrail_policy,
        )

        extra_hdrs = build_extra_headers(
            extra_headers=extra_headers, properties=properties,
            user_id=user_id, request_id=request_id,
        )
        extra_hdrs = merge_session_headers(self._client, extra_hdrs)

        from fi.gateway._utils import parse_timeout

        opts = RequestOptions(
            method="POST",
            url="/v1/responses",
            body=body,
            headers=extra_hdrs,
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )

        if stream:
            from fi.gateway._streaming import Stream

            response = self._client._get_base_client()._stream_request(opts, agentcc_params)
            return Stream(response)

        return self._client._get_base_client()._request_with_retry(opts, ResponseObject, agentcc_params)

    def retrieve(
        self,
        response_id: str,
        *,
        extra_headers: dict[str, str] | None = None,
        timeout: Any = NOT_GIVEN,
    ) -> ResponseObject:
        from fi.gateway._utils import parse_timeout

        opts = RequestOptions(
            method="GET",
            url=f"/v1/responses/{response_id}",
            headers=extra_headers or {},
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        return self._client._get_base_client()._request_with_retry(opts, ResponseObject)

    def delete(
        self,
        response_id: str,
        *,
        extra_headers: dict[str, str] | None = None,
        timeout: Any = NOT_GIVEN,
    ) -> None:
        from fi.gateway._utils import parse_timeout

        opts = RequestOptions(
            method="DELETE",
            url=f"/v1/responses/{response_id}",
            headers=extra_headers or {},
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        self._client._get_base_client()._request_raw_with_retry(opts)


class AsyncResponses:
    """Async responses resource."""

    def __init__(self, client: Any) -> None:
        self._client = client

    async def create(
        self,
        *,
        model: str,
        input: str | list[dict[str, Any]],
        instructions: Any = NOT_GIVEN,
        tools: Any = NOT_GIVEN,
        tool_choice: Any = NOT_GIVEN,
        temperature: Any = NOT_GIVEN,
        top_p: Any = NOT_GIVEN,
        max_output_tokens: Any = NOT_GIVEN,
        previous_response_id: Any = NOT_GIVEN,
        store: bool = True,
        metadata: Any = NOT_GIVEN,
        stream: bool = False,
        # AgentCC-specific params
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
    ) -> ResponseObject | Any:
        body = _build_response_body(
            model=model, input=input, instructions=instructions,
            tools=tools, tool_choice=tool_choice, temperature=temperature,
            top_p=top_p, max_output_tokens=max_output_tokens,
            previous_response_id=previous_response_id, store=store,
            metadata=metadata, stream=stream, extra_body=extra_body, **kwargs,
        )

        agentcc_params = collect_agentcc_params(
            session_id=session_id, trace_id=trace_id,
            request_metadata=request_metadata, request_timeout=request_timeout,
            cache_ttl=cache_ttl, cache_namespace=cache_namespace,
            cache_force_refresh=cache_force_refresh, cache_control=cache_control,
            guardrail_policy=guardrail_policy,
        )

        extra_hdrs = build_extra_headers(
            extra_headers=extra_headers, properties=properties,
            user_id=user_id, request_id=request_id,
        )
        extra_hdrs = merge_session_headers(self._client, extra_hdrs)

        from fi.gateway._utils import parse_timeout

        opts = RequestOptions(
            method="POST",
            url="/v1/responses",
            body=body,
            headers=extra_hdrs,
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )

        if stream:
            from fi.gateway._streaming import AsyncStream

            response = await self._client._get_base_client()._stream_request(opts, agentcc_params)
            return AsyncStream(response)

        return await self._client._get_base_client()._request_with_retry(opts, ResponseObject, agentcc_params)

    async def retrieve(
        self,
        response_id: str,
        *,
        extra_headers: dict[str, str] | None = None,
        timeout: Any = NOT_GIVEN,
    ) -> ResponseObject:
        from fi.gateway._utils import parse_timeout

        opts = RequestOptions(
            method="GET",
            url=f"/v1/responses/{response_id}",
            headers=extra_headers or {},
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        return await self._client._get_base_client()._request_with_retry(opts, ResponseObject)

    async def delete(
        self,
        response_id: str,
        *,
        extra_headers: dict[str, str] | None = None,
        timeout: Any = NOT_GIVEN,
    ) -> None:
        from fi.gateway._utils import parse_timeout

        opts = RequestOptions(
            method="DELETE",
            url=f"/v1/responses/{response_id}",
            headers=extra_headers or {},
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        await self._client._get_base_client()._request_raw_with_retry(opts)
