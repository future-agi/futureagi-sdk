"""Exporter headers held in a ``dict`` subclass are read once into a plain ``dict``: the key checks, the pinning and the
exporter all receive that copy, so the values the checks judge are the values that reach the wire.

A ``requests`` session reads a mapping through its keys and ``__getitem__`` (the ``Mapping`` protocol), while
``dict.items()`` of a subclass returns the stored values; a subclass whose ``__getitem__`` gives another value than
the one stored is the case covered here. Host names resolve to loopback (the ``rig`` helper); the listeners count
connections and marker bytes at the target, at a ``CONNECT``-aware proxy sink and at the redirect targets. The gRPC
case runs in a child process with ``grpc_proxy`` set to a ``CONNECT``-aware loopback sink.
"""

import os
import subprocess
import sys
import textwrap
from collections.abc import Mapping
from pathlib import Path

import pytest

from fi.evals.otel.config import ExporterConfig
from fi.evals.otel.types import ExporterType
from tests.core.test_exporter_headers_are_read_once import export_one_span
from tests.experiments.unit.oracle_probe import Sink
from tests.experiments.unit.test_header_key_senders import MARKER, rig  # noqa: F401

pytest.importorskip("opentelemetry.sdk.trace")

HTTP_TYPES = [ExporterType.OTLP_HTTP, ExporterType.ARIZE, ExporterType.PHOENIX, ExporterType.LANGFUSE]
PYTHON = Path(__file__).resolve().parents[2]


def collector(sink):
    return f"http://collector.example.test:{sink.port}"


class LazyDict(dict):
    """Stores ``env:NAME`` and gives the value of ``NAME`` from the environment when a header is read by name."""

    def __getitem__(self, name):
        value = dict.__getitem__(self, name)
        if isinstance(value, str) and value.startswith("env:"):
            return os.environ[value[4:]]
        return value


class LazyMapping(Mapping):
    """The same placeholder resolution behind the ``Mapping`` protocol alone."""

    def __init__(self, stored):
        self.stored = stored

    def __iter__(self):
        return iter(self.stored)

    def __len__(self):
        return len(self.stored)

    def __getitem__(self, name):
        return LazyDict(self.stored)[name]


class Shifting(dict):
    """Holds ``X-Team: blue``; the one method named by ``method`` answers with the key once it has been called
    ``clean`` times."""

    def __init__(self, method, clean):
        super().__init__({"X-Team": "blue"})
        self.method, self.clean, self.reads = method, clean, 0

    def _keyed(self, method):
        if method != self.method:
            return False
        self.reads += 1
        return self.reads > self.clean

    def keys(self):
        return ["X-Api-Key"] if self._keyed("keys") else dict.keys(self)

    def __iter__(self):
        return iter(["X-Api-Key"]) if self._keyed("iter") else dict.__iter__(self)

    def items(self):
        return [("X-Api-Key", MARKER)] if self._keyed("items") else dict.items(self)

    def get(self, name, default=None):
        return MARKER if self._keyed("get") else dict.get(self, name, default)

    def __getitem__(self, name):
        if self._keyed("getitem") or name == "X-Api-Key":
            return MARKER
        return dict.__getitem__(self, name)


def build_and_send(headers, base, kind):
    from fi.evals.otel._tracer_factories import _create_exporter

    try:
        exporter = _create_exporter(ExporterConfig(type=kind, endpoint=f"{base}/v1/traces", headers=headers))
        if exporter is not None:
            export_one_span(exporter)
    except Exception as error:  # noqa: BLE001 - a refusal is one of the allowed outcomes
        return error
    return None


def env_marker(monkeypatch):
    monkeypatch.setenv("FI_API_KEY", MARKER)


@pytest.mark.parametrize("kind", HTTP_TYPES + [ExporterType.FUTUREAGI])
def test_a_dict_subclass_that_resolves_a_key_on_read_is_refused_for_a_plain_remote_collector(rig, monkeypatch, kind):
    env_marker(monkeypatch)
    from fi.errors import ConfigurationError

    error = build_and_send(LazyDict({"X-Fi-Token": "env:FI_API_KEY"}), collector(rig.target), kind)
    assert (rig.connections(), rig.bytes()) == (0, 0)
    assert isinstance(error, ConfigurationError), error


@pytest.mark.parametrize("make", [lambda: {"X-Fi-Token": MARKER}, lambda: LazyMapping({"X-Fi-Token": "env:FI_API_KEY"})],
                         ids=["plain dict", "Mapping"])
@pytest.mark.parametrize("kind", HTTP_TYPES + [ExporterType.FUTUREAGI])
def test_the_plain_dict_and_mapping_controls_are_refused(rig, monkeypatch, kind, make):
    env_marker(monkeypatch)
    from fi.errors import ConfigurationError

    error = build_and_send(make(), collector(rig.target), kind)
    assert (rig.connections(), rig.bytes()) == (0, 0)
    assert isinstance(error, ConfigurationError), error


