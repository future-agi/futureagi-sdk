"""A redirect whose ``Location`` names a port that cannot be read (out of range, or not a number) is refused with
``KeyedRedirectRefusedError`` (code ``KEYED_REDIRECT_REFUSED``), the error the SDK's ``requests`` session raises for a
refused redirect, and nothing is sent after the first request.

Real loopback sockets: origin A on 127.0.0.1 answers 301, 302, 303, 307 or 308 with such a ``Location`` (on 127.0.0.2
or ``localhost``, with ``NO_PROXY`` set so ``requests`` reads the port while it looks up proxies). A listener on
127.0.0.2 at A's port records every byte it gets: 0. A sees one request.
"""

from __future__ import annotations

import secrets

import pytest

from tests.core.redirect_sinks import _Listener

STATUSES = (301, 302, 303, 307, 308)
LOCATIONS = ("out-of-range", "not-a-number", "localhost-out-of-range")


def _origins(location: str, status: int) -> tuple[str, _Listener, _Listener]:
    first = _Listener("127.0.0.1")
    try:
        second = _Listener("127.0.0.2", first.port)
    except OSError:
        first.close()
        pytest.skip("127.0.0.2 cannot listen on the port of the first origin here")
    target = {
        "out-of-range": f"http://127.0.0.2:{first.port}0000/done",
        "not-a-number": f"http://127.0.0.2:{first.port}x/done",
        "localhost-out-of-range": f"http://localhost:{first.port}0000/done",
    }[location]
    first.redirect = ("http", status, target)
    return f"http://127.0.0.1:{first.port}/start", first, second


def _marker() -> str:
    return "MK" + "-A-" + secrets.token_hex(8)


@pytest.mark.parametrize("status", STATUSES, ids=lambda status: str(status))
@pytest.mark.parametrize("location", LOCATIONS)
@pytest.mark.parametrize("keyed", [False, True], ids=["plain", "keyed"])
def test_session_refuses_a_location_with_an_unreadable_port(
    keyed: bool, location: str, status: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fi._core.requests_session import LoopbackDirectSession
    from fi.errors import KeyedRedirectRefusedError

    monkeypatch.setenv("NO_PROXY", "internal.example")
    marker = _marker()
    headers = {"x-vendor-key": marker, **({"X-Api-Key": _marker()} if keyed else {})}
    url, first, second = _origins(location, status)
    try:
        with LoopbackDirectSession() as session:
            with pytest.raises(KeyedRedirectRefusedError) as caught:
                session.post(url, data=b"payload", headers=headers, timeout=10)
    finally:
        first.close()
        second.close()
    assert caught.value.get_error_code() == "KEYED_REDIRECT_REFUSED"
    assert caught.value.status_code == status
    assert second.records == [], f"{sum(len(raw) for _, raw in second.records)} bytes at 127.0.0.2"
    assert len(first.records) == 1 and marker.encode() in first.records[0][1]


@pytest.mark.parametrize("status", STATUSES, ids=lambda status: str(status))
@pytest.mark.parametrize("location", LOCATIONS)
def test_exporter_reports_a_location_with_an_unreadable_port_as_a_failed_export(
    location: str, status: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("opentelemetry.exporter.otlp.proto.http.trace_exporter")
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SpanExportResult

    from fi.evals.otel._tracer_factories import _create_exporter
    from fi.evals.otel.config import ExporterConfig, ExporterType

    monkeypatch.setenv("NO_PROXY", "internal.example")
    marker = _marker()
    url, first, second = _origins(location, status)
    exporter = _create_exporter(ExporterConfig(
        type=ExporterType.ARIZE, endpoint=url, headers={"space_id": marker}, timeout_ms=5000,
    ))
    span = TracerProvider().get_tracer("t").start_span("s")
    span.end()
    try:
        result = exporter.export([span])
    finally:
        exporter.shutdown()
        first.close()
        second.close()
    assert result == SpanExportResult.FAILURE
    assert second.records == [], f"{sum(len(raw) for _, raw in second.records)} bytes at 127.0.0.2"
    assert len(first.records) == 1
