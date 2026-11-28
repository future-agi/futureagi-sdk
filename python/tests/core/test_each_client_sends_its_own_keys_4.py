"""Two clients built from the same exporter preset (``fi.evals.otel.get_exporter_preset``) each send their own keys.

Each tenant builds its exporter configuration from the ``arize`` preset, points it at its own loopback collector and
adds its own key header. The clients are used one after another and from 8 threads at once; each collector counts,
per request, the bytes of each tenant's key that reach it. The keys are derived at runtime from the shared test marker.
"""

from __future__ import annotations

import dataclasses
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

pytest.importorskip("opentelemetry.sdk.trace")
pytest.importorskip("opentelemetry.exporter.otlp.proto.http.trace_exporter")

from fi.evals.otel.config import get_exporter_preset  # noqa: E402
from tests.experiments.unit.oracle_probe import KEY  # noqa: E402

TENANTS = ("north", "south")
ENV = ("FI_ALLOW_INSECURE_HTTP", "HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy",
       "OTEL_EXPORTER_OTLP_HEADERS", "OTEL_EXPORTER_OTLP_TRACES_HEADERS", "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
       "OTEL_EXPORTER_OTLP_ENDPOINT")


def tenant_key(tenant: str) -> str:
    return f"{tenant}-{KEY.decode()}-{tenant}"


class Collector:
    """A loopback OTLP HTTP collector that keeps the raw header and body bytes of each request."""

    def __init__(self) -> None:
        requests = self.requests = []
        lock = threading.Lock()

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802 - the http.server hook name
                body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
                with lock:
                    requests.append(str(self.headers).encode("latin-1") + body)
                self.send_response(200)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def counts(self, tenant: str) -> list:
        """The bytes of ``tenant``'s key in each request this collector received."""
        needle = tenant_key(tenant).encode()
        return [request.count(needle) * len(needle) for request in list(self.requests)]

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def collectors(monkeypatch):
    for name in ENV:
        monkeypatch.delenv(name, raising=False)
    sinks = {tenant: Collector() for tenant in TENANTS}
    yield sinks
    for sink in sinks.values():
        sink.close()


class ReplacedEndpointClient:
    """A client that copies the preset with its own endpoint and adds its key header."""

    def __init__(self, tenant: str, port: int) -> None:
        self.config = dataclasses.replace(
            get_exporter_preset("arize"), endpoint=f"http://127.0.0.1:{port}/v1/traces", timeout_ms=5000
        )
        self.config.headers["api_key"] = tenant_key(tenant)

    def send(self) -> None:
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor

        from fi.evals.otel._tracer_factories import _create_exporter

        exporter = _create_exporter(self.config)
        assert exporter is not None
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        provider.get_tracer("t").start_span("s").end()
        provider.shutdown()


class SetEndpointClient(ReplacedEndpointClient):
    """A client that sets the endpoint and key header on the configuration the preset returns."""

    def __init__(self, tenant: str, port: int) -> None:
        self.config = get_exporter_preset("arize")
        self.config.endpoint = f"http://127.0.0.1:{port}/v1/traces"
        self.config.timeout_ms = 5000
        self.config.headers["api_key"] = tenant_key(tenant)


def other(tenant: str) -> str:
    return TENANTS[1 - TENANTS.index(tenant)]


def report(collectors) -> dict:
    return {
        sink_tenant: {key_tenant: sink.counts(key_tenant) for key_tenant in TENANTS}
        for sink_tenant, sink in collectors.items()
    }


def assert_own_keys_only(collectors, expected_requests: int) -> None:
    seen = report(collectors)
    for tenant, sink in collectors.items():
        own = sink.counts(tenant)
        foreign = sink.counts(other(tenant))
        assert sum(foreign) == 0, f"{tenant} collector got {sum(foreign)} bytes of the other key: {seen}"
        assert len(own) == expected_requests and all(own), f"{tenant} collector requests: {seen}"


CLIENTS = [ReplacedEndpointClient, SetEndpointClient]


@pytest.mark.parametrize("client_class", CLIENTS)
def test_clients_used_one_after_another_send_their_own_keys(collectors, client_class):
    clients = {tenant: client_class(tenant, collectors[tenant].port) for tenant in TENANTS}
    for _ in range(2):
        for tenant in TENANTS:
            clients[tenant].send()
    assert_own_keys_only(collectors, 2)


@pytest.mark.parametrize("client_class", CLIENTS)
def test_clients_used_from_eight_threads_send_their_own_keys(collectors, client_class):
    threads_per_tenant = 4
    built = threading.Barrier(2 * threads_per_tenant)
    errors = []

    def run(tenant):
        try:
            client = client_class(tenant, collectors[tenant].port)
            built.wait(timeout=30)
            for _ in range(3):
                client.send()
        except Exception as error:  # noqa: BLE001 - reported below
            errors.append(error)

    threads = [threading.Thread(target=run, args=(tenant,)) for tenant in TENANTS for _ in range(threads_per_tenant)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    assert errors == []
    assert_own_keys_only(collectors, 3 * threads_per_tenant)
