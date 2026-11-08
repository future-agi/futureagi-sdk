"""Released callback contracts and redaction helpers.

Published request descriptors retain live caller-owned values. Snapshot requests
are detached and masked. CallbackResponse delegates to the original parsed model;
sent request headers are scrubbed by the transport. Handler errors are logged at
DEBUG and never replace SDK results.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from fi.gateway._constants import CREDENTIAL_HEADER_NAMES


@dataclass
class CallbackRequest:
    method: str
    url: str
    headers: dict[str, str]
    body: dict[str, Any] | None
    timeout: Any = None
    max_retries: int | None = None
    files: dict[str, Any] | None = field(default=None, repr=False)


@dataclass
class CallbackResponse:
    status_code: int
    headers: dict[str, str]
    agentcc: Any = None
    body: dict[str, Any] | None = None
    _parsed: Any = field(default=None, repr=False, compare=False)

    def __getattr__(self, name: str) -> Any:
        parsed = self.__dict__.get("_parsed")
        if parsed is None:
            raise AttributeError(name)
        return getattr(parsed, name)


@dataclass
class StreamInfo:
    agentcc: Any = None
    chunk_count: int = 0


class CallbackHandler:
    """Override any lifecycle hooks needed; all defaults are no-ops."""

    def on_request_start(self, request: CallbackRequest) -> None:
        """Before sending the request."""

    def on_request_end(self, request: CallbackRequest, response: CallbackResponse) -> None:
        """After a successful non-streaming response."""

    def on_stream_start(self, request: CallbackRequest, stream: StreamInfo) -> None:
        """After opening a streaming response."""

    def on_stream_chunk(self, request: CallbackRequest, chunk: Any) -> None:
        """For each consumed chunk."""

    def on_stream_end(self, request: CallbackRequest, stream: StreamInfo, completion: Any) -> None:
        """When a stream ends or is closed."""

    def on_error(self, request: CallbackRequest, error: Exception) -> None:
        """When a request fails permanently."""

    def on_retry(self, request: CallbackRequest, error: Exception, attempt: int, delay: float) -> None:
        """Before the next retry attempt."""

    def on_guardrail_warning(self, request: CallbackRequest, warning: Any) -> None:
        """For a guardrail warning (246)."""

    def on_guardrail_block(self, request: CallbackRequest, error: Any) -> None:
        """For a guardrail block (446)."""

    def on_cache_hit(self, request: CallbackRequest, response: CallbackResponse, cache_type: str) -> None:
        """For a cache hit reported by the gateway."""

    def on_cost_update(self, request: CallbackRequest, cost: float, cumulative_cost: float) -> None:
        """When a request reports a cost."""

    def on_budget_warning(self, request: CallbackRequest, current_spend: float, max_budget: float, percent_used: float) -> None:
        """For a configured budget warning."""

    def on_fallback(self, request: CallbackRequest, original_model: str, fallback_model: str, reason: str) -> None:
        """For a fallback reported by the gateway."""

    def on_session_start(self, session: Any) -> None:
        """When a session is entered."""

    def on_session_end(self, session: Any, total_cost: float, request_count: int, total_tokens: int) -> None:
        """When a session exits."""


REDACTED = "[REDACTED]"
_TEXT_KEYS = ("prompt", "input", "instructions")
_CREDENTIAL_KEYS = frozenset(name.replace("-", "_") for name in CREDENTIAL_HEADER_NAMES) | {
    "virtual_key", "secret_key", "fi_api_key", "fi_secret_key",
    "access_token", "refresh_token", "client_secret", "password",
}


def _redact_message(message: Any) -> Any:
    if not isinstance(message, dict):
        return message
    out = dict(message)
    if out.get("content") is not None:
        out["content"] = REDACTED
    if isinstance(out.get("tool_calls"), list):
        out["tool_calls"] = [
            {**call, "function": {**call["function"], "arguments": REDACTED}}
            if isinstance(call, dict) and isinstance(call.get("function"), dict)
            and call["function"].get("arguments") is not None else call
            for call in out["tool_calls"]
        ]
    if isinstance(out.get("function_call"), dict) and out["function_call"].get("arguments") is not None:
        out["function_call"] = {**out["function_call"], "arguments": REDACTED}
    return out


def redact_credentials(value: Any) -> Any:
    """Copy structured callback data without credential-bearing fields."""
    if isinstance(value, dict):
        return {
            key: REDACTED if str(key).lower().replace("-", "_") in _CREDENTIAL_KEYS
            else redact_credentials(item)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        items = tuple(redact_credentials(item) for item in value)
        if hasattr(value, "_fields"):
            return type(value)(*items)
        return type(value)(items)
    if isinstance(value, list):
        return type(value)(redact_credentials(item) for item in value)
    return value


def redact_body(body: Any) -> Any:
    """Copy a body without message text, tool arguments, prompt/input/instructions."""
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
    """One descriptor copy with exactly the published shallow message redaction."""
    return replace(request, body=redact_body(request.body))
