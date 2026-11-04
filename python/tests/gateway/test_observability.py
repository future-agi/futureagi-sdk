"""Tests for observability and callback improvements."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any
from unittest.mock import MagicMock

from fi.gateway.callbacks import (
    CallbackHandler,
    CallbackRequest,
    CallbackResponse,
    JSONLoggingCallbackHandler,
    AgentCCLogger,
    StreamInfo,
    redact_callback_request,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request(
    body: dict[str, Any] | None = None,
) -> CallbackRequest:
    return CallbackRequest(
        method="POST",
        url="/v1/chat/completions",
        headers={"Authorization": "Bearer sk-test"},
        body=body,
    )


def _make_response(
    status: int = 200,
    latency: int = 100,
    cost: float | None = 0.005,
    cache_hit: bool = False,
    body: dict[str, Any] | None = None,
) -> CallbackResponse:
    meta = MagicMock()
    meta.latency_ms = latency
    meta.cost = cost
    meta.cache_hit = cache_hit
    if body is None:
        body = {
            "model": "gpt-4o",
            "usage": {"prompt_tokens": 10, "completion_tokens": 20},
        }
    return CallbackResponse(status_code=status, headers={}, agentcc=meta, body=body)


# ===========================================================================
# CallbackHandler new hooks
# ===========================================================================


class TestCallbackHandlerNewHooks:
    """Verify the five new no-op hooks exist on CallbackHandler."""

    def test_callback_handler_has_on_cost_update(self) -> None:
        assert hasattr(CallbackHandler, "on_cost_update")

    def test_callback_handler_has_on_budget_warning(self) -> None:
        assert hasattr(CallbackHandler, "on_budget_warning")

    def test_callback_handler_has_on_fallback(self) -> None:
        assert hasattr(CallbackHandler, "on_fallback")

    def test_callback_handler_has_on_session_start(self) -> None:
        assert hasattr(CallbackHandler, "on_session_start")

    def test_callback_handler_has_on_session_end(self) -> None:
        assert hasattr(CallbackHandler, "on_session_end")

    def test_new_hooks_are_noop(self) -> None:
        """Calling every new hook on the base class must not raise."""
        handler = CallbackHandler()
        req = _make_request()
        # on_cost_update
        handler.on_cost_update(req, cost=0.01, cumulative_cost=0.05)
        # on_budget_warning
        handler.on_budget_warning(req, current_spend=8.0, max_budget=10.0, percent_used=80.0)
        # on_fallback
        handler.on_fallback(req, original_model="gpt-4o", fallback_model="gpt-3.5-turbo", reason="rate_limit")
        # on_session_start
        handler.on_session_start(session=None)
        # on_session_end
        handler.on_session_end(session=None, total_cost=1.23, request_count=5, total_tokens=500)


# ===========================================================================
# JSONLoggingCallbackHandler
# ===========================================================================


class TestJSONLoggingCallbackHandler:
    """Tests for the structured JSON logging callback."""

    def test_json_logger_request_end(self, tmp_path: Any) -> None:
        log_file = str(tmp_path / "agentcc.jsonl")
        logger = JSONLoggingCallbackHandler(file_path=log_file)
        req = _make_request()
        resp = _make_response()
        logger.on_request_end(req, resp)

        with open(log_file) as f:
            entry = json.loads(f.readline())
        assert entry["event"] == "request_complete"
        assert entry["method"] == "POST"
        assert entry["url"] == "/v1/chat/completions"
        assert entry["status_code"] == 200
        assert entry["model"] == "gpt-4o"
        assert entry["tokens"]["prompt"] == 10
        assert entry["tokens"]["completion"] == 20

    def test_json_logger_error(self, tmp_path: Any) -> None:
        log_file = str(tmp_path / "agentcc.jsonl")
        logger = JSONLoggingCallbackHandler(file_path=log_file)
        req = _make_request()
        logger.on_error(req, RuntimeError("boom"))

        with open(log_file) as f:
            entry = json.loads(f.readline())
        assert entry["event"] == "request_error"
        assert entry["error_type"] == "RuntimeError"
        assert entry["error_message"] == "boom"

    def test_json_logger_stream_end(self, tmp_path: Any) -> None:
        log_file = str(tmp_path / "agentcc.jsonl")
        logger = JSONLoggingCallbackHandler(file_path=log_file)
        req = _make_request()
        stream = StreamInfo(chunk_count=42)
        logger.on_stream_end(req, stream, completion=None)

        with open(log_file) as f:
            entry = json.loads(f.readline())
        assert entry["event"] == "stream_complete"
        assert entry["chunk_count"] == 42

    def test_json_logger_stdout_mode(self, caplog: Any) -> None:
        """When file_path is None, logs go to the Python logger."""
        logger = JSONLoggingCallbackHandler(file_path=None, log_level="INFO")
        req = _make_request()
        resp = _make_response()

        agentcc_logger = logging.getLogger("agentcc.json_logger")
        agentcc_logger.setLevel(logging.DEBUG)
        with caplog.at_level(logging.INFO, logger="agentcc.json_logger"):
            logger.on_request_end(req, resp)
        # Verify something was logged
        assert len(caplog.records) >= 1
        parsed = json.loads(caplog.records[-1].message)
        assert parsed["event"] == "request_complete"

    def test_json_logger_timestamps_present(self, tmp_path: Any) -> None:
        log_file = str(tmp_path / "agentcc.jsonl")
        logger = JSONLoggingCallbackHandler(file_path=log_file)
        req = _make_request()
        resp = _make_response()
        logger.on_request_end(req, resp)
        logger.on_error(req, ValueError("err"))

        with open(log_file) as f:
            lines = f.readlines()
        for line in lines:
            entry = json.loads(line)
            assert "timestamp" in entry
            assert entry["timestamp"].endswith("Z")


# ===========================================================================
# AgentCCLogger
# ===========================================================================


class TestAgentCCLogger:
    """Tests for the AgentCCLogger abstract base."""

    def test_agentcc_logger_has_log_methods(self) -> None:
        logger = AgentCCLogger()
        assert callable(getattr(logger, "log_pre_call", None))
        assert callable(getattr(logger, "log_success", None))
        assert callable(getattr(logger, "log_failure", None))
        assert callable(getattr(logger, "async_log_success", None))
        assert callable(getattr(logger, "async_log_failure", None))

    def test_agentcc_logger_subclass(self) -> None:
        """Create a custom subclass, verify hooks get called."""
        calls: list[str] = []

        class MyLogger(AgentCCLogger):
            def log_pre_call(self, model: str, messages: list, kwargs: dict) -> None:
                calls.append("pre_call")

            def log_success(self, model: str, messages: list, response: Any, start_time: float, end_time: float) -> None:
                calls.append("success")

            def log_failure(self, model: str, messages: list, error: Exception, start_time: float, end_time: float) -> None:
                calls.append("failure")

        logger = MyLogger()
        logger.log_pre_call("gpt-4o", [{"role": "user", "content": "hi"}], {})
        logger.log_success("gpt-4o", [], None, 0.0, 1.0)
        logger.log_failure("gpt-4o", [], RuntimeError("x"), 0.0, 1.0)

        assert calls == ["pre_call", "success", "failure"]

    def test_agentcc_logger_is_callback_handler(self) -> None:
        logger = AgentCCLogger()
        assert isinstance(logger, CallbackHandler)

    def test_agentcc_logger_async_defaults_call_sync(self) -> None:
        """async_log_success / async_log_failure default to sync versions."""
        calls: list[str] = []

        class MyLogger(AgentCCLogger):
            def log_success(self, model: str, messages: list, response: Any, start_time: float, end_time: float) -> None:
                calls.append("sync_success")

            def log_failure(self, model: str, messages: list, error: Exception, start_time: float, end_time: float) -> None:
                calls.append("sync_failure")

        logger = MyLogger()
        asyncio.run(logger.async_log_success("gpt-4o", [], None, 0.0, 1.0))
        asyncio.run(logger.async_log_failure("gpt-4o", [], RuntimeError("x"), 0.0, 1.0))
        assert calls == ["sync_success", "sync_failure"]


# ===========================================================================
# Content redaction
# ===========================================================================


class TestContentRedaction:
    """Tests for redact_callback_request."""

    def test_redact_callback_request_with_messages(self) -> None:
        req = _make_request(body={
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is 2+2?"},
            ],
        })
        redacted = redact_callback_request(req)
        assert redacted is not req  # new instance
        for msg in redacted.body["messages"]:  # type: ignore[index]
            assert msg["content"] == "[REDACTED]"

    def test_redact_callback_request_no_messages(self) -> None:
        req = _make_request(body={"model": "gpt-4o"})
        result = redact_callback_request(req)
        # No messages key -- returned as-is
        assert result is req

    def test_redact_callback_request_preserves_other_fields(self) -> None:
        req = _make_request(body={
            "model": "gpt-4o",
            "temperature": 0.7,
            "messages": [
                {"role": "user", "content": "secret"},
            ],
        })
        redacted = redact_callback_request(req)
        assert redacted.body["temperature"] == 0.7  # type: ignore[index]
        assert redacted.body["model"] == "gpt-4o"  # type: ignore[index]
        assert redacted.method == "POST"
        assert redacted.url == "/v1/chat/completions"
        assert redacted.headers == {"Authorization": "Bearer sk-test"}

    def test_redact_callback_request_empty_body(self) -> None:
        req = _make_request(body=None)
        result = redact_callback_request(req)
        assert result is req

    def test_redact_callback_request_message_without_content(self) -> None:
        """Messages without a 'content' key are left untouched."""
        req = _make_request(body={
            "model": "gpt-4o",
            "messages": [
                {"role": "tool", "tool_call_id": "abc"},
                {"role": "user", "content": "hi"},
            ],
        })
        redacted = redact_callback_request(req)
        msgs = redacted.body["messages"]  # type: ignore[index]
        # tool message has no content key -- unchanged
        assert "content" not in msgs[0]
        assert msgs[0]["tool_call_id"] == "abc"
        # user message was redacted
        assert msgs[1]["content"] == "[REDACTED]"


# ===========================================================================
# Lazy import tests
# ===========================================================================


class TestLazyImports:
    """Verify the new classes are importable from the top-level agentcc package."""

    def test_json_logging_handler_importable(self) -> None:
        import fi.gateway as agentcc

        cls = agentcc.JSONLoggingCallbackHandler
        assert cls is JSONLoggingCallbackHandler

    def test_agentcc_logger_importable(self) -> None:
        import fi.gateway as agentcc

        cls = agentcc.AgentCCLogger
        assert cls is AgentCCLogger
