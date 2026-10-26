"""Callback handler base class and data types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CallbackRequest:
    """Request info passed to callbacks."""
    method: str
    url: str
    headers: dict[str, str]
    body: dict[str, Any] | None


@dataclass
class CallbackResponse:
    """Response info passed to callbacks."""
    status_code: int
    headers: dict[str, str]
    agentcc: Any = None  # AgentCCMetadata
    body: dict[str, Any] | None = None


@dataclass
class StreamInfo:
    """Stream metadata passed to stream callbacks."""
    agentcc: Any = None  # AgentCCMetadata
    chunk_count: int = 0


class CallbackHandler:
    """Abstract base for callback handlers.

    Override any methods you need — all have no-op default implementations.
    """

    def on_request_start(self, request: CallbackRequest) -> None:
        """Called before a request is sent."""

    def on_request_end(self, request: CallbackRequest, response: CallbackResponse) -> None:
        """Called after a successful response."""

    def on_stream_start(self, request: CallbackRequest, stream: StreamInfo) -> None:
        """Called when a streaming response starts."""

    def on_stream_chunk(self, request: CallbackRequest, chunk: Any) -> None:
        """Called for each streaming chunk."""

    def on_stream_end(self, request: CallbackRequest, stream: StreamInfo, completion: Any) -> None:
        """Called when a streaming response ends."""

    def on_error(self, request: CallbackRequest, error: Exception) -> None:
        """Called when a request fails."""

    def on_retry(self, request: CallbackRequest, error: Exception, attempt: int, delay: float) -> None:
        """Called before a retry attempt."""

    def on_guardrail_warning(self, request: CallbackRequest, warning: Any) -> None:
        """Called when a guardrail warning (246) is raised."""

    def on_guardrail_block(self, request: CallbackRequest, error: Any) -> None:
        """Called when a guardrail block (446) is raised."""

    def on_cache_hit(self, request: CallbackRequest, response: CallbackResponse, cache_type: str) -> None:
        """Called when a cache hit is detected."""

    def on_cost_update(self, request: CallbackRequest, cost: float, cumulative_cost: float) -> None:
        """Called after every request when cost is tracked."""

    def on_budget_warning(self, request: CallbackRequest, current_spend: float, max_budget: float, percent_used: float) -> None:
        """Called when spend exceeds warning threshold (default 80%)."""

    def on_fallback(self, request: CallbackRequest, original_model: str, fallback_model: str, reason: str) -> None:
        """Called when a fallback provider/model is used."""

    def on_session_start(self, session: Any) -> None:
        """Called when a session context manager enters."""

    def on_session_end(self, session: Any, total_cost: float, request_count: int, total_tokens: int) -> None:
        """Called when a session context manager exits."""


def redact_callback_request(request: CallbackRequest) -> CallbackRequest:
    """Return a copy of *request* with message content replaced by ``[REDACTED]``.

    If the request body does not contain a ``messages`` key the original
    request is returned unchanged.
    """
    if request.body and isinstance(request.body, dict) and "messages" in request.body:
        redacted_body = dict(request.body)
        redacted_body["messages"] = [
            {**m, "content": "[REDACTED]"} if "content" in m else m
            for m in request.body["messages"]
        ]
        return CallbackRequest(
            method=request.method,
            url=request.url,
            headers=request.headers,
            body=redacted_body,
        )
    return request
