"""The Zipkin exporter of ``fi.evals.otel._tracer_factories._create_exporter`` uses the loopback-direct session the other
HTTP exporters use: a loopback collector's export skips the environment proxy, a remote collector keeps it."""

from __future__ import annotations

import pytest

pytest.importorskip("opentelemetry.sdk.trace")
pytest.importorskip("opentelemetry.exporter.zipkin.json")

from fi._core.requests_session import LoopbackDirectSession  # noqa: E402
from fi.evals.otel._tracer_factories import _create_exporter  # noqa: E402
from fi.evals.otel.config import ExporterConfig, ExporterType  # noqa: E402
from tests.evals.test_trace_export_loopback import _export_one_span, _proxy_everything  # noqa: E402
from tests.platform.test_env_proxy import REMOTE, servers_fixture  # noqa: F401,E402  (fixture)


def _zipkin(endpoint: str | None):
    return _create_exporter(ExporterConfig(type=ExporterType.ZIPKIN, endpoint=endpoint, timeout_ms=5000))


def test_the_exporter_has_the_loopback_direct_session():
    assert isinstance(_zipkin("http://127.0.0.1:9411/api/v2/spans").session, LoopbackDirectSession)
    assert isinstance(_zipkin(None).session, LoopbackDirectSession)


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost"])
def test_a_loopback_collector_skips_the_environment_proxy(servers, monkeypatch, host):
    proxy, sink = servers
    _proxy_everything(monkeypatch, proxy)
    _export_one_span(_zipkin(f"http://{host}:{sink.port}/api/v2/spans"))
    assert proxy.requests == []
    assert [(method, path) for method, path, _ in sink.requests] == [("POST", "/api/v2/spans")]


def test_a_remote_collector_goes_through_the_environment_proxy(servers, monkeypatch):
    proxy, sink = servers
    _proxy_everything(monkeypatch, proxy)
    _export_one_span(_zipkin(f"http://{REMOTE}:{sink.port}/api/v2/spans"))
    assert [method for method, _, _ in proxy.requests] == ["POST"]
    assert sink.requests == []
