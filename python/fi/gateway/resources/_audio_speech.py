"""Audio speech, text to speech (``/v1/audio/speech``).

The gateway parameters go to the transport like every other resource's, so the
request's ``request_metadata`` is merged over the client's ``metadata=`` (and an active
session's) by the one metadata rule. agentcc 1.x wrote them as extra headers here, so
outside a session ``request_metadata`` replaced the client's metadata for speech only.
"""

from __future__ import annotations

from typing import Any

from fi.gateway._agentcc_params import (
    build_extra_headers,
    collect_agentcc_params,
    merge_session_headers,
)
from fi.gateway._constants import NOT_GIVEN
from fi.gateway._transport._base import RequestOptions


class Speech:
    """Sync speech (TTS) resource."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def create(
        self,
        *,
        model: str,
        input: str,
        voice: str,
        response_format: str = "mp3",
        speed: float = 1.0,
        # AgentCC-specific params
        session_id: Any = NOT_GIVEN,
        trace_id: Any = NOT_GIVEN,
        request_metadata: Any = NOT_GIVEN,
        request_timeout: Any = NOT_GIVEN,
        guardrail_policy: Any = NOT_GIVEN,
        properties: dict[str, str] | None = None,
        user_id: str | None = None,
        request_id: str | None = None,
        extra_headers: dict[str, str] | None = None,
        extra_body: dict[str, Any] | None = None,
        timeout: Any = NOT_GIVEN,
    ) -> bytes:
        body: dict[str, Any] = {
            "model": model,
            "input": input,
            "voice": voice,
        }
        if response_format != "mp3":
            body["response_format"] = response_format
        if speed != 1.0:
            body["speed"] = speed
        if extra_body:
            body.update(extra_body)

        agentcc_params = collect_agentcc_params(
            session_id=session_id,
            trace_id=trace_id,
            request_metadata=request_metadata,
            request_timeout=request_timeout,
            guardrail_policy=guardrail_policy,
        )

        extra_hdrs = build_extra_headers(
            extra_headers=extra_headers,
            properties=properties,
            user_id=user_id,
            request_id=request_id,
        )
        extra_hdrs = merge_session_headers(self._client, extra_hdrs, agentcc_params)

        from fi.gateway._utils import parse_timeout

        opts = RequestOptions(
            method="POST",
            url="/v1/audio/speech",
            body=body,
            headers=extra_hdrs,
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        return self._client._get_base_client()._request_raw_with_retry(
            opts, agentcc_params
        )


class AsyncSpeech:
    """Async speech (TTS) resource."""

    def __init__(self, client: Any) -> None:
        self._client = client

    async def create(
        self,
        *,
        model: str,
        input: str,
        voice: str,
        response_format: str = "mp3",
        speed: float = 1.0,
        # AgentCC-specific params
        session_id: Any = NOT_GIVEN,
        trace_id: Any = NOT_GIVEN,
        request_metadata: Any = NOT_GIVEN,
        request_timeout: Any = NOT_GIVEN,
        guardrail_policy: Any = NOT_GIVEN,
        properties: dict[str, str] | None = None,
        user_id: str | None = None,
        request_id: str | None = None,
        extra_headers: dict[str, str] | None = None,
        extra_body: dict[str, Any] | None = None,
        timeout: Any = NOT_GIVEN,
    ) -> bytes:
        body: dict[str, Any] = {
            "model": model,
            "input": input,
            "voice": voice,
        }
        if response_format != "mp3":
            body["response_format"] = response_format
        if speed != 1.0:
            body["speed"] = speed
        if extra_body:
            body.update(extra_body)

        agentcc_params = collect_agentcc_params(
            session_id=session_id,
            trace_id=trace_id,
            request_metadata=request_metadata,
            request_timeout=request_timeout,
            guardrail_policy=guardrail_policy,
        )

        extra_hdrs = build_extra_headers(
            extra_headers=extra_headers,
            properties=properties,
            user_id=user_id,
            request_id=request_id,
        )
        extra_hdrs = merge_session_headers(self._client, extra_hdrs, agentcc_params)

        from fi.gateway._utils import parse_timeout

        opts = RequestOptions(
            method="POST",
            url="/v1/audio/speech",
            body=body,
            headers=extra_hdrs,
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        return await self._client._get_base_client()._request_raw_with_retry(
            opts, agentcc_params
        )
