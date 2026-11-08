"""Tests for the callback system (ported from agentcc 1.0; the hooks get what the client passes).

agentcc 1.0's tests built ``CallbackRequest`` / ``CallbackResponse`` objects by hand, which
the client never passes; here the hooks get the request descriptor (``RequestOptions``)
and the returned value, as ``AgentCC(callbacks=[...])`` calls them. The tests of the
never-firing hooks and of those two dataclasses stay with the agentcc 2.0 compatibility
package (port manifest). test_callbacks_effect.py drives the same callbacks through a
real client.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import Any

import pytest

from fi.gateway.callbacks import (CallbackHandler, LoggingCallback,
                                  MetricsCallback, RequestOptions)


class _RecordingCallback(CallbackHandler):
    """Test callback that records all calls."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple]] = []

    def on_request_start(self, request: RequestOptions) -> None:
        self.calls.append(("on_request_start", (request,)))

    def on_request_end(self, request: RequestOptions, response: Any) -> None:
        self.calls.append(("on_request_end", (request, response)))

    def on_error(self, request: RequestOptions, error: Exception) -> None:
        self.calls.append(("on_error", (request, error)))

    def on_retry(
        self, request: RequestOptions, error: Exception, attempt: int, delay: float
    ) -> None:
        self.calls.append(("on_retry", (request, error, attempt, delay)))


def _make_request() -> RequestOptions:
    return RequestOptions(method="POST", url="/v1/chat/completions")


def _make_response(
    latency: int = 100,
    cost: float | None = 0.005,
    status: int = 200,
    total_tokens: int | None = 30,
) -> SimpleNamespace:
    """What a non-streaming call returns, as far as the callbacks read it."""
    meta = SimpleNamespace(
        provider="openai",
        latency_ms=latency,
        cost=cost,
        http_response=SimpleNamespace(status_code=status),
    )
    usage = None if total_tokens is None else SimpleNamespace(total_tokens=total_tokens)
    return SimpleNamespace(agentcc=meta, usage=usage)


# --- Base handler tests ---


def test_default_handler_methods_are_noop() -> None:
    """All default methods should execute without error."""
    handler = CallbackHandler()
    req = _make_request()
    resp = _make_response()
    handler.on_request_start(req)
    handler.on_request_end(req, resp)
    handler.on_error(req, Exception("test"))
    handler.on_retry(req, Exception("test"), 1, 0.5)


def test_the_base_declares_only_the_four_hooks_the_client_fires() -> None:
    hooks = sorted(n for n in vars(CallbackHandler) if n.startswith("on_"))
    assert hooks == ["on_error", "on_request_end", "on_request_start", "on_retry"]


def test_the_request_descriptor_is_public() -> None:
    """A handler can name the type its hooks receive without a private import."""
    import inspect

    from fi.gateway._transport._base import RequestOptions as Private

    assert RequestOptions is Private
    hints = inspect.get_annotations(CallbackHandler.on_request_start)
    assert hints["request"] == "RequestOptions"


def test_custom_callback_records_calls() -> None:
    cb = _RecordingCallback()
    req = _make_request()
    resp = _make_response()
    cb.on_request_start(req)
    cb.on_request_end(req, resp)
    assert len(cb.calls) == 2
    assert cb.calls[0][0] == "on_request_start"
    assert cb.calls[1][0] == "on_request_end"


def test_callback_exception_does_not_propagate() -> None:
    """Verify _dispatch_callback swallows exceptions."""
    from fi.gateway._base_client import BaseClient

    class _BrokenCallback(CallbackHandler):
        def on_request_start(self, request: RequestOptions) -> None:
            raise RuntimeError("Boom!")

    # Create a minimal concrete client to test dispatch
    class _TestClient(BaseClient):
        pass

    client = _TestClient(
        api_key="sk-test", base_url="http://localhost", callbacks=[_BrokenCallback()]
    )
    # Should not raise
    client._dispatch_callback("on_request_start", _make_request())


# --- LoggingCallback tests ---


def _messages(caplog: pytest.LogCaptureFixture) -> list[tuple[str, str]]:
    return [
        (r.levelname, r.getMessage()) for r in caplog.records if r.name == "fi.gateway"
    ]


def test_logging_callback_request_start(caplog: pytest.LogCaptureFixture) -> None:
    cb = LoggingCallback(level="INFO")
    with caplog.at_level(logging.INFO, logger="fi.gateway"):
        cb.on_request_start(_make_request())
    assert _messages(caplog) == [("INFO", "Request: POST /v1/chat/completions")]


def test_logging_callback_request_end(caplog: pytest.LogCaptureFixture) -> None:
    cb = LoggingCallback(level="INFO")
    with caplog.at_level(logging.INFO, logger="fi.gateway"):
        cb.on_request_end(_make_request(), _make_response())
        cb.on_request_end(_make_request(), b"audio-bytes")
    assert _messages(caplog) == [
        ("INFO", "Response: status=200 provider=openai latency=100ms cost=0.005"),
        ("INFO", "Response: POST /v1/chat/completions"),
    ]


def test_logging_callback_error(caplog: pytest.LogCaptureFixture) -> None:
    cb = LoggingCallback()
    with caplog.at_level(logging.INFO, logger="fi.gateway"):
        cb.on_error(_make_request(), RuntimeError("test error"))
    assert _messages(caplog) == [
        ("ERROR", "Error: POST /v1/chat/completions - test error")
    ]


