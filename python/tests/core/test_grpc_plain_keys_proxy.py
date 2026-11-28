"""A plain gRPC channel that carries the SDK's keys from the environment is not routed through a proxy. The
target is a self-managed hostname that resolves to loopback through a preloaded resolver, configured by FI_GRPC_URL,
FI_BASE_URL or FI_TRACES_URL, with no headers on the exporter configuration."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.core._localhost_dial import KEY, PROXY_ENV, SECRET, Sink, proxy, target  # noqa: F401
from tests.core.test_localhost_direct_dial_grpc import SHIM, shim_compiler

CHILD = r"""
import sys
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from fi.evals.otel._tracer_factories import _create_exporter
from fi.evals.otel.tracer import ExporterConfig, ExporterType

memory = InMemorySpanExporter()
provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(memory))
provider.get_tracer("t").start_span("s").end()
exporter = _create_exporter(ExporterConfig(type=ExporterType.OTLP_GRPC, endpoint=sys.argv[1], insecure=True,
                                           headers={}, timeout_ms=2000))
exporter.export(memory.get_finished_spans())
"""

FORMS = {
    "FI_GRPC_URL": lambda port: f"loop.test:{port}",
    "FI_BASE_URL": lambda port: f"http://loop.test:{port}",
    "FI_TRACES_URL": lambda port: f"http://loop.test:{port}/v1/traces",
}
PROXY_VARIABLES = ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "grpc_proxy", "GRPC_PROXY", "ALL_PROXY", "all_proxy")


@pytest.fixture(scope="module")
def shim_library(tmp_path_factory) -> Path:
    command = shim_compiler()
    pytest.importorskip("opentelemetry.exporter.otlp.proto.grpc.trace_exporter")
    directory = tmp_path_factory.mktemp("plain_keys_shim")
    (directory / "shim.c").write_text(SHIM)
    library = directory / "shim.so"
    subprocess.run([*command, "-shared", "-fPIC", "-o", str(library), str(directory / "shim.c"), "-ldl"], check=True)
    return library


@pytest.mark.parametrize("variable", PROXY_VARIABLES)
@pytest.mark.parametrize("setting", sorted(FORMS))
def test_a_plain_self_hosted_channel_with_environment_keys_bypasses_the_proxy(
        shim_library, tmp_path, target, proxy, setting, variable):
    env = {k: v for k, v in os.environ.items() if k not in PROXY_ENV and not k.startswith(("FI_", "OTEL_"))}
    env.update(LD_PRELOAD=str(shim_library), GRPC_DNS_RESOLVER="native", FI_API_KEY=KEY, FI_SECRET_KEY=SECRET,
               FI_ALLOW_INSECURE_HTTP="1", PYTHONPATH=str(Path(__file__).resolve().parents[2]),
               **{setting: FORMS[setting](target.port), variable: f"http://127.0.0.1:{proxy.port}"})
    subprocess.run([sys.executable, "-c", CHILD, f"loop.test:{target.port}"], env=env, timeout=60,
                   capture_output=True, cwd=str(tmp_path))
    assert proxy.connections == 0, proxy.first_lines
    assert proxy.marker_bytes == 0
    assert target.connections >= 1


@pytest.mark.parametrize("variable", ("http_proxy", "grpc_proxy"))
def test_a_plain_channel_with_an_environment_authorization_header_bypasses_the_proxy(
        shim_library, tmp_path, target, proxy, variable):
    env = {k: v for k, v in os.environ.items() if k not in PROXY_ENV and not k.startswith(("FI_", "OTEL_"))}
    env.update(LD_PRELOAD=str(shim_library), GRPC_DNS_RESOLVER="native", FI_ALLOW_INSECURE_HTTP="1",
               OTEL_EXPORTER_OTLP_HEADERS=f"authorization=Bearer {KEY}",
               PYTHONPATH=str(Path(__file__).resolve().parents[2]), **{variable: f"http://127.0.0.1:{proxy.port}"})
    subprocess.run([sys.executable, "-c", CHILD, f"loop.test:{target.port}"], env=env, timeout=60,
                   capture_output=True, cwd=str(tmp_path))
    assert proxy.connections == 0, proxy.first_lines
    assert proxy.marker_bytes == 0
