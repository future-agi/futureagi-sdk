"""The evals OpenTelemetry exporters (``fi.evals.otel._tracer_factories._create_exporter``) send a loopback
collector's export straight to this machine, so the keys in the export headers are not handed to an environment
proxy; a remote collector keeps the proxy.

HTTP exporters are checked against a recording local server acting as the proxy. The gRPC exporter is checked in a
subprocess with ``grpc_proxy`` set and a byte-counting TCP listener standing in for the proxy. A remote host here is
a made-up name: an HTTP test resolves it to a local server, and the gRPC proxy resolves it, so what each test checks
is which listener got the bytes.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import textwrap
import threading
from pathlib import Path

import pytest

pytest.importorskip("opentelemetry.sdk.trace")
pytest.importorskip("opentelemetry.exporter.otlp.proto.http.trace_exporter")

from fi.evals.otel._tracer_factories import _create_exporter  # noqa: E402
from fi.evals.otel.config import ExporterConfig, ExporterType  # noqa: E402
from tests.platform.test_env_proxy import REMOTE, _proxy_url, servers_fixture  # noqa: F401,E402  (fixture)

PYTHON = Path(__file__).resolve().parents[2]
HTTP_TYPES = [
    ExporterType.OTLP_HTTP, ExporterType.ARIZE, ExporterType.PHOENIX, ExporterType.LANGFUSE, ExporterType.FUTUREAGI,
]


def _proxy_everything(monkeypatch, proxy) -> None:
    for name in ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy"):
        monkeypatch.setenv(name, _proxy_url(proxy))


def _export_one_span(exporter) -> None:
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor

    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    provider.get_tracer("t").start_span("s").end()
    provider.shutdown()


def _config(kind: ExporterType, endpoint: str) -> ExporterConfig:
    return ExporterConfig(type=kind, endpoint=endpoint, headers={"x-api-key": "run-key-not-a-secret"}, timeout_ms=5000)


@pytest.mark.parametrize("kind", HTTP_TYPES)
@pytest.mark.parametrize("host", ["127.0.0.1", "localhost"])
def test_a_loopback_collector_skips_the_environment_proxy(servers, monkeypatch, kind, host):
    proxy, sink = servers
    _proxy_everything(monkeypatch, proxy)
    exporter = _create_exporter(_config(kind, f"http://{host}:{sink.port}/v1/traces"))
    assert exporter is not None
    _export_one_span(exporter)
    assert proxy.requests == []
    assert [(method, path) for method, path, _ in sink.requests] == [("POST", "/v1/traces")]


@pytest.mark.parametrize("kind", HTTP_TYPES)
def test_a_remote_plain_http_collector_with_credentials_is_reached_directly_when_opted_in(servers, monkeypatch, kind):
    """The session the SDK builds for the exporter sends plain HTTP that carries keys straight to its host: the opt-in
    allows it, and the proxy variables do not route it."""
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    proxy, sink = servers
    _proxy_everything(monkeypatch, proxy)
    exporter = _create_exporter(_config(kind, f"http://{REMOTE}:{sink.port}/v1/traces"))
    assert exporter is not None
    _export_one_span(exporter)
    assert proxy.requests == []
    assert [(method, path) for method, path, _ in sink.requests] == [("POST", "/v1/traces")]


@pytest.mark.parametrize("kind", HTTP_TYPES)
def test_a_remote_plain_http_collector_with_credentials_is_refused_without_the_opt_in(servers, monkeypatch, kind):
    from fi.errors import ConfigurationError

    monkeypatch.delenv("FI_ALLOW_INSECURE_HTTP", raising=False)
    proxy, sink = servers
    _proxy_everything(monkeypatch, proxy)
    with pytest.raises(ConfigurationError, match="FI_ALLOW_INSECURE_HTTP=1"):
        _create_exporter(_config(kind, f"http://{REMOTE}:{sink.port}/v1/traces"))
    assert proxy.requests == [] and sink.requests == []


def test_an_https_remote_collector_asks_the_proxy_to_connect(servers, monkeypatch):
    proxy, sink = servers
    _proxy_everything(monkeypatch, proxy)
    exporter = _create_exporter(_config(ExporterType.OTLP_HTTP, f"https://{REMOTE}:{sink.port}/v1/traces"))
    _export_one_span(exporter)
    assert proxy.requests and {method for method, _, _ in proxy.requests} == {"CONNECT"}
    assert sink.requests == []


class _Counter:
    """A TCP listener that counts the bytes each connection sends and answers none."""

    def __init__(self) -> None:
        self.received = bytearray()
        self._listener = socket.create_server(("127.0.0.1", 0))
        self.port = self._listener.getsockname()[1]
        self._stop = False
        threading.Thread(target=self._accept, daemon=True).start()

    def _accept(self) -> None:
        while not self._stop:
            try:
                connection, _ = self._listener.accept()
            except OSError:
                return
            threading.Thread(target=self._read, args=(connection,), daemon=True).start()

    def _read(self, connection: socket.socket) -> None:
        connection.settimeout(0.2)
        with connection:
            for _ in range(15):
                try:
                    chunk = connection.recv(65536)
                except socket.timeout:
                    continue
                except OSError:
                    return
                if not chunk:
                    return
                self.received += chunk

    def close(self) -> None:
        self._stop = True
        self._listener.close()


_GRPC_SCRIPT = textwrap.dedent(
    """
    import sys
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from fi.evals.otel._tracer_factories import _create_exporter
    from fi.evals.otel.config import ExporterConfig, ExporterType

    exporter = _create_exporter(ExporterConfig(
        type=ExporterType.OTLP_GRPC, endpoint=sys.argv[1], insecure=True, timeout_ms=2000,
        headers={"x-api-key": "run-key-not-a-secret"},
    ))
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    provider.get_tracer("t").start_span("s").end()
    provider.shutdown()
    """
)


def _export_over_grpc(endpoint: str) -> subprocess.CompletedProcess:
    pytest.importorskip("opentelemetry.exporter.otlp.proto.grpc.trace_exporter")
    env = {k: v for k, v in os.environ.items() if k.lower() not in ("grpc_proxy", "http_proxy", "https_proxy", "no_proxy",
                                                                 "fi_base_url", "fi_traces_url", "fi_grpc_url")}
    # The collector here is not a Future AGI host: a loopback FI_BASE_URL from the fixtures would name it as one.
    env["PYTHONPATH"] = os.pathsep.join([str(PYTHON), *[p for p in sys.path if p]])
    env["GRPC_DNS_RESOLVER"] = "native"  # a name only the system resolver answers (app.localhost) is dialed directly
    return subprocess.run([sys.executable, "-c", _GRPC_SCRIPT, endpoint], env=env | _PROXY_ENV, timeout=60,
                          capture_output=True)


_PROXY_ENV: dict[str, str] = {}


@pytest.fixture(name="grpc_proxy")
def grpc_proxy_fixture():
    proxy, collector = _Counter(), _Counter()
    _PROXY_ENV.clear()
    _PROXY_ENV.update(grpc_proxy=f"http://127.0.0.1:{proxy.port}", http_proxy=f"http://127.0.0.1:{proxy.port}")
    yield proxy, collector
    proxy.close()
    collector.close()
    _PROXY_ENV.clear()


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost"])
def test_a_loopback_grpc_collector_gets_the_connection_and_the_proxy_no_bytes(grpc_proxy, host):
    proxy, collector = grpc_proxy
    _export_over_grpc(f"{host}:{collector.port}")
    assert bytes(proxy.received) == b""
    assert collector.received.startswith(b"PRI * HTTP/2.0")


def test_a_remote_plain_grpc_collector_that_gets_keys_is_reached_directly_when_opted_in(grpc_proxy, monkeypatch):
    """The channel the SDK builds for a plain gRPC export that carries keys has proxies off (``grpc.enable_http_proxy=0``):
    the opt-in allows it, and ``grpc_proxy`` / ``http_proxy`` do not route it."""
    proxy, collector = grpc_proxy
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    # app.localhost is not loopback by the written-host rule, and the system resolver answers it with 127.0.0.1
    _export_over_grpc(f"app.localhost:{collector.port}")
    assert bytes(proxy.received) == b""
    assert collector.received.startswith(b"PRI * HTTP/2.0")


def test_a_remote_plain_grpc_collector_that_gets_keys_is_refused_without_the_opt_in(grpc_proxy, monkeypatch):
    proxy, collector = grpc_proxy
    monkeypatch.delenv("FI_ALLOW_INSECURE_HTTP", raising=False)
    done = _export_over_grpc(f"{REMOTE}:{collector.port}")
    assert done.returncode != 0 and b"FI_ALLOW_INSECURE_HTTP=1" in done.stderr
    assert bytes(proxy.received) == b"" and collector.received == b""
