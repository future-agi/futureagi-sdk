"""Deprecated log-oriented callback adapter on the released lifecycle hooks."""

from __future__ import annotations

import time
from typing import Any

from fi.gateway._deprecation import deprecated
from fi.gateway.callbacks.base import CallbackHandler, CallbackRequest, CallbackResponse


@deprecated
class AgentCCLogger(CallbackHandler):
    """Subclass and override log_* methods to receive request lifecycle events.

    Request text is the callback-only snapshot, so redact_messages also applies
    here. Each request stores its own start time; concurrent calls do not share it.
    """

    def __init__(self) -> None:
        """Initialize the no-argument released callback adapter."""

    def on_request_start(self, request: CallbackRequest) -> None:
        setattr(request, "_logger_start_time", time.time())
        body = request.body or {}
        self.log_pre_call(body.get("model", ""), body.get("messages", []), body)

    def on_request_end(self, request: CallbackRequest, response: CallbackResponse) -> None:
        body = request.body or {}
        end = time.time()
        self.log_success(
            body.get("model", ""), body.get("messages", []), response,
            getattr(request, "_logger_start_time", end), end,
        )

    def on_error(self, request: CallbackRequest, error: Exception) -> None:
        body = request.body or {}
        end = time.time()
        self.log_failure(
            body.get("model", ""), body.get("messages", []), error,
            getattr(request, "_logger_start_time", end), end,
        )

    def log_pre_call(self, model: str, messages: list, kwargs: dict) -> None:
        """Override: called before API request."""

    def log_success(self, model: str, messages: list, response: Any, start_time: float, end_time: float) -> None:
        """Override: called on successful response."""

    def log_failure(self, model: str, messages: list, error: Exception, start_time: float, end_time: float) -> None:
        """Override: called on failed response."""

    async def async_log_success(self, model: str, messages: list, response: Any, start_time: float, end_time: float) -> None:
        """Released awaitable helper; the transport's lifecycle hooks are synchronous."""
        self.log_success(model, messages, response, start_time, end_time)

    async def async_log_failure(self, model: str, messages: list, error: Exception, start_time: float, end_time: float) -> None:
        """Released awaitable helper; the transport's lifecycle hooks are synchronous."""
        self.log_failure(model, messages, error, start_time, end_time)
