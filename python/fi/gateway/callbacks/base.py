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


REDACTED = "[REDACTED]"

# Body keys other than `messages` that carry user or model text.
_TEXT_KEYS = ("prompt", "input", "instructions")


def _redact_message(message: Any) -> Any:
    """One chat message with its text removed: the content, and the arguments of any tool
    call (the model writes user data into those too)."""
    if not isinstance(message, dict):
        return message
    out = dict(message)
    if out.get("content") is not None:
        out["content"] = REDACTED
    if isinstance(out.get("tool_calls"), list):
        out["tool_calls"] = [
            {**call, "function": {**call["function"], "arguments": REDACTED}}
            if isinstance(call, dict) and isinstance(call.get("function"), dict) and call["function"].get("arguments") is not None
            else call
            for call in out["tool_calls"]
        ]
    if isinstance(out.get("function_call"), dict) and out["function_call"].get("arguments") is not None:
        out["function_call"] = {**out["function_call"], "arguments": REDACTED}
    return out


def redact_body(body: Any) -> Any:
    """A copy of a request body with every message text replaced by ``[REDACTED]``: chat
    message content and tool-call arguments, and the `prompt` / `input` / `instructions`
    of the other endpoints. Anything else (model, parameters, tool schemas) is kept."""
    if not isinstance(body, dict):
        return body
    out = dict(body)
    if isinstance(out.get("messages"), list):
        out["messages"] = [_redact_message(m) for m in out["messages"]]
    for key in _TEXT_KEYS:
        if out.get(key) is not None:
            out[key] = REDACTED
    return out


def redact_callback_request(request: CallbackRequest) -> CallbackRequest:
    """Return a copy of *request* with message content replaced by ``[REDACTED]``
    (see `redact_body`). A request without a dict body is returned unchanged."""
    if not isinstance(request.body, dict):
        return request
    body = redact_body(request.body)
    if body == request.body:
        return request  # nothing to redact: the same object, as before
    return CallbackRequest(method=request.method, url=request.url, headers=request.headers, body=body)
