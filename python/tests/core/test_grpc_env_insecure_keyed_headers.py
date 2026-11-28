"""A gRPC exporter with ``insecure`` unset reads ``OTEL_EXPORTER_OTLP_TRACES_INSECURE`` or
``OTEL_EXPORTER_OTLP_INSECURE``: with ``true`` it opens a channel without TLS. The SDK judges the channel the exporter
opens, so headers that hold a key (``X-Fi-Token: <FI_API_KEY>`` or ``Authorization: Bearer <FI_API_KEY>``) bound for a
remote collector (not Future AGI, not loopback) get no plain channel without ``FI_ALLOW_INSECURE_HTTP=1``: the
exporter is refused, or it opens TLS, and the mode the SDK judged is the mode the exporter holds (``_insecure``).

gRPC resolves names in C, so each case runs in a child process with a preloaded resolver library that answers
``collector.example.test`` with 127.0.0.1 (the shim of ``test_localhost_direct_dial_grpc``). The target listener (T)
answers the HTTP/2 preface; the proxy listener (P) answers a ``CONNECT`` and reads the tunnel. Both count the plain
HTTP/2 connections and the bytes of the key, a fresh random value per case.
"""

from __future__ import annotations

import json
import os
import secrets
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest

from tests.core._localhost_dial import PROXY_ENV
from tests.core.test_localhost_direct_dial_grpc import SHIM, shim_compiler
from tests.experiments.unit.oracle_probe import Sink

PYTHON = Path(__file__).resolve().parents[2]
COLLECTOR = "collector.example.test"
PREFACE = b"PRI * HTTP/2.0"
ENV_SETTINGS = ("OTEL_EXPORTER_OTLP_TRACES_INSECURE", "OTEL_EXPORTER_OTLP_INSECURE")
CONTAINERS = ("dict", "mapping", "lazy_dict", "ordered_dict", "mapping_proxy", "pairs", "str_subclass_value",
              "authorization")
PATHS = ("factory", "setup_tracing")
PROXY_SETTINGS = ("grpc_proxy", "GRPC_PROXY", "https_proxy", "HTTPS_PROXY", "http_proxy", "HTTP_PROXY", "all_proxy",
                  "ALL_PROXY")

CHILD = textwrap.dedent(
    r'''
    import json, os, sys, types
    from collections import OrderedDict
    from collections.abc import Mapping

    path, container, endpoint = sys.argv[1], sys.argv[2], sys.argv[3]
    key = os.environ["FI_API_KEY"]

    class LazyDict(dict):
        """Stores ``env:NAME`` and gives the value of ``NAME`` when a header is read by name."""

        def __getitem__(self, name):
            value = dict.__getitem__(self, name)
            if isinstance(value, str) and value.startswith("env:"):
                return os.environ[value[4:]]
            return value

    class PlainMapping(Mapping):
        def __init__(self, stored):
            self.stored = stored

        def __iter__(self):
            return iter(self.stored)

        def __len__(self):
            return len(self.stored)

        def __getitem__(self, name):
            return self.stored[name]

    class Text(str):
        pass

    headers = {
        "dict": lambda: {"x-fi-token": key},
        "mapping": lambda: PlainMapping({"x-fi-token": key}),
        "lazy_dict": lambda: LazyDict({"x-fi-token": "env:FI_API_KEY"}),
        "ordered_dict": lambda: OrderedDict([("x-fi-token", key)]),
        "mapping_proxy": lambda: types.MappingProxyType({"x-fi-token": key}),
        "pairs": lambda: [("x-fi-token", key)],
        "str_subclass_value": lambda: {"x-fi-token": Text(key)},
        "authorization": lambda: {"authorization": "Bearer " + key},
    }[container]()

    import fi._core.http_security as http_security
    from opentelemetry.exporter.otlp.proto.grpc import trace_exporter

    judged, built = [], []
    check = http_security.require_secure_grpc_target

    def judging(endpoint_, headers_, *args, **kwargs):
        judged.append(bool(kwargs.get("insecure")))
        return check(endpoint_, headers_, *args, **kwargs)

    http_security.require_secure_grpc_target = judging
    original_init = trace_exporter.OTLPSpanExporter.__init__

    def recording_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        built.append(self)

    trace_exporter.OTLPSpanExporter.__init__ = recording_init

    from fi.evals.otel.config import ExporterConfig, TraceConfig
    from fi.evals.otel.types import ExporterType

    config = ExporterConfig(type=ExporterType.OTLP_GRPC, endpoint=endpoint, headers=headers, insecure=None,
                            timeout_ms=2000)
    result = {"refused": None, "code": None}
    try:
        if path == "factory":
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import SimpleSpanProcessor
            from fi.evals.otel._tracer_factories import _create_exporter

            exporter = _create_exporter(config)
            provider = TracerProvider()
            provider.add_span_processor(SimpleSpanProcessor(exporter))
            provider.get_tracer("t").start_span("s").end()
        else:
            from fi.evals.otel.tracer import setup_tracing

            provider = setup_tracing(TraceConfig(service_name="svc", exporters=[config]))
            provider.get_tracer("t").start_span("s").end()
            provider.force_flush(5000)
    except Exception as error:  # a refusal is one of the allowed outcomes
        result["refused"] = type(error).__name__
        result["code"] = getattr(error, "code", None)
    result["judged"] = judged
    result["insecure"] = [getattr(exporter_, "_insecure", None) for exporter_ in built]
    print("RESULT " + json.dumps(result), flush=True)
    os._exit(0)
    '''
)


