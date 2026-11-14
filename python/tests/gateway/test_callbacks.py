"""Tests for the callback system."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

from fi.gateway.callbacks import (
    CallbackHandler,
    CallbackRequest,
    CallbackResponse,
    LoggingCallback,
    MetricsCallback,
    StreamInfo,
)


class _RecordingCallback(CallbackHandler):
    """Test callback that records all calls."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple]] = []

    def on_request_start(self, request: CallbackRequest) -> None:
        self.calls.append(("on_request_start", (request,)))

    def on_request_end(self, request: CallbackRequest, response: CallbackResponse) -> None:
        self.calls.append(("on_request_end", (request, response)))

    def on_error(self, request: CallbackRequest, error: Exception) -> None:
        self.calls.append(("on_error", (request, error)))

    def on_retry(self, request: CallbackRequest, error: Exception, attempt: int, delay: float) -> None:
        self.calls.append(("on_retry", (request, error, attempt, delay)))

    def on_stream_start(self, request: CallbackRequest, stream: StreamInfo) -> None:
        self.calls.append(("on_stream_start", (request, stream)))

    def on_stream_end(self, request: CallbackRequest, stream: StreamInfo, completion: object) -> None:
        self.calls.append(("on_stream_end", (request, stream, completion)))

    def on_cache_hit(self, request: CallbackRequest, response: CallbackResponse, cache_type: str) -> None:
        self.calls.append(("on_cache_hit", (request, response, cache_type)))


def _make_request() -> CallbackRequest:
    return CallbackRequest(method="POST", url="/v1/chat/completions", headers={}, body=None)


def _make_response(latency: int = 100, cost: float | None = 0.005, status: int = 200) -> CallbackResponse:
    meta = MagicMock()
    meta.provider = "openai"
    meta.latency_ms = latency
    meta.cost = cost
    return CallbackResponse(status_code=status, headers={}, agentcc=meta)


# --- Base handler tests ---

def test_default_handler_methods_are_noop() -> None:
    """All default methods should execute without error."""
    handler = CallbackHandler()
    req = _make_request()
    resp = _make_response()
    handler.on_request_start(req)
    handler.on_request_end(req, resp)
    handler.on_stream_start(req, StreamInfo())
    handler.on_stream_chunk(req, None)
    handler.on_stream_end(req, StreamInfo(), None)
    handler.on_error(req, Exception("test"))
    handler.on_retry(req, Exception("test"), 1, 0.5)
    handler.on_guardrail_warning(req, None)
    handler.on_guardrail_block(req, None)
    handler.on_cache_hit(req, resp, "hit_exact")


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
        def on_request_start(self, request: CallbackRequest) -> None:
            raise RuntimeError("Boom!")

    # Create a minimal concrete client to test dispatch
    class _TestClient(BaseClient):
        pass

    client = _TestClient(api_key="sk-test", base_url="http://localhost", callbacks=[_BrokenCallback()])
    # Should not raise
    client._dispatch_callback("on_request_start", _make_request())


# --- LoggingCallback tests ---

def test_logging_callback_request_start(caplog: object) -> None:
    cb = LoggingCallback(level="INFO")
    req = _make_request()
    logging.captureWarnings(True)
    logger = logging.getLogger("agentcc")
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    try:
        cb.on_request_start(req)
    finally:
        logger.removeHandler(handler)
        logging.captureWarnings(False)


def test_logging_callback_request_end() -> None:
    cb = LoggingCallback(level="INFO")
    req = _make_request()
    resp = _make_response()
    # Should not raise
    cb.on_request_end(req, resp)


def test_logging_callback_error() -> None:
    cb = LoggingCallback()
    req = _make_request()
    cb.on_error(req, RuntimeError("test error"))


def test_logging_callback_retry() -> None:
    cb = LoggingCallback()
    req = _make_request()
    cb.on_retry(req, RuntimeError("retry"), 1, 0.5)


def test_logging_callback_cache_hit() -> None:
    cb = LoggingCallback()
    req = _make_request()
    resp = _make_response()
    cb.on_cache_hit(req, resp, "hit_exact")


# --- MetricsCallback tests ---

def test_metrics_initial_state() -> None:
    m = MetricsCallback()
    assert m.total_requests == 0
    assert m.total_errors == 0
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
    m.on_request_end(req, _make_response(latency=200, cost=0.02))
    assert m.total_requests == 2
    assert m.total_cost == 0.03
    assert m.avg_latency == 150.0


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
    assert m.total_cost == 0.0
    assert m.avg_latency == 0.0


def test_metrics_no_agentcc_metadata() -> None:
    """Metrics should handle responses without agentcc metadata."""
    m = MetricsCallback()
    req = _make_request()
    resp = CallbackResponse(status_code=200, headers={}, agentcc=None)
    m.on_request_end(req, resp)
    assert m.total_requests == 1
    assert m.avg_latency == 0.0


# --- CallbackRequest/CallbackResponse tests ---

def test_callback_request_creation() -> None:
    req = CallbackRequest(method="POST", url="/v1/chat/completions", headers={"x-key": "val"}, body={"model": "gpt-4o"})
    assert req.method == "POST"
    assert req.body == {"model": "gpt-4o"}


def test_callback_response_creation() -> None:
    resp = CallbackResponse(status_code=200, headers={"x-h": "v"}, body={"id": "chatcmpl-1"})
    assert resp.status_code == 200
    assert resp.agentcc is None


def test_stream_info_defaults() -> None:
    si = StreamInfo()
    assert si.agentcc is None
    assert si.chunk_count == 0
