"""Custom logger base class bridging event callbacks and a log-oriented interface."""

from __future__ import annotations

from typing import Any

from fi.gateway.callbacks.base import CallbackHandler


class AgentCCLogger(CallbackHandler):
    """Abstract base for custom loggers with pre/post hooks.

    This bridges the gap between the event-based :class:`CallbackHandler` and a
    simpler log-oriented interface.  Subclass this and override the ``log_*``
    methods to plug in custom logging backends.
    """

    def log_pre_call(self, model: str, messages: list, kwargs: dict) -> None:        """Override: called before API request."""

    def log_success(self, model: str, messages: list, response: Any, start_time: float, end_time: float) -> None:        """Override: called on successful response."""

    def log_failure(self, model: str, messages: list, error: Exception, start_time: float, end_time: float) -> None:        """Override: called on failed response."""

    async def async_log_success(self, model: str, messages: list, response: Any, start_time: float, end_time: float) -> None:
        """Override: async version of log_success."""
        self.log_success(model, messages, response, start_time, end_time)

    async def async_log_failure(self, model: str, messages: list, error: Exception, start_time: float, end_time: float) -> None:
        """Override: async version of log_failure."""
        self.log_failure(model, messages, error, start_time, end_time)
