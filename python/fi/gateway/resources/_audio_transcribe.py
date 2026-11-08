"""Audio transcriptions and translations (``/v1/audio/transcriptions``, ``/v1/audio/translations``).

Each upload is a multipart form (see ``_audio_upload``): the audio as the ``file`` part,
the other fields as form values, the gateway parameters as headers.
"""

from __future__ import annotations

from typing import Any

from fi.gateway._constants import NOT_GIVEN
from fi.gateway.resources._audio_upload import upload_request
from fi.gateway.types.audio import Transcription, Translation


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
        opts, agentcc_params = upload_request(
            self._client,
            "/v1/audio/transcriptions",
            file=file,
            model=model,
            fields={
                "language": language,
                "prompt": prompt,
                "response_format": response_format,
                "temperature": temperature,
                "timestamp_granularities": timestamp_granularities,
                **kwargs,
            },
            gateway={
                "session_id": session_id,
                "trace_id": trace_id,
                "request_metadata": request_metadata,
                "request_timeout": request_timeout,
                "cache_ttl": cache_ttl,
                "cache_namespace": cache_namespace,
                "cache_force_refresh": cache_force_refresh,
                "cache_control": cache_control,
                "guardrail_policy": guardrail_policy,
            },
            properties=properties,
            user_id=user_id,
            request_id=request_id,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        return self._client._get_base_client()._request_with_retry(
            opts, Transcription, agentcc_params
        )


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
        opts, agentcc_params = upload_request(
            self._client,
            "/v1/audio/transcriptions",
            file=file,
            model=model,
            fields={
                "language": language,
                "prompt": prompt,
                "response_format": response_format,
                "temperature": temperature,
                "timestamp_granularities": timestamp_granularities,
                **kwargs,
            },
            gateway={
                "session_id": session_id,
                "trace_id": trace_id,
                "request_metadata": request_metadata,
                "request_timeout": request_timeout,
                "cache_ttl": cache_ttl,
                "cache_namespace": cache_namespace,
                "cache_force_refresh": cache_force_refresh,
                "cache_control": cache_control,
                "guardrail_policy": guardrail_policy,
            },
            properties=properties,
            user_id=user_id,
            request_id=request_id,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        return await self._client._get_base_client()._request_with_retry(
            opts, Transcription, agentcc_params
        )


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
        opts, agentcc_params = upload_request(
            self._client,
            "/v1/audio/translations",
            file=file,
            model=model,
            fields={
                "prompt": prompt,
                "response_format": response_format,
                "temperature": temperature,
                **(extra_body or {}),
                **kwargs,
            },
            gateway={
                "session_id": session_id,
                "trace_id": trace_id,
                "request_metadata": request_metadata,
                "request_timeout": request_timeout,
                "cache_ttl": cache_ttl,
                "cache_namespace": cache_namespace,
                "cache_force_refresh": cache_force_refresh,
                "cache_control": cache_control,
                "guardrail_policy": guardrail_policy,
            },
            properties=properties,
            user_id=user_id,
            request_id=request_id,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        return self._client._get_base_client()._request_with_retry(
            opts, Translation, agentcc_params
        )


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
        opts, agentcc_params = upload_request(
            self._client,
            "/v1/audio/translations",
            file=file,
            model=model,
            fields={
                "prompt": prompt,
                "response_format": response_format,
                "temperature": temperature,
                **(extra_body or {}),
                **kwargs,
            },
            gateway={
                "session_id": session_id,
                "trace_id": trace_id,
                "request_metadata": request_metadata,
                "request_timeout": request_timeout,
                "cache_ttl": cache_ttl,
                "cache_namespace": cache_namespace,
                "cache_force_refresh": cache_force_refresh,
                "cache_control": cache_control,
                "guardrail_policy": guardrail_policy,
            },
            properties=properties,
            user_id=user_id,
            request_id=request_id,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        return await self._client._get_base_client()._request_with_retry(
            opts, Translation, agentcc_params
        )
