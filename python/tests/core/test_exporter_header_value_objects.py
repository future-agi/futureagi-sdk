"""Exporter header names and values that are ``str`` or ``bytes`` subclasses (or other objects) are read once into
plain ``str``/``bytes``: the key checks judge the text that is sent.

The checks read a value with ``str(value)``; ``requests``/``http.client`` and gRPC send ``value.encode()`` or the
``str`` content. A subclass whose ``__str__`` gives other text than its content, or whose ``encode`` gives other bytes,
is the case covered here. Host names resolve to loopback (the ``rig`` helper); the listeners count connections and
marker bytes at the target and at a ``CONNECT``-aware proxy sink. The gRPC case runs in a child process with
``grpc_proxy`` set to a ``CONNECT``-aware loopback sink.
"""

import os
import subprocess
import sys
import textwrap
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


class StrV(str):
    """Holds the key; ``str()`` of it gives harmless text."""

    def __str__(self):
        return "blue"


class StrE(str):
    """Holds harmless text; ``encode()`` of it gives the key from the environment."""

    def encode(self, *args, **kwargs):
        return os.environ["FI_API_KEY"].encode()


def build_and_send(headers, base, kind):
    from fi.evals.otel._tracer_factories import _create_exporter

    try:
        exporter = _create_exporter(ExporterConfig(type=kind, endpoint=f"{base}/v1/traces", headers=headers))
        if exporter is not None:
            export_one_span(exporter)
    except Exception as error:  # noqa: BLE001 - a refusal is one of the allowed outcomes
        return error
    return None


@pytest.mark.parametrize("make", [lambda: StrV(MARKER), lambda: StrE("blue")], ids=["str-hides-key", "encode-gives-key"])
@pytest.mark.parametrize("wrap", [dict, list], ids=["dict", "pairs"])
@pytest.mark.parametrize("kind", HTTP_TYPES)
def test_a_str_subclass_value_sends_no_key_to_a_plain_remote_collector(rig, monkeypatch, kind, make, wrap):
    monkeypatch.setenv("FI_API_KEY", MARKER)
    headers = wrap([("X-Fi-Token", make())]) if wrap is list else {"X-Fi-Token": make()}
    build_and_send(headers, f"http://collector.example.test:{rig.target.port}", kind)
    assert rig.bytes() == 0, (rig.connections(), rig.bytes())


def test_a_plain_dict_of_plain_text_is_handed_on_as_the_same_object(rig):
    from fi.evals.otel._tracer_factories import _create_exporter

    headers = {"X-Team": "blue"}
    exporter = _create_exporter(ExporterConfig(type=ExporterType.OTLP_HTTP,
                                               endpoint=f"http://collector.example.test:{rig.target.port}/v1/traces",
                                               headers=headers))
    assert exporter._headers is headers


GRPC_CHILD = textwrap.dedent(
    """
    import os, sys
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from fi.evals.otel._tracer_factories import _create_exporter
    from fi.evals.otel.config import ExporterConfig, ExporterType

    marker, which = sys.argv[2], sys.argv[3]
    os.environ["FI_API_KEY"] = marker

    class StrV(str):
        def __str__(self):
            return "blue"

    class StrE(str):
        def encode(self, *args, **kwargs):
            return marker.encode()

    value = StrV(marker) if which == "str" else StrE("blue")
    try:
        exporter = _create_exporter(ExporterConfig(type=ExporterType.OTLP_GRPC, endpoint=sys.argv[1], insecure=True,
                                                   timeout_ms=2000, headers={"x-fi-token": value}))
    except Exception as error:
        print("refused", type(error).__name__)
        sys.exit(0)
    if exporter is not None:
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        provider.get_tracer("t").start_span("s").end()
        provider.shutdown()
    """
)


@pytest.mark.parametrize("which", ["str", "encode"])
def test_a_str_subclass_value_sends_no_key_through_a_grpc_proxy(which):
    pytest.importorskip("opentelemetry.exporter.otlp.proto.grpc.trace_exporter")
    proxy = Sink(True)
    try:
        env = {k: v for k, v in os.environ.items() if not k.upper().startswith(("FI_", "OTEL_", "GRPC_", "HTTP_",
                                                                                 "HTTPS_", "ALL_", "NO_"))}
        env.update(PYTHONPATH=str(PYTHON), grpc_proxy=f"http://127.0.0.1:{proxy.port}",
                   http_proxy=f"http://127.0.0.1:{proxy.port}")
        done = subprocess.run([sys.executable, "-c", GRPC_CHILD, "collector.example.test:4317", MARKER, which],
                              env=env, timeout=60, capture_output=True, cwd=str(PYTHON))
        assert proxy.marker_bytes == 0, (proxy.connections, proxy.marker_bytes, done.stdout[-500:], done.stderr[-2000:])
    finally:
        proxy.close()
