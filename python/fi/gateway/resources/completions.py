"""Legacy text completions resource with full AgentCC gateway integration."""

from __future__ import annotations

from typing import Any

from fi.gateway._base_client import RequestOptions
from fi.gateway._constants import NOT_GIVEN
from fi.gateway._agentcc_params import build_extra_headers, collect_agentcc_params, merge_session_headers
from fi.gateway.types.completion import Completion


def _build_body(
    *,
    model: str,
    prompt: str | list[str],
    max_tokens: Any = NOT_GIVEN,
    temperature: Any = NOT_GIVEN,
    top_p: Any = NOT_GIVEN,
    n: Any = NOT_GIVEN,
    stream: Any = NOT_GIVEN,
    logprobs: Any = NOT_GIVEN,
    echo: Any = NOT_GIVEN,
    stop: Any = NOT_GIVEN,
    presence_penalty: Any = NOT_GIVEN,
    frequency_penalty: Any = NOT_GIVEN,
    best_of: Any = NOT_GIVEN,
    logit_bias: Any = NOT_GIVEN,
    user: Any = NOT_GIVEN,
    seed: Any = NOT_GIVEN,
    suffix: Any = NOT_GIVEN,
    extra_body: dict[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    body: dict[str, Any] = {"model": model, "prompt": prompt}
    for key, val in {
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "n": n,
        "stream": stream,
        "logprobs": logprobs,
        "echo": echo,
        "stop": stop,
        "presence_penalty": presence_penalty,
        "frequency_penalty": frequency_penalty,
        "best_of": best_of,
        "logit_bias": logit_bias,
        "user": user,
        "seed": seed,
        "suffix": suffix,
    }.items():
        if val is not NOT_GIVEN:
            body[key] = val
    if extra_body:
        body.update(extra_body)
    if kwargs:
        body.update(kwargs)
    return body


class Completions:
    """Sync legacy completions resource."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def create(
        self,
        *,
        model: str,
        prompt: str | list[str],
        max_tokens: Any = NOT_GIVEN,
        temperature: Any = NOT_GIVEN,
        top_p: Any = NOT_GIVEN,
        n: Any = NOT_GIVEN,
        stream: Any = NOT_GIVEN,
        logprobs: Any = NOT_GIVEN,
        echo: Any = NOT_GIVEN,
        stop: Any = NOT_GIVEN,
        presence_penalty: Any = NOT_GIVEN,
        frequency_penalty: Any = NOT_GIVEN,
        best_of: Any = NOT_GIVEN,
        logit_bias: Any = NOT_GIVEN,
        user: Any = NOT_GIVEN,
        seed: Any = NOT_GIVEN,
        suffix: Any = NOT_GIVEN,
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
    ) -> Completion | Any:
        body = _build_body(
            model=model, prompt=prompt,
            max_tokens=max_tokens, temperature=temperature, top_p=top_p,
            n=n, stream=stream, logprobs=logprobs, echo=echo, stop=stop,
            presence_penalty=presence_penalty, frequency_penalty=frequency_penalty,
            best_of=best_of, logit_bias=logit_bias, user=user, seed=seed,
            suffix=suffix, extra_body=extra_body, **kwargs,
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
            url="/v1/completions",
            body=body,
            headers=extra_hdrs,
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )

        if stream is True or (stream is not NOT_GIVEN and stream):
            from fi.gateway._streaming import Stream

            response = self._client._get_base_client()._stream_request(opts, agentcc_params)
            return Stream(response, Completion)  # text completions, not chat chunks

        return self._client._get_base_client()._request_with_retry(opts, Completion, agentcc_params)


class AsyncCompletions:
    """Async legacy completions resource."""

    def __init__(self, client: Any) -> None:
        self._client = client

    async def create(
        self,
        *,
        model: str,
        prompt: str | list[str],
        max_tokens: Any = NOT_GIVEN,
        temperature: Any = NOT_GIVEN,
        top_p: Any = NOT_GIVEN,
        n: Any = NOT_GIVEN,
        stream: Any = NOT_GIVEN,
        logprobs: Any = NOT_GIVEN,
        echo: Any = NOT_GIVEN,
        stop: Any = NOT_GIVEN,
        presence_penalty: Any = NOT_GIVEN,
        frequency_penalty: Any = NOT_GIVEN,
        best_of: Any = NOT_GIVEN,
        logit_bias: Any = NOT_GIVEN,
        user: Any = NOT_GIVEN,
        seed: Any = NOT_GIVEN,
        suffix: Any = NOT_GIVEN,
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
    ) -> Completion | Any:
        body = _build_body(
            model=model, prompt=prompt,
            max_tokens=max_tokens, temperature=temperature, top_p=top_p,
            n=n, stream=stream, logprobs=logprobs, echo=echo, stop=stop,
            presence_penalty=presence_penalty, frequency_penalty=frequency_penalty,
            best_of=best_of, logit_bias=logit_bias, user=user, seed=seed,
            suffix=suffix, extra_body=extra_body, **kwargs,
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
            url="/v1/completions",
            body=body,
            headers=extra_hdrs,
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )

        if stream is True or (stream is not NOT_GIVEN and stream):
            from fi.gateway._streaming import AsyncStream

            response = await self._client._get_base_client()._stream_request(opts, agentcc_params)
            return AsyncStream(response, Completion)

        return await self._client._get_base_client()._request_with_retry(opts, Completion, agentcc_params)
