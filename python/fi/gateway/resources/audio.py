"""Audio resource: ``audio.transcriptions``, ``audio.speech`` and ``audio.translations``."""

from __future__ import annotations

from typing import Any

from fi.gateway._agentcc_params import (
    build_extra_headers as build_extra_headers,
    collect_agentcc_params as collect_agentcc_params,
    merge_session_headers as merge_session_headers,
)
from fi.gateway._constants import NOT_GIVEN as NOT_GIVEN
from fi.gateway._transport._base import RequestOptions as RequestOptions
from fi.gateway.resources._audio_speech import AsyncSpeech, Speech
from fi.gateway.resources._audio_transcribe import (
    AsyncTranscriptions,
    AsyncTranslations,
    Transcriptions,
    Translations,
)
from fi.gateway.types.audio import Transcription as Transcription, Translation as Translation

__all__ = [
    "NOT_GIVEN",
    "RequestOptions",
    "Transcription",
    "Translation",
    "build_extra_headers",
    "collect_agentcc_params",
    "merge_session_headers",
    "AsyncAudio",
    "AsyncSpeech",
    "AsyncTranscriptions",
    "AsyncTranslations",
    "Audio",
    "Speech",
    "Transcriptions",
    "Translations",
]


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
