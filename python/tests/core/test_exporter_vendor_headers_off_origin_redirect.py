"""A redirect off the first request's origin carries none of the caller's headers, for each OpenTelemetry HTTP exporter
the SDK builds for a collector of the user's choice (OTLP_HTTP, ARIZE, PHOENIX, LANGFUSE).

Real loopback sockets. Each exporter is built by ``_create_exporter`` with vendor headers that hold planted markers (a
Honeycomb ``x-honeycomb-team``, an Arize ``api_key`` and ``space_id``, ...) and sends to origin A on 127.0.0.1. A answers
301, 302, 303, 307 or 308 to a second origin: another host on the same port (127.0.0.2), another port on the same host,
or another host and port. The second origin records the raw bytes of each request and holds 0 bytes of any marker,
while it does get the export (one request, with the exporter's ``User-Agent``, and for 307 and 308 the body and its
``Content-Type``). A redirect that stays on the first origin delivers every marker.
"""

from __future__ import annotations

import secrets

import pytest

pytest.importorskip("opentelemetry.sdk.trace")
pytest.importorskip("opentelemetry.exporter.otlp.proto.http.trace_exporter")

from fi.evals.otel._tracer_factories import _create_exporter  # noqa: E402
from fi.evals.otel.config import ExporterConfig, ExporterType  # noqa: E402
from tests.core.redirect_sinks import _Listener  # noqa: E402

STATUSES = (301, 302, 303, 307, 308)
CELLS = ("other-host", "other-port", "other-host-and-port")
VENDOR_NAMES = {
    # A name that opens with "accept-" is not one of the Accept headers, so it is dropped too.
    ExporterType.OTLP_HTTP: ("x-honeycomb-team", "x-honeycomb-dataset", "accept-x-honeycomb-team"),
    ExporterType.ARIZE: ("api_key", "space_id"),
    ExporterType.PHOENIX: ("api_key", "x-phoenix-project"),
    ExporterType.LANGFUSE: ("x-langfuse-public-key", "x-langfuse-project"),
}


def _vendor_headers(kind: ExporterType) -> dict[str, str]:
    tag = secrets.token_hex(8)
    return {name: "MK" + kind.name + name.replace("-", "").replace("_", "").upper() + tag for name in VENDOR_NAMES[kind]}


def _export(kind: ExporterType, url: str, headers: dict[str, str]):
    from opentelemetry.sdk.trace import TracerProvider

    exporter = _create_exporter(ExporterConfig(type=kind, endpoint=url, headers=dict(headers), timeout_ms=5000))
    span = TracerProvider().get_tracer("t").start_span("s")
    span.end()
    try:
        return exporter.export([span])
    finally:
        exporter.shutdown()


def _origins(cell: str, status: int) -> tuple[str, _Listener, _Listener]:
    first = _Listener("127.0.0.1")
    if cell == "other-host":
        try:
            second = _Listener("127.0.0.2", first.port)
        except OSError:
            first.close()
            pytest.skip("127.0.0.2 cannot listen on the port of the first origin here")
    elif cell == "other-port":
        second = _Listener("127.0.0.1")
    else:
        second = _Listener("127.0.0.2")
    first.redirect = ("http", status, f"http://{second.host}:{second.port}/v1/traces/done")
    return f"http://127.0.0.1:{first.port}/v1/traces", first, second


def _marker_bytes(raw: bytes, headers: dict[str, str]) -> int:
    return sum(raw.count(value.encode()) * len(value) for value in headers.values())


@pytest.mark.parametrize("status", STATUSES, ids=lambda status: str(status))
@pytest.mark.parametrize("cell", CELLS)
@pytest.mark.parametrize("kind", list(VENDOR_NAMES), ids=lambda kind: kind.name)
def test_off_origin_redirect_carries_no_vendor_header(kind: ExporterType, cell: str, status: int) -> None:
    from opentelemetry.sdk.trace.export import SpanExportResult

    headers = _vendor_headers(kind)
    url, first, second = _origins(cell, status)
    try:
        result = _export(kind, url, headers)
    finally:
        first.close()
        second.close()
    raw = b"".join(record for _, record in second.records)
    assert _marker_bytes(raw, headers) == 0, f"{_marker_bytes(raw, headers)} marker bytes at the second origin"
    assert len(first.records) == 1 and _marker_bytes(first.records[0][1], headers) > 0
    assert result == SpanExportResult.SUCCESS
    assert len(second.records) == 1, "the redirect did not reach the second origin"
    lowered = raw.lower()
    assert b"user-agent:" in lowered
    if status in (307, 308):
        assert b"content-type: application/x-protobuf" in lowered and b"content-length:" in lowered


@pytest.mark.parametrize("status", STATUSES, ids=lambda status: str(status))
@pytest.mark.parametrize("kind", list(VENDOR_NAMES), ids=lambda kind: kind.name)
def test_same_origin_redirect_delivers_every_vendor_header(kind: ExporterType, status: int) -> None:
    from opentelemetry.sdk.trace.export import SpanExportResult

    headers = _vendor_headers(kind)
    first = _Listener("127.0.0.1")
    first.redirect = ("http", status, f"http://127.0.0.1:{first.port}/v1/traces/done")
    try:
        result = _export(kind, f"http://127.0.0.1:{first.port}/v1/traces", headers)
    finally:
        first.close()
    assert result == SpanExportResult.SUCCESS
    assert len(first.records) == 2 and b"/done" in first.records[1][1].split(b"\r\n", 1)[0]
    for value in headers.values():
        assert value.encode() in first.records[1][1], "the redirect on the first origin lost a vendor header"
