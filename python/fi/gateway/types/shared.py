"""Shared type definitions used across the AgentCC SDK."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Usage(BaseModel):
    """Token usage information from a completion response."""

    model_config = ConfigDict(extra="allow")

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_tokens_details: dict[str, object] | None = None
    completion_tokens_details: dict[str, object] | None = None


class ErrorBody(BaseModel):
    """Parsed error object from the gateway's JSON error response."""

    message: str
    type: str | None = None
    code: str | None = None
    param: str | None = None


class ErrorResponse(BaseModel):
    """Top-level error response: ``{"error": {...}}``."""

    error: ErrorBody
