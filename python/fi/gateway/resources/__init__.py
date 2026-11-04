"""Resource classes — chat, completions, embeddings, moderations, rerank,
images, audio, files, batches, responses, feedback, models."""

from __future__ import annotations

from fi.gateway.resources.audio import (
    AsyncAudio,
    AsyncSpeech,
    AsyncTranscriptions,
    AsyncTranslations,
    Audio,
    Speech,
    Transcriptions,
    Translations,
)
from fi.gateway.resources.batches import AsyncBatches, Batches
from fi.gateway.resources.chat import AsyncChat, Chat
from fi.gateway.resources.completions import AsyncCompletions, Completions
from fi.gateway.resources.embeddings import AsyncEmbeddings, Embeddings
from fi.gateway.resources.files import AsyncFiles, Files
from fi.gateway.resources.images import AsyncImages, Images
from fi.gateway.resources.models import AsyncModels, Models
from fi.gateway.resources.moderations import AsyncModerations, Moderations
from fi.gateway.resources.rerank import AsyncRerank, Rerank
from fi.gateway.resources.responses import AsyncResponses, Responses

__all__ = [
    "AsyncAudio",
    "AsyncBatches",
    "AsyncChat",
    "AsyncCompletions",
    "AsyncEmbeddings",
    "AsyncFiles",
    "AsyncImages",
    "AsyncModels",
    "AsyncModerations",
    "AsyncRerank",
    "AsyncResponses",
    "AsyncSpeech",
    "AsyncTranscriptions",
    "AsyncTranslations",
    "Audio",
    "Batches",
    "Chat",
    "Completions",
    "Embeddings",
    "Files",
    "Images",
    "Models",
    "Moderations",
    "Rerank",
    "Responses",
    "Speech",
    "Transcriptions",
    "Translations",
]
