"""A 3xx answer to the experiment trace export is recorded as the run's export status and nothing is followed: the
listener the ``Location`` names, on another port or on the exporter's own origin, receives no connection and no byte
of the keys. The collector listener sees the one request that carries the keys."""

from __future__ import annotations

import pytest

from tests.core._plaintext_oracle import PROXY_NAMES, MARKER_KEY, MARKER_SECRET, Sink

REDIRECT_STATUSES = [301, 302, 303, 307, 308]


def _export_one_span(collector_url: str, tmp_path, monkeypatch):
    from fi.experiments._redact import Redactor
    from fi.experiments._tracing.export import exporter_factory
    from fi.experiments._tracing.export_status import ExportStatus

    for name in PROXY_NAMES:
        monkeypatch.delenv(name, raising=False)
    endpoint = collector_url + "/tracer/v1/traces"
    outcome = ExportStatus("run-1", endpoint, Redactor())
    make = exporter_factory(base_url=collector_url, api_key=MARKER_KEY, secret_key=MARKER_SECRET, project="p",
                            run_name="r", run_id="run-1", redactor=Redactor(), outcome=outcome, _endpoint=endpoint)
    provider = make()
    provider.get_tracer("t").start_span("s").end()
    provider.shutdown()
    outcome.failed()
    return outcome


@pytest.mark.parametrize("status", REDIRECT_STATUSES)
def test_a_redirect_to_another_listener_is_not_followed_and_it_sees_no_key_byte(status, tmp_path, monkeypatch):
    target = Sink()
    collector = Sink(status=f"{status} Redirect".encode(), location=f"http://127.0.0.1:{target.port}/landed")
    try:
        outcome = _export_one_span(f"http://127.0.0.1:{collector.port}", tmp_path, monkeypatch)
        assert collector.requests == 1
        assert collector.marker_bytes > 0  # the first request is the one that carries the keys
        assert target.requests == 0
        assert target.chunks == []
        assert target.marker_bytes == 0
        assert outcome.error is not None and outcome.error.status_code == status
    finally:
        collector.close()
        target.close()


@pytest.mark.parametrize("status", REDIRECT_STATUSES)
def test_a_redirect_to_the_exporters_own_origin_is_not_followed(status, tmp_path, monkeypatch):
    collector = Sink(status=f"{status} Redirect".encode(), location="/landed")
    try:
        outcome = _export_one_span(f"http://127.0.0.1:{collector.port}", tmp_path, monkeypatch)
        assert collector.requests == 1
        assert b"GET /landed" not in b"".join(collector.chunks) and b"POST /landed" not in b"".join(collector.chunks)
        assert outcome.error is not None and outcome.error.status_code == status
    finally:
        collector.close()
