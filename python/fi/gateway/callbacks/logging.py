"""Built-in callback implementations."""

from __future__ import annotations

import logging
import statistics
import threading

from fi.gateway.callbacks.base import CallbackHandler, CallbackRequest, CallbackResponse


class LoggingCallback(CallbackHandler):
    """Logs request lifecycle events using Python's logging module."""

    def __init__(self, level: str = "INFO", logger_name: str = "agentcc") -> None:
        self._level = getattr(logging, level.upper(), logging.INFO)
        self._logger = logging.getLogger(logger_name)

    def on_request_start(self, request: CallbackRequest) -> None:
        self._logger.log(self._level, "Request: %s %s", request.method, request.url)

    def on_request_end(self, request: CallbackRequest, response: CallbackResponse) -> None:
        meta = response.agentcc
        if meta:
            self._logger.log(
                self._level,
                "Response: status=%d provider=%s latency=%dms cost=%s",
                response.status_code,
                getattr(meta, "provider", "unknown"),
                getattr(meta, "latency_ms", 0),
                getattr(meta, "cost", None),
            )
        else:
            self._logger.log(self._level, "Response: status=%d", response.status_code)

    def on_error(self, request: CallbackRequest, error: Exception) -> None:
        self._logger.log(
            logging.ERROR,
            "Error: %s %s - %s",
            request.method,
            request.url,
            error,
        )

    def on_retry(self, request: CallbackRequest, error: Exception, attempt: int, delay: float) -> None:
        self._logger.log(
            logging.WARNING,
            "Retry %d after %.2fs: %s %s - %s",
            attempt,
            delay,
            request.method,
            request.url,
            error,
        )

    def on_cache_hit(self, request: CallbackRequest, response: CallbackResponse, cache_type: str) -> None:
        self._logger.log(self._level, "Cache hit (%s): %s %s", cache_type, request.method, request.url)


class MetricsCallback(CallbackHandler):
    """Collects in-memory request metrics.

    Thread-safe. Access aggregate stats via properties like
    ``avg_latency``, ``p95_latency``, ``error_rate``, etc.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._total_requests: int = 0
        self._total_errors: int = 0
        self._total_tokens: int = 0
        self._total_cost: float = 0.0
        self._latencies: list[float] = []

    def on_request_end(self, request: CallbackRequest, response: CallbackResponse) -> None:
        meta = response.agentcc
        with self._lock:
            self._total_requests += 1
            if meta:
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

    @property
    def p95_latency(self) -> float:
        with self._lock:
            if not self._latencies:
                return 0.0
            sorted_l = sorted(self._latencies)
            idx = int(len(sorted_l) * 0.95)
            return sorted_l[min(idx, len(sorted_l) - 1)]

    @property
    def p99_latency(self) -> float:
        with self._lock:
            if not self._latencies:
                return 0.0
            sorted_l = sorted(self._latencies)
            idx = int(len(sorted_l) * 0.99)
            return sorted_l[min(idx, len(sorted_l) - 1)]

    @property
    def error_rate(self) -> float:
        total = self._total_requests + self._total_errors
        return self._total_errors / total if total > 0 else 0.0

    def reset(self) -> None:
        """Clear all counters."""
        with self._lock:
            self._total_requests = 0
            self._total_errors = 0
            self._total_tokens = 0
            self._total_cost = 0.0
            self._latencies = []
