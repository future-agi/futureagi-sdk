"""Safe logging and aggregate metrics for parsed values and callback wrappers."""

from __future__ import annotations

import logging
import statistics
import threading
from typing import Any

from fi.gateway.callbacks.base import CallbackHandler, CallbackRequest, CallbackResponse


def _status_code(response: Any) -> int | None:
    code = getattr(response, "status_code", None)
    if not isinstance(code, int):
        http = getattr(getattr(response, "agentcc", None), "http_response", None)
        code = getattr(http, "status_code", None)
    return code if isinstance(code, int) else None


class LoggingCallback(CallbackHandler):
    def __init__(self, level: str = "INFO", logger_name: str = "agentcc") -> None:
        self._level = getattr(logging, level.upper(), logging.INFO)
        self._logger = logging.getLogger(logger_name)

    def on_request_start(self, request: CallbackRequest) -> None:
        # This sink deliberately omits body, headers and files. Never log the
        # live descriptor: caller-supplied credential fields are not masked there.
        self._logger.log(self._level, "Request: %s %s", request.method, request.url)

    def on_request_end(self, request: CallbackRequest, response: Any) -> None:
        meta = getattr(response, "agentcc", None)
        status = _status_code(response)
        if meta is not None:
            self._logger.log(
                self._level, "Response: status=%s provider=%s latency=%dms cost=%s",
                status if status is not None else "-", getattr(meta, "provider", "unknown"),
                getattr(meta, "latency_ms", 0) or 0, getattr(meta, "cost", None),
            )
        else:
            self._logger.log(self._level, "Response: status=%s", status if status is not None else "-")

    def on_error(self, request: CallbackRequest, error: Exception) -> None:
        self._logger.log(logging.ERROR, "Error: %s %s - %s", request.method, request.url, error)

    def on_retry(self, request: CallbackRequest, error: Exception, attempt: int, delay: float) -> None:
        self._logger.log(logging.WARNING, "Retry %d after %.2fs: %s %s - %s", attempt, delay, request.method, request.url, error)

    def on_cache_hit(self, request: CallbackRequest, response: CallbackResponse, cache_type: str) -> None:
        self._logger.log(self._level, "Cache hit (%s): %s %s", cache_type, request.method, request.url)


class MetricsCallback(CallbackHandler):
    """Thread-safe counters and latency percentiles."""

    def __init__(self, *, count_tokens: bool = False) -> None:
        """Set ``count_tokens=True`` to opt into usage-token aggregation."""
        self._count_tokens = count_tokens
        self._lock = threading.Lock()
        self._total_requests = 0
        self._total_errors = 0
        self._total_tokens = 0
        self._total_cost = 0.0
        self._latencies: list[float] = []

    def on_request_end(self, request: CallbackRequest, response: Any) -> None:
        meta = getattr(response, "agentcc", None)
        usage = getattr(response, "usage", None)
        tokens = getattr(usage, "total_tokens", None)
        if tokens is None and isinstance(getattr(response, "body", None), dict):
            tokens = (response.body.get("usage") or {}).get("total_tokens")
        with self._lock:
            self._total_requests += 1
            if self._count_tokens and isinstance(tokens, int):
                self._total_tokens += tokens
            if meta is not None:
                latency = getattr(meta, "latency_ms", 0)
                if latency:
                    self._latencies.append(float(latency))
                cost = getattr(meta, "cost", None)
                if cost is not None:
                    self._total_cost += float(cost)

    def on_error(self, request: CallbackRequest, error: Exception) -> None:
        with self._lock:
            self._total_errors += 1

    @property
    def total_requests(self) -> int:
        return self._total_requests

    @property
    def total_errors(self) -> int:
        return self._total_errors

    @property
    def total_tokens(self) -> int:
        return self._total_tokens

    @property
    def total_cost(self) -> float:
        return self._total_cost

    @property
    def avg_latency(self) -> float:
        with self._lock:
            return statistics.mean(self._latencies) if self._latencies else 0.0

    @property
    def p50_latency(self) -> float:
        with self._lock:
            return statistics.median(self._latencies) if self._latencies else 0.0

    def _percentile(self, percentile: float) -> float:
        with self._lock:
            if not self._latencies:
                return 0.0
            values = sorted(self._latencies)
            return values[min(int(len(values) * percentile), len(values) - 1)]

    @property
    def p95_latency(self) -> float:
        return self._percentile(0.95)

    @property
    def p99_latency(self) -> float:
        return self._percentile(0.99)

    @property
    def error_rate(self) -> float:
        total = self._total_requests + self._total_errors
        return self._total_errors / total if total > 0 else 0.0

    def reset(self) -> None:
        with self._lock:
            self._total_requests = self._total_errors = self._total_tokens = 0
            self._total_cost = 0.0
            self._latencies = []
