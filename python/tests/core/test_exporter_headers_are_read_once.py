"""An exporter's headers are read once: the key check and the exporter see the same snapshot, whatever the caller's
mapping (or ``dict`` subclass) returns on a later read, and an iterator of pairs is kept. The gRPC cases run in a child
process whose ``grpc_proxy`` names a ``CONNECT``-aware loopback sink that counts the marker."""

import pytest

from fi.evals.otel.config import ExporterConfig
from fi.evals.otel.types import ExporterType
from tests.experiments.unit.test_header_key_senders import MARKER, remote, rig  # noqa: F401  (fixture)

pytest.importorskip("opentelemetry.sdk.trace")
from collections.abc import Mapping  # noqa: E402


class ReadTwice(Mapping):
    """Holds a harmless header for its first ``clean`` reads and the key on every later read."""

    def __init__(self, clean=1):
        self.clean = clean
        self.reads = 0

    def __iter__(self):
        self.reads += 1
        return iter(["X-Team"] if self.reads <= self.clean else ["X-Api-Key"])

    def __getitem__(self, name):
        return "blue" if name == "X-Team" else MARKER

    def __len__(self):
        return 1


class ReadTwiceDict(dict):
    """A ``dict`` subclass that holds a harmless header and lists the key once its names have been read ``clean``
    times, by ``keys()``, ``items()`` or iteration."""

    def __init__(self, clean=1):
        super().__init__({"X-Team": "blue"})
        self.clean = clean
        self.reads = 0

    def _keyed(self):
        self.reads += 1
        return self.reads > self.clean

    def __iter__(self):
        return iter(["X-Api-Key"]) if self._keyed() else dict.__iter__(self)

    def keys(self):
        return ["X-Api-Key"] if self._keyed() else dict.keys(self)

    def items(self):
        return [("X-Api-Key", MARKER)] if self._keyed() else dict.items(self)

    def __getitem__(self, name):
        return MARKER if name == "X-Api-Key" else dict.__getitem__(self, name)


TYPES = [ExporterType.OTLP_HTTP, ExporterType.ARIZE, ExporterType.PHOENIX, ExporterType.LANGFUSE]
WITH_FUTUREAGI = TYPES + [ExporterType.FUTUREAGI]


def export_one_span(exporter):
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor

    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    with provider.get_tracer("t").start_as_current_span("s"):
        pass
    provider.shutdown()


def build_and_send(headers, base, kind):
    from fi.evals.otel._tracer_factories import _create_exporter

    try:
        exporter = _create_exporter(ExporterConfig(type=kind, endpoint=f"{base}/v1/traces", headers=headers))
        if exporter is not None:
            export_one_span(exporter)
    except Exception as error:  # noqa: BLE001 - a refusal is one of the allowed outcomes
        return error
    return None


CLEAN_READS = range(1, 9)


@pytest.mark.parametrize("clean", CLEAN_READS)
@pytest.mark.parametrize("kind", TYPES)
def test_a_mapping_that_changes_between_reads_sends_no_key_to_a_non_loopback_host(rig, monkeypatch, kind, clean):
    build_and_send(ReadTwice(clean), remote(rig.target), kind)
    assert rig.bytes() == 0


@pytest.mark.parametrize("clean", CLEAN_READS)
@pytest.mark.parametrize("kind", TYPES)
def test_the_same_mapping_reaches_no_proxy(rig, monkeypatch, kind, clean):
    from tests.experiments.unit.test_header_key_senders import proxied

    proxied(rig, monkeypatch)
    build_and_send(ReadTwice(clean), remote(rig.target), kind)
    assert rig.bytes() == 0


@pytest.mark.parametrize("kind", TYPES)
def test_an_iterator_of_pairs_is_kept(rig, monkeypatch, kind):
    from fi.errors import ConfigurationError

    error = build_and_send(iter([("X-Api-Key", MARKER)]), remote(rig.target), kind)
    assert isinstance(error, ConfigurationError) and error.code == "insecure_http_origin", error
    assert rig.connections() == 0 and rig.bytes() == 0


@pytest.mark.parametrize("kind", WITH_FUTUREAGI)
def test_a_snapshot_of_a_mapping_is_sent_to_loopback(rig, monkeypatch, kind):
    build_and_send({"X-Api-Key": MARKER}, f"http://localhost:{rig.target.port}", kind)
    assert rig.target.marker_bytes > 0


@pytest.mark.parametrize("clean", CLEAN_READS)
@pytest.mark.parametrize("kind", WITH_FUTUREAGI)
def test_a_dict_subclass_that_changes_between_reads_sends_no_key_to_a_non_loopback_host(rig, monkeypatch, kind, clean):
    build_and_send(ReadTwiceDict(clean), remote(rig.target), kind)
    assert rig.bytes() == 0


@pytest.mark.parametrize("clean", CLEAN_READS)
@pytest.mark.parametrize("kind", WITH_FUTUREAGI)
def test_the_same_dict_subclass_reaches_no_proxy(rig, monkeypatch, kind, clean):
    from tests.experiments.unit.test_header_key_senders import proxied

    proxied(rig, monkeypatch)
    build_and_send(ReadTwiceDict(clean), remote(rig.target), kind)
    assert rig.bytes() == 0


@pytest.mark.parametrize("kind", WITH_FUTUREAGI)
def test_a_dict_subclass_holding_the_key_is_sent_to_loopback(rig, monkeypatch, kind):
    build_and_send(ReadTwiceDict(0), f"http://localhost:{rig.target.port}", kind)
    assert rig.target.marker_bytes > 0


GRPC_CHILD = """
import sys
from fi.evals.otel._tracer_factories import _create_exporter
from tests.core.test_exporter_headers_are_read_once import ExporterConfig, ExporterType, ReadTwice, ReadTwiceDict
from tests.core.test_exporter_headers_are_read_once import export_one_span

headers = {"mapping": ReadTwice, "dict subclass": ReadTwiceDict}[sys.argv[2]](int(sys.argv[3]))
export_one_span(_create_exporter(ExporterConfig(type=ExporterType.OTLP_GRPC, endpoint=sys.argv[1], insecure=True,
                                                timeout_ms=2000, headers=headers)))
"""


@pytest.mark.parametrize("clean", range(1, 7))
@pytest.mark.parametrize("form", ["mapping", "dict subclass"])
def test_a_grpc_exporter_sends_no_key_read_after_the_snapshot_through_a_proxy(form, clean):
    import os
    import subprocess
    import sys
    from pathlib import Path

    from tests.experiments.unit.oracle_probe import Sink

    pytest.importorskip("opentelemetry.exporter.otlp.proto.grpc.trace_exporter")
    python = Path(__file__).resolve().parents[2]
    proxy = Sink(True)
    try:
        env = {k: v for k, v in os.environ.items()
               if not k.upper().startswith(("FI_", "OTEL_", "GRPC_", "HTTP_", "HTTPS_", "ALL_", "NO_"))}
        env.update(PYTHONPATH=str(python), grpc_proxy=f"http://127.0.0.1:{proxy.port}")
        done = subprocess.run([sys.executable, "-c", GRPC_CHILD, "collector.example.test:4317", form, str(clean)],
                              env=env, timeout=60, capture_output=True, cwd=str(python))
        assert proxy.marker_bytes == 0, (proxy.connections, done.stderr[-2000:])
    finally:
        proxy.close()
