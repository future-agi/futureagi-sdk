"""The trace export session (``ExportSession``, the session the OTLP span exporter posts through) sends a
loopback collector's export straight to this machine, so the run's keys are not handed to an environment proxy; a
remote collector keeps ``HTTP_PROXY`` / ``HTTPS_PROXY`` / ``ALL_PROXY`` and ``NO_PROXY``.

A remote host here is a made-up name the test resolves to a local server (the no-egress guard allows only loopback
addresses), so what the test checks is which listener got the request.
"""

from __future__ import annotations

import pytest
import requests

from fi.experiments._redact import Redactor
from fi.experiments._tracing.export_status import ExportSession, ExportStatus
from fi.experiments._tracing.instrument import python_supported
from tests.platform.test_env_proxy import REMOTE, _proxy_url, _Server, servers_fixture  # noqa: F401  (fixture)


def _export(url: str) -> None:
    with ExportSession(ExportStatus("run-1", url, Redactor([]))) as session:
        try:
            session.post(url, data=b"spans", headers={"Authorization": "Bearer run-key-not-a-secret"}, timeout=5)
        except requests.RequestException:
            pass


def _proxy_everything(monkeypatch, proxy) -> None:
    for name in ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy"):
        monkeypatch.setenv(name, _proxy_url(proxy))


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "[::1]"])
def test_a_loopback_collector_skips_the_environment_proxy(servers, monkeypatch, host):
    proxy, sink = servers
    if host == "[::1]":
        try:
            sink = _Server("direct", host="::1")
        except OSError:
            pytest.skip("this machine has no IPv6 loopback")
    _proxy_everything(monkeypatch, proxy)
    _export(f"http://{host}:{sink.port}/v1/traces")
    assert proxy.requests == []
    assert [(method, path) for method, path, _ in sink.requests] == [("POST", "/v1/traces")]


def test_a_remote_plain_http_collector_that_gets_keys_is_reached_directly(servers, monkeypatch):
    """Plain HTTP that carries keys is sent by the SDK's own session with proxies off, whatever the proxy variables say."""
    proxy, sink = servers
    _proxy_everything(monkeypatch, proxy)
    _export(f"http://{REMOTE}:{sink.port}/v1/traces")
    assert proxy.requests == []
    assert [method for method, _, _ in sink.requests] == ["POST"]


def test_no_proxy_leaves_a_remote_collector_out_of_the_proxy(servers, monkeypatch):
    proxy, sink = servers
    _proxy_everything(monkeypatch, proxy)
    monkeypatch.setenv("NO_PROXY", REMOTE)
    monkeypatch.setenv("no_proxy", REMOTE)
    _export(f"http://{REMOTE}:{sink.port}/v1/traces")
    assert proxy.requests == []
    assert [(method, path) for method, path, _ in sink.requests] == [("POST", "/v1/traces")]


@pytest.mark.skipif(
    not python_supported(),
    reason="fi-instrumentation-otel does not support Python 3.14, so a run with tracing raises TracingUnsupportedError",
)
def test_a_run_exports_its_spans_to_a_loopback_collector_without_the_environment_proxy(servers, monkeypatch):
    """The whole path: ``experiments.run`` with the real OTLP HTTP span exporter, whose session is the export
    session, and an environment proxy set with no ``NO_PROXY``: every export reaches the loopback collector."""
    from tests.experiments.unit.contract_server import ContractServer
    from tests.experiments.unit.test_otlp_failures import collector, run_on

    proxy, _sink = servers
    _proxy_everything(monkeypatch, proxy)
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_TRACES_TIMEOUT", "5")
    with collector(200) as (base, sent):
        result = run_on(base, ContractServer())
    assert result.status == "completed"
    assert [method for method, _, _ in sent] and all(method == "POST" for method, _, _ in sent)
    assert proxy.requests == []