@pytest.mark.parametrize("clean", range(0, 9))
@pytest.mark.parametrize("method", ["keys", "iter", "get", "items", "getitem"])
@pytest.mark.parametrize("kind", HTTP_TYPES)
def test_a_dict_subclass_keyed_on_a_later_read_sends_no_key_to_a_plain_remote_collector(rig, monkeypatch, kind, method,
                                                                                       clean):
    env_marker(monkeypatch)
    build_and_send(Shifting(method, clean), collector(rig.target), kind)
    assert rig.bytes() == 0


def wire_headers(sink):
    """The header lines of the first request a listener received, names in lower case."""
    blob = b"".join(sink.data)
    head = blob.split(b"\r\n\r\n", 1)[0].decode("latin-1").split("\r\n")[1:]
    return {name.strip().lower(): value.strip() for name, _, value in (line.partition(":") for line in head)}


@pytest.mark.parametrize("kind", HTTP_TYPES + [ExporterType.FUTUREAGI])
def test_the_checks_the_pinning_and_the_exporter_receive_one_plain_copy_that_is_the_one_sent(rig, monkeypatch,
                                                                                         kind):
    env_marker(monkeypatch)
    import fi._core.http_security as http_security
    import fi._otlp_headers as otlp_headers
    from fi._core.proxy_routing import header_pairs

    judged, handed = [], []
    check, pin = http_security.require_secure_credential_headers, otlp_headers.pin_headers

    def judging(url, headers, **kwargs):
        judged.append((type(headers), [(str(n), str(v)) for n, v in header_pairs(headers)]))
        return check(url, headers, **kwargs)

    def pinning(exporter, headers):
        handed.append(("pin", type(headers)))
        return pin(exporter, headers)

    monkeypatch.setattr(http_security, "require_secure_credential_headers", judging)
    monkeypatch.setattr(otlp_headers, "pin_headers", pinning)
    from fi.evals.otel._tracer_factories import _create_exporter

    endpoint = f"http://localhost:{rig.target.port}/v1/traces"
    exporter = _create_exporter(ExporterConfig(type=kind, endpoint=endpoint,
                                               headers=LazyDict({"X-Fi-Token": "env:FI_API_KEY", "X-Team": "blue"})))
    handed.append(("exporter", type(exporter._headers)))
    export_one_span(exporter)

    sent = wire_headers(rig.target)
    assert judged
    for _, pairs in judged:
        for name, value in pairs:
            assert sent.get(name.lower()) == value, (name, value, sent.get(name.lower()))
    assert rig.target.marker_bytes > 0 and rig.proxy.connections == 0
    assert all(kind_ is dict for kind_, _ in judged), judged
    assert all(kind_ is dict for _, kind_ in handed), handed


def test_a_plain_dict_is_handed_on_as_the_same_object(rig, monkeypatch):
    import fi._core.http_security as http_security

    headers = {"X-Team": "blue"}
    seen = []
    check = http_security.require_secure_credential_headers
    monkeypatch.setattr(http_security, "require_secure_credential_headers",
                        lambda url, given, **kwargs: (seen.append(given), check(url, given, **kwargs))[1])
    from fi.evals.otel._tracer_factories import _create_exporter

    exporter = _create_exporter(ExporterConfig(type=ExporterType.OTLP_HTTP, endpoint=f"{collector(rig.target)}/v1/traces",
                                               headers=headers))
    assert seen and all(given is headers for given in seen)
    assert exporter._headers is headers


GRPC_CHILD = textwrap.dedent(
    """
    import sys
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from fi.evals.otel._tracer_factories import _create_exporter
    from fi.evals.otel.config import ExporterConfig, ExporterType

    marker, clean = sys.argv[2], int(sys.argv[3])

    class FlipItems(dict):
        reads = 0

        def items(self):
            FlipItems.reads += 1
            return [("x-api-key", marker)] if FlipItems.reads > clean else dict.items(self)

    exporter = _create_exporter(ExporterConfig(type=ExporterType.OTLP_GRPC, endpoint=sys.argv[1], insecure=True,
                                               timeout_ms=2000, headers=FlipItems({"x-team": "blue"})))
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    provider.get_tracer("t").start_span("s").end()
    provider.shutdown()
    """
)


@pytest.mark.parametrize("clean", range(0, 7))
def test_a_dict_subclass_whose_items_change_sends_no_key_through_a_grpc_proxy(clean):
    pytest.importorskip("opentelemetry.exporter.otlp.proto.grpc.trace_exporter")
    proxy = Sink(True)
    try:
        env = {k: v for k, v in os.environ.items() if not k.upper().startswith(("FI_", "OTEL_", "GRPC_", "HTTP_",
                                                                                 "HTTPS_", "ALL_", "NO_"))}
        env.update(PYTHONPATH=str(PYTHON), grpc_proxy=f"http://127.0.0.1:{proxy.port}",
                   http_proxy=f"http://127.0.0.1:{proxy.port}")
        done = subprocess.run([sys.executable, "-c", GRPC_CHILD, "collector.example.test:4317", MARKER, str(clean)],
                              env=env, timeout=60, capture_output=True, cwd=str(PYTHON))
        assert proxy.marker_bytes == 0, (proxy.connections, done.stderr[-2000:])
    finally:
        proxy.close()