@pytest.fixture(scope="module")
def shim_library(tmp_path_factory) -> Path:
    command = shim_compiler()
    pytest.importorskip("opentelemetry.exporter.otlp.proto.grpc.trace_exporter")
    directory = tmp_path_factory.mktemp("env_insecure_shim")
    source = SHIM.replace('if (node && strcmp(node, "loop.test") == 0) node = "127.0.0.1";',
                          'if (node && (strcmp(node, "loop.test") == 0 || strcmp(node, "%s") == 0)) node = "127.0.0.1";'
                          % COLLECTOR)
    assert COLLECTOR in source
    (directory / "shim.c").write_text(source)
    library = directory / "shim.so"
    subprocess.run([*command, "-shared", "-fPIC", "-o", str(library), str(directory / "shim.c"), "-ldl"], check=True)
    return library


@pytest.fixture()
def sinks():
    target, proxy = Sink(False), Sink(True)
    yield target, proxy
    target.close()
    proxy.close()


class Seen:
    def __init__(self, sink: Sink, key: str) -> None:
        blob = b"".join(sink.data)
        self.connections = sink.connections
        self.plain = blob.count(PREFACE)
        self.key_bytes = blob.count(key.encode()) * len(key)

    def __repr__(self) -> str:
        return f"connections={self.connections} plain_h2={self.plain} key_bytes={self.key_bytes}"


def run_case(shim_library: Path, tmp_path: Path, sinks, path: str, container: str, endpoint: str, extra: dict):
    target, proxy = sinks
    key = secrets.token_hex(16)
    env = {k: v for k, v in os.environ.items()
           if k not in PROXY_ENV and k not in PROXY_SETTINGS and not k.startswith(("FI_", "OTEL_", "GRPC_"))}
    preload = [str(shim_library)] + [p for p in os.environ.get("LD_PRELOAD", "").split(":") if p]
    env.update(LD_PRELOAD=":".join(preload), GRPC_DNS_RESOLVER="native", FI_API_KEY=key,
               FI_LOGIN_FILE=str(tmp_path / "no-login.json"), PYTHONPATH=str(PYTHON), **extra)
    done = subprocess.run([sys.executable, "-c", CHILD, path, container, endpoint], env=env, timeout=120,
                          capture_output=True, cwd=str(tmp_path))
    time.sleep(0.3)
    lines = [line for line in done.stdout.decode(errors="replace").splitlines() if line.startswith("RESULT ")]
    assert lines, done.stderr.decode(errors="replace")[-3000:]
    return json.loads(lines[-1][len("RESULT "):]), Seen(target, key), Seen(proxy, key)


def proxy_env(proxy: Sink) -> dict:
    return {name: f"http://127.0.0.1:{proxy.port}" for name in PROXY_SETTINGS}


def assert_refused_or_tls(result: dict, at_target: Seen, at_proxy: Seen) -> None:
    observed = (result, at_target, at_proxy)
    assert at_target.key_bytes == 0, observed
    assert at_target.plain == 0, observed
    assert at_proxy.key_bytes == 0, observed
    assert at_proxy.plain == 0, observed
    if result["refused"] is not None:
        assert result["refused"] in ("ConfigurationError", "InsecureHttpRefusedError"), observed
        assert result["insecure"] == [], observed
        assert at_target.connections == 0 and at_proxy.connections == 0, observed
    else:
        assert result["insecure"] == [False], observed
        assert result["judged"] and result["judged"][-1] is False, observed


