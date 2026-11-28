"""The HTTP span exporter reports redirect answers as failed deliveries."""

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SpanExportResult
from requests import Response

from fi._otlp_headers import futureagi_session


class Listener:
    def __init__(self, host, status=200, location=None):
        self.requests = []
        self.body_bytes = 0
        listener = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                listener.body_bytes += len(body)
                listener.requests.append((self.command, self.path, self.headers))
                self.send_response(status)
                if location is not None:
                    self.send_header("Location", location)
                self.send_header("Content-Length", "0")
                self.end_headers()

            do_GET = do_POST

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer((host, 0), Handler)
        self.thread = threading.Thread(
            target=self.server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True
        )

    @property
    def endpoint(self):
        host, port = self.server.server_address
        return f"http://{host}:{port}/v1/traces"

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()


@pytest.mark.parametrize(
    ("status", "has_location", "expected"),
    [
        pytest.param(307, False, SpanExportResult.FAILURE, id="307-no-location"),
        pytest.param(300, True, SpanExportResult.FAILURE, id="300-with-location"),
        pytest.param(308, False, SpanExportResult.FAILURE, id="308-no-location"),
        pytest.param(304, True, SpanExportResult.FAILURE, id="304-with-location"),
        pytest.param(200, False, SpanExportResult.SUCCESS, id="200"),
        pytest.param(304, False, SpanExportResult.SUCCESS, id="304-no-location"),
        pytest.param(300, False, SpanExportResult.SUCCESS, id="300-no-location"),
        pytest.param(302, True, SpanExportResult.FAILURE, id="302-with-location"),
    ],
)
def test_http_span_export_result_for_redirect_answers(
    status, has_location, expected, monkeypatch
):
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,127.0.0.2")
    headers = {"x-api-key": "redirect-key-value", "x-secret-key": "redirect-secret-value"}
    with Listener("127.0.0.2") as target:
        location = target.endpoint if has_location else None
        with Listener("127.0.0.1", status, location) as origin:
            exporter = OTLPSpanExporter(
                endpoint=origin.endpoint, session=futureagi_session(plain=True),
                headers=headers, timeout=2,
            )
            provider = TracerProvider()
            try:
                span = provider.get_tracer("redirect-test").start_span("one")
                span.end()
                result = exporter.export([span])
            finally:
                exporter.shutdown()
                provider.shutdown()

    assert len(origin.requests) == 1
    method, path, received = origin.requests[0]
    assert (method, path) == ("POST", "/v1/traces")
    assert origin.body_bytes > 0
    assert {name: received[name] for name in headers} == headers
    assert len(target.requests) == 0
    assert target.body_bytes == 0
    assert result is expected


def test_is_redirect_answer():
    from fi._core.requests_session import is_redirect_answer

    cases = [
        (301, None, True),
        (302, "/v1/traces", True),
        (303, "", True),
        (307, None, True),
        (308, None, True),
        (300, "/v1/traces", True),
        (304, "/v1/traces", True),
        (399, "/v1/traces", True),
        (300, None, False),
        (304, "", False),
        (200, "/v1/traces", False),
        (400, "/v1/traces", False),
    ]
    for status, location, expected in cases:
        response = Response()
        response.status_code = status
        if location is not None:
            response.headers["location"] = location
        assert is_redirect_answer(response) is expected, (status, location)
