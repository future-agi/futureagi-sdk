"""AgentCC type definitions."""

from __future__ import annotations

from fi.gateway.types.agentcc_metadata import AgentCCMetadata, RateLimitInfo
from fi.gateway.types.audio import Transcription, Translation
from fi.gateway.types.batch import BatchResponse
from fi.gateway.types.completion import Completion, CompletionChoice
from fi.gateway.types.embedding import Embedding, EmbeddingResponse
from fi.gateway.types.files import FileDeleted, FileList, FileObject
from fi.gateway.types.gateway_config import HealthResponse
from fi.gateway.types.image import Image, ImageResponse
from fi.gateway.types.model import Model, ModelList
from fi.gateway.types.moderation import ModerationResponse, ModerationResult
from fi.gateway.types.rerank import RerankResponse, RerankResult
from fi.gateway.types.responses import (
    ContentPart,
    ResponseObject,
    ResponseOutput,
    ResponseStreamEvent,
    ResponseUsage,
)
from fi.gateway.types.shared import ErrorBody, ErrorResponse, Usage

__all__ = [
    "AgentCCMetadata",
    "BatchResponse",
    "Completion",
    "CompletionChoice",
    "ContentPart",
    "Embedding",
    "EmbeddingResponse",
    "ErrorBody",
    "ErrorResponse",
    "FileDeleted",
    "FileList",
    "FileObject",
    "HealthResponse",
    "Image",
    "ImageResponse",
    "Model",
    "ModelList",
    "ModerationResponse",
    "ModerationResult",
    "RateLimitInfo",
    "RerankResponse",
    "RerankResult",
    "ResponseObject",
    "ResponseOutput",
    "ResponseStreamEvent",
    "ResponseUsage",
    "Transcription",
    "Translation",
    "Usage",
]
