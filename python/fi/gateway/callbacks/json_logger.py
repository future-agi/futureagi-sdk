"""JSON structured logging callback handler."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from fi.gateway.callbacks.base import (
    CallbackHandler,
    CallbackRequest,
    CallbackResponse,
    StreamInfo,
)


class JSONLoggingCallbackHandler(CallbackHandler):
    """Writes structured JSON logs for every request.

    When *file_path* is provided, each log entry is appended as a single JSON
    line.  When *file_path* is ``None`` (default), logs are emitted via the
    standard ``agentcc.json_logger`` Python logger at the given *log_level*.
    """

    def __init__(self, file_path: str | None = None, log_level: str = "INFO") -> None:
        self._file_path = file_path
        self._log_level = log_level
        self._logger = logging.getLogger("agentcc.json_logger")

    # ------------------------------------------------------------------
    # CallbackHandler overrides
    # ------------------------------------------------------------------

    def on_request_end(self, request: CallbackRequest, response: CallbackResponse) -> None:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "event": "request_complete",
            "method": request.method,
            "url": request.url,
            "status_code": response.status_code,
            "latency_ms": response.agentcc.latency_ms if response.agentcc else None,
            "cost": response.agentcc.cost if response.agentcc else None,
            "model": response.body.get("model") if isinstance(response.body, dict) else None,
            "tokens": {
                "prompt": response.body.get("usage", {}).get("prompt_tokens") if isinstance(response.body, dict) else None,
                "completion": response.body.get("usage", {}).get("completion_tokens") if isinstance(response.body, dict) else None,
            },
            "cache_hit": response.agentcc.cache_status if response.agentcc else None,
        }
        self._write_log(log_entry)

    def on_error(self, request: CallbackRequest, error: Exception) -> None:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "event": "request_error",
            "method": request.method,
            "url": request.url,
            "error_type": type(error).__name__,
            "error_message": str(error),
        }
        self._write_log(log_entry)

    def on_stream_end(self, request: CallbackRequest, stream: StreamInfo, completion: Any) -> None:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "event": "stream_complete",
            "method": request.method,
            "url": request.url,
            "chunk_count": stream.chunk_count if stream else None,
        }
        self._write_log(log_entry)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _write_log(self, entry: dict[str, Any]) -> None:
        line = json.dumps(entry, default=str)
        if self._file_path:
            with open(self._file_path, "a") as f:
                f.write(line + "\n")
        else:
            self._logger.log(getattr(logging, self._log_level, logging.INFO), line)
