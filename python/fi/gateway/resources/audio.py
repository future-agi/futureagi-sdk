"""Audio resource — transcriptions, speech, and translations with full AgentCC integration."""

from __future__ import annotations

from typing import Any

from fi.gateway._agentcc_params import (
    build_extra_headers,
    collect_agentcc_params,
    merge_session_headers,
)
from fi.gateway._base_client import RequestOptions
from fi.gateway._constants import NOT_GIVEN
from fi.gateway.types.audio import Transcription, Translation

# ---------------------------------------------------------------------------
# Transcriptions
# ---------------------------------------------------------------------------


class Transcriptions:
    """Sync transcriptions resource."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def create(
        self,
        *,
        file: Any,
        model: str,
        language: Any = NOT_GIVEN,
        prompt: Any = NOT_GIVEN,
        response_format: Any = NOT_GIVEN,
        temperature: Any = NOT_GIVEN,
        timestamp_granularities: Any = NOT_GIVEN,
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
        timeout: Any = NOT_GIVEN,
        **kwargs: Any,
    ) -> Transcription:
        body: dict[str, Any] = {"model": model}
        for key, val in {
            "language": language,
            "prompt": prompt,
            "response_format": response_format,
            "temperature": temperature,
            "timestamp_granularities": timestamp_granularities,
        }.items():
            if val is not NOT_GIVEN:
                body[key] = val
        if kwargs:
            body.update(kwargs)

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
            url="/v1/audio/transcriptions",
            body=body,
            files={"file": file},
            headers=extra_hdrs,
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        return self._client._get_base_client()._request_with_retry(opts, Transcription, agentcc_params)


class AsyncTranscriptions:
    """Async transcriptions resource."""

    def __init__(self, client: Any) -> None:
        self._client = client

    async def create(
        self,
        *,
        file: Any,
        model: str,
        language: Any = NOT_GIVEN,
        prompt: Any = NOT_GIVEN,
        response_format: Any = NOT_GIVEN,
        temperature: Any = NOT_GIVEN,
        timestamp_granularities: Any = NOT_GIVEN,
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
        timeout: Any = NOT_GIVEN,
        **kwargs: Any,
    ) -> Transcription:
        body: dict[str, Any] = {"model": model}
        for key, val in {
            "language": language,
            "prompt": prompt,
            "response_format": response_format,
            "temperature": temperature,
            "timestamp_granularities": timestamp_granularities,
        }.items():
            if val is not NOT_GIVEN:
                body[key] = val
        if kwargs:
            body.update(kwargs)

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
            url="/v1/audio/transcriptions",
            body=body,
            files={"file": file},
            headers=extra_hdrs,
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        return await self._client._get_base_client()._request_with_retry(opts, Transcription, agentcc_params)


# ---------------------------------------------------------------------------
# Speech (TTS)
# ---------------------------------------------------------------------------


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
            session_id=session_id, trace_id=trace_id,
            request_metadata=request_metadata, request_timeout=request_timeout,
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
            url="/v1/audio/speech",
            body=body,
            headers=extra_hdrs,
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        return self._client._get_base_client()._request_raw_with_retry(opts, agentcc_params)


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
            session_id=session_id, trace_id=trace_id,
            request_metadata=request_metadata, request_timeout=request_timeout,
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
            url="/v1/audio/speech",
            body=body,
            headers=extra_hdrs,
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        return await self._client._get_base_client()._request_raw_with_retry(opts, agentcc_params)


# ---------------------------------------------------------------------------
# Translations
# ---------------------------------------------------------------------------


class Translations:
    """Sync translations resource."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def create(
        self,
        *,
        file: Any,
        model: str,
        prompt: Any = NOT_GIVEN,
        response_format: Any = NOT_GIVEN,
        temperature: Any = NOT_GIVEN,
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
    ) -> Translation:
        body: dict[str, Any] = {"model": model}
        for key, val in {
            "prompt": prompt,
            "response_format": response_format,
            "temperature": temperature,
        }.items():
            if val is not NOT_GIVEN:
                body[key] = val
        if extra_body:
            body.update(extra_body)
        if kwargs:
            body.update(kwargs)

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
            url="/v1/audio/translations",
            body=body,
            files={"file": file},
            headers=extra_hdrs,
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        return self._client._get_base_client()._request_with_retry(opts, Translation, agentcc_params)


class AsyncTranslations:
    """Async translations resource."""

    def __init__(self, client: Any) -> None:
        self._client = client

    async def create(
        self,
        *,
        file: Any,
        model: str,
        prompt: Any = NOT_GIVEN,
        response_format: Any = NOT_GIVEN,
        temperature: Any = NOT_GIVEN,
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
    ) -> Translation:
        body: dict[str, Any] = {"model": model}
        for key, val in {
            "prompt": prompt,
            "response_format": response_format,
            "temperature": temperature,
        }.items():
            if val is not NOT_GIVEN:
                body[key] = val
        if extra_body:
            body.update(extra_body)
        if kwargs:
            body.update(kwargs)

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
            url="/v1/audio/translations",
            body=body,
            files={"file": file},
            headers=extra_hdrs,
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        return await self._client._get_base_client()._request_with_retry(opts, Translation, agentcc_params)


# ---------------------------------------------------------------------------
# Audio (container with sub-resources)
# ---------------------------------------------------------------------------


class Audio:
    """Sync audio resource with sub-resources."""

    def __init__(self, client: Any) -> None:
        self._client = client
        self._transcriptions: Transcriptions | None = None
        self._speech: Speech | None = None
        self._translations: Translations | None = None

    @property
    def transcriptions(self) -> Transcriptions:
        if self._transcriptions is None:
            self._transcriptions = Transcriptions(self._client)
        return self._transcriptions

    @property
    def speech(self) -> Speech:
        if self._speech is None:
            self._speech = Speech(self._client)
        return self._speech

    @property
    def translations(self) -> Translations:
        if self._translations is None:
            self._translations = Translations(self._client)
        return self._translations


class AsyncAudio:
    """Async audio resource with sub-resources."""

    def __init__(self, client: Any) -> None:
        self._client = client
        self._transcriptions: AsyncTranscriptions | None = None
        self._speech: AsyncSpeech | None = None
        self._translations: AsyncTranslations | None = None

    @property
    def transcriptions(self) -> AsyncTranscriptions:
        if self._transcriptions is None:
            self._transcriptions = AsyncTranscriptions(self._client)
        return self._transcriptions

    @property
    def speech(self) -> AsyncSpeech:
        if self._speech is None:
            self._speech = AsyncSpeech(self._client)
        return self._speech

    @property
    def translations(self) -> AsyncTranslations:
        if self._translations is None:
            self._translations = AsyncTranslations(self._client)
        return self._translations