@pytest.mark.parametrize("container", CONTAINERS)
@pytest.mark.parametrize("setting", ENV_SETTINGS)
@pytest.mark.parametrize("path", PATHS)
def test_an_environment_insecure_setting_gets_no_plain_channel_for_keyed_headers_to_a_remote_collector(
        shim_library, tmp_path, sinks, path, setting, container):
    target, _ = sinks
    result, at_target, at_proxy = run_case(shim_library, tmp_path, sinks, path, container,
                                           f"{COLLECTOR}:{target.port}", {setting: "true"})
    assert_refused_or_tls(result, at_target, at_proxy)


@pytest.mark.parametrize("container", ("dict", "authorization"))
@pytest.mark.parametrize("setting", ENV_SETTINGS)
@pytest.mark.parametrize("path", PATHS)
def test_an_environment_insecure_setting_with_proxy_variables_sends_no_key_to_the_collector_or_the_proxy(
        shim_library, tmp_path, sinks, path, setting, container):
    target, proxy = sinks
    result, at_target, at_proxy = run_case(shim_library, tmp_path, sinks, path, container,
                                           f"{COLLECTOR}:{target.port}", {setting: "true", **proxy_env(proxy)})
    assert_refused_or_tls(result, at_target, at_proxy)


# --- controls: plain channels that are allowed ---------------------------------------------------------------------


@pytest.mark.parametrize("with_proxy", (False, True), ids=("no-proxy", "env-proxy"))
@pytest.mark.parametrize("setting", ENV_SETTINGS)
@pytest.mark.parametrize("path", PATHS)
def test_a_loopback_collector_with_an_environment_insecure_setting_gets_its_plain_channel_direct(
        shim_library, tmp_path, sinks, path, setting, with_proxy):
    target, proxy = sinks
    extra = {setting: "true", **(proxy_env(proxy) if with_proxy else {})}
    result, at_target, at_proxy = run_case(shim_library, tmp_path, sinks, path, "dict", f"127.0.0.1:{target.port}",
                                           extra)
    observed = (result, at_target, at_proxy)
    assert result["refused"] is None and result["insecure"] == [True], observed
    assert at_target.plain >= 1 and at_target.key_bytes > 0, observed
    assert at_proxy.connections == 0 and at_proxy.key_bytes == 0, observed


@pytest.mark.parametrize("container", ("dict", "authorization"))
@pytest.mark.parametrize("setting", ENV_SETTINGS)
@pytest.mark.parametrize("path", PATHS)
def test_an_opted_in_remote_collector_with_an_environment_insecure_setting_gets_its_plain_channel(
        shim_library, tmp_path, sinks, path, setting, container):
    target, _ = sinks
    extra = {setting: "true", "FI_ALLOW_INSECURE_HTTP": "1"}
    result, at_target, at_proxy = run_case(shim_library, tmp_path, sinks, path, container,
                                           f"{COLLECTOR}:{target.port}", extra)
    observed = (result, at_target, at_proxy)
    assert result["refused"] is None and result["insecure"] == [True], observed
    assert at_target.plain >= 1 and at_target.key_bytes > 0, observed
    assert at_proxy.connections == 0 and at_proxy.key_bytes == 0, observed


@pytest.mark.parametrize("endpoint,extra", [
    ("127.0.0.1:{port}", {}),
    (COLLECTOR + ":{port}", {"FI_ALLOW_INSECURE_HTTP": "1"}),
], ids=("loopback", "opted-in"))
@pytest.mark.parametrize("setting", ENV_SETTINGS)
def test_the_mode_the_sdk_judges_is_the_mode_the_exporter_opens(shim_library, tmp_path, sinks, setting, endpoint,
                                                                 extra):
    target, _ = sinks
    result, at_target, at_proxy = run_case(shim_library, tmp_path, sinks, "factory", "dict",
                                           endpoint.format(port=target.port), {setting: "true", **extra})
    observed = (result, at_target, at_proxy)
    assert result["refused"] is None and result["judged"], observed
    assert result["insecure"] == [result["judged"][-1]] == [True], observed
