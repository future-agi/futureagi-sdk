"""Per-run export outcome, independent of batch processor logs and force_flush's queue status.

The public requests-session hook works with traceAI's HTTP exporter across OTLP versions. It
observes attempts, but only a *terminal batch failure* is retained: a retry that succeeds is not
lost data. Error bodies/reason phrases and transport exception text never reach exporter logs.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Any, Optional
from urllib.parse import urlsplit, urlunsplit
import warnings

import requests

from fi.experiments.errors import TraceExportError, TraceExportWarning


class ExportStatus:
    def __init__(self, run_id: str, endpoint: str, redactor: Any) -> None:
        parts = urlsplit(endpoint)
        # Diagnostic URLs never contain userinfo, query parameters or fragments.
        self.endpoint = redactor.text(urlunsplit((parts.scheme, parts.netloc.rsplit("@", 1)[-1],
                                                 parts.path, "", "")))
        self.run_id = run_id
        self.error: Optional[TraceExportError] = None
        self.status_code: Optional[int] = None
        self.reason = "exporter failed"
        self._warned = False

    def begin_batch(self) -> None:
        self.status_code = None
        self.reason = "exporter failed"

    def failed(self) -> None:
        # A later successful batch must never erase an earlier dropped batch.
        if self.error is None:
            self.error = TraceExportError(self.run_id, self.endpoint, self.status_code, self.reason)

    def warn(self) -> None:
        # Called on the run thread after tracing shutdown, never on the exporter worker.
        if self.error is not None and not self._warned:
            self._warned = True
            try:
                warnings.warn(str(self.error), TraceExportWarning, stacklevel=3)
            except TraceExportWarning:
                # A warnings-as-errors policy must not replace the typed export error or
                # an in-flight primary error (especially RunInterrupted) during cleanup.
                pass


class ExportSession(requests.Session):
    """Record status without exposing a response body, arbitrary reason phrase or exception text."""

    def __init__(self, outcome: ExportStatus) -> None:
        super().__init__()
        self.outcome = outcome

    def send(self, request: Any, **kwargs: Any) -> Any:
        # Do not follow redirects with credentials or accidentally accept a login page as export.
        kwargs["allow_redirects"] = False
        try:
            response = super().send(request, **kwargs)
        except requests.RequestException as exc:
            self.outcome.status_code = None
            if isinstance(exc, requests.Timeout):
                self.outcome.reason = "connection timed out"
                raise requests.Timeout("connection timed out") from None
            if isinstance(exc, requests.ConnectionError):
                self.outcome.reason = "connection failed"
                raise requests.ConnectionError("connection failed") from None
            # Keep malformed requests and response decoding failures non-retryable. Raising
            # ConnectionError for all RequestExceptions would add OTLP connection retries.
            self.outcome.reason = "request failed"
            raise requests.RequestException("request failed") from None
        self.outcome.status_code = response.status_code
        self.outcome.reason = f"HTTP {response.status_code}"
        # Upstream exporters log these fields, sometimes including response.text. Keep retries
        # and status handling intact, but never pass through server-controlled diagnostic text.
        try:
            response.reason = HTTPStatus(response.status_code).phrase
        except ValueError:
            response.reason = "HTTP response"
        if not 200 <= response.status_code < 300:
            response._content = b""
        return response