def test_logging_callback_retry(caplog: pytest.LogCaptureFixture) -> None:
    cb = LoggingCallback()
    with caplog.at_level(logging.INFO, logger="fi.gateway"):
        cb.on_retry(_make_request(), RuntimeError("retry"), 1, 0.5)
    assert _messages(caplog) == [
        ("WARNING", "Retry 1 after 0.50s: POST /v1/chat/completions - retry")
    ]


# --- MetricsCallback tests ---


def test_metrics_initial_state() -> None:
    m = MetricsCallback()
    assert m.total_requests == 0
    assert m.total_errors == 0
    assert m.total_tokens == 0
    assert m.total_cost == 0.0
    assert m.avg_latency == 0.0
    assert m.p50_latency == 0.0
    assert m.p95_latency == 0.0
    assert m.p99_latency == 0.0
    assert m.error_rate == 0.0


def test_metrics_tracks_requests() -> None:
    m = MetricsCallback()
    req = _make_request()
    resp = _make_response(latency=100, cost=0.01)
    m.on_request_end(req, resp)
    m.on_request_end(req, _make_response(latency=200, cost=0.02, total_tokens=12))
    assert m.total_requests == 2
    assert m.total_cost == 0.03
    assert m.avg_latency == 150.0
    assert m.total_tokens == 42


def test_metrics_tracks_errors() -> None:
    m = MetricsCallback()
    req = _make_request()
    m.on_request_end(req, _make_response())
    m.on_error(req, RuntimeError("fail"))
    assert m.total_errors == 1
    assert m.error_rate == 0.5  # 1 error / (1 request + 1 error)


def test_metrics_percentiles() -> None:
    m = MetricsCallback()
    req = _make_request()
    for i in range(100):
        m.on_request_end(req, _make_response(latency=i + 1))
    assert m.p50_latency == 50.5  # median of 1..100
    assert m.p95_latency >= 95
    assert m.p99_latency >= 99


def test_metrics_reset() -> None:
    m = MetricsCallback()
    req = _make_request()
    m.on_request_end(req, _make_response())
    m.on_error(req, RuntimeError("fail"))
    m.reset()
    assert m.total_requests == 0
    assert m.total_errors == 0
    assert m.total_tokens == 0
    assert m.total_cost == 0.0
    assert m.avg_latency == 0.0


def test_metrics_no_agentcc_metadata() -> None:
    """Metrics should handle responses without agentcc metadata (audio bytes)."""
    m = MetricsCallback()
    req = _make_request()
    m.on_request_end(req, b"audio-bytes")
    m.on_request_end(req, SimpleNamespace(agentcc=None, usage=None))
    assert m.total_requests == 2
    assert m.avg_latency == 0.0
    assert m.total_tokens == 0


@pytest.mark.parametrize(
    "name",
    [
        "CallbackRequest",
        "CallbackResponse",
        "StreamInfo",
        "redact_callback_request",
        "JSONLoggingCallbackHandler",
        "AgentCCLogger",
    ],
)
def test_the_shim_only_callback_names_are_gone(name: str, monkeypatch) -> None:
    import fi.gateway
    import fi.gateway.callbacks as callbacks

    value = getattr(callbacks, name, None)
    assert value is not None
    if name in {"JSONLoggingCallbackHandler", "AgentCCLogger"}:
        with pytest.warns(DeprecationWarning, match=name):
            assert getattr(fi.gateway, name, None) is value
        with pytest.warns(DeprecationWarning, match=name):
            logger = value()
        assert isinstance(logger, callbacks.CallbackHandler)
        assert callable(logger.on_request_end)
        request = callbacks.CallbackRequest("POST", "/v1/chat/completions", {},
                                            {"model": "m", "messages": []})
        response = callbacks.CallbackResponse(200, {}, body={"model": "m"})
        events = []
        if name == "JSONLoggingCallbackHandler":
            monkeypatch.setattr(logger, "_write_log", events.append)
            logger.on_request_end(request, response)
            assert len(events) == 1
            assert events[0]["event"] == "request_complete"
            assert events[0]["model"] == "m" and events[0]["status_code"] == 200
        else:
            monkeypatch.setattr(logger, "log_pre_call", lambda *args: events.append(("pre", args)))
            monkeypatch.setattr(logger, "log_success", lambda *args: events.append(("success", args)))
            logger.on_request_start(request)
            logger.on_request_end(request, response)
            assert [event for event, _ in events] == ["pre", "success"]
            assert events[0][1] == ("m", [], request.body)
            assert events[1][1][:3] == ("m", [], response)
    else:
        # Released only from callbacks, never from the gateway root. Records stay
        # plain dataclasses; callbacks= is the warning boundary for their use.
        assert not hasattr(fi.gateway, name)
        from fi.gateway.callbacks import base

        assert value is getattr(base, name)
        if name == "CallbackRequest":
            request = value("POST", "/v1/chat/completions", {}, {"messages": []})
            assert request.method == "POST" and request.body == {"messages": []}
        elif name == "CallbackResponse":
            response = value(200, {}, body={"model": "m"})
            assert response.status_code == 200 and response.body == {"model": "m"}
        elif name == "StreamInfo":
            assert value(chunk_count=2).chunk_count == 2
        else:
            request = base.CallbackRequest("POST", "/v1/chat/completions", {},
                                           {"messages": [{"role": "user", "content": "private"}]})
            redacted = value(request)
            assert redacted.body["messages"][0]["content"] == "[REDACTED]"
            assert request.body["messages"][0]["content"] == "private"
