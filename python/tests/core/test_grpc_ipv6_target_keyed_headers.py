"""A gRPC exporter whose headers hold the SDK's keys opens a channel without TLS only to a loopback collector, or to
another collector with ``FI_ALLOW_INSECURE_HTTP=1``. A bracketed IPv6 target (with or without a port, with a zone id)
and a target behind a scheme (``grpc://``, ``grpcs://``, any other) are read and judged as an IPv4 address or a name
is: a scheme other than ``https`` does not turn a plain channel into a TLS judgement, and a plain channel to a host
that is not loopback, or that cannot be read, is refused with ``ConfigurationError``.

gRPC dials an address literal in C, so each case runs in a child process with a preloaded library (the shim of
``test_localhost_direct_dial_grpc``, with one more rule) that sends a connect to ``2001:db8::1`` (any port) to the
listener on ``::1`` and a connect to ``198.51.100.1`` to ``127.0.0.1``, and logs every address it is asked to dial. The
listener answers the HTTP/2 preface and counts the bytes of the planted key and secret, fresh random values per case.
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
PREFACE = b"PRI * HTTP/2.0"
DOC_V6 = "2001:db8::1"
PATHS = ("factory", "setup_tracing")
MODES = ("env_traces_insecure", "env_insecure", "insecure_arg")
MODE_ENV = {
    "env_traces_insecure": {"OTEL_EXPORTER_OTLP_TRACES_INSECURE": "true"},
    "env_insecure": {"OTEL_EXPORTER_OTLP_INSECURE": "true"},
    "insecure_arg": {},
}
REMOTE_FORMS = (
    "grpc://[2001:db8::1]:{port}",
    "foo://[2001:db8::1]:{port}",
    "grpc://[::ffff:198.51.100.1]:{port}",
    "grpc://[2001:db8::1]",
    "grpcs://[2001:db8::1]:{port}",
)
PROXY_SETTINGS = ("grpc_proxy", "GRPC_PROXY", "https_proxy", "HTTPS_PROXY", "http_proxy", "HTTP_PROXY", "all_proxy",
                  "ALL_PROXY")

REDIRECT_V6 = r"""
        {
            struct in6_addr doc;
            const char *port = getenv("FI_SHIM_V6_PORT");
            inet_pton(AF_INET6, "2001:db8::1", &doc);
            if (memcmp(&a6.sin6_addr, &doc, sizeof doc) == 0) {
                a6.sin6_addr = in6addr_loopback;
                if (port) a6.sin6_port = htons((unsigned short)atoi(port));
                return real(fd, (const struct sockaddr *)&a6, len);
            }
        }
"""
HOOK = "        note(text);\n        if (IN6_IS_ADDR_V4MAPPED"

CHILD = textwrap.dedent(
    r'''
    import json, os, sys

    path, mode, endpoint = sys.argv[1], sys.argv[2], sys.argv[3]
    headers = {"x-api-key": os.environ["MARK_API"], "x-secret-key": os.environ["MARK_SECRET"]}
    insecure = {"insecure_arg": True, "tls_arg": False}.get(mode)

    from opentelemetry.exporter.otlp.proto.grpc import trace_exporter

    built = []
    original_init = trace_exporter.OTLPSpanExporter.__init__

    def recording_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        built.append(self)

    trace_exporter.OTLPSpanExporter.__init__ = recording_init

    from fi.errors import ConfigurationError
    from fi.evals.otel.config import ExporterConfig, TraceConfig
    from fi.evals.otel.types import ExporterType

    config = ExporterConfig(type=ExporterType.OTLP_GRPC, endpoint=endpoint, headers=headers, insecure=insecure,
                            timeout_ms=2000)
    result = {"refused": None, "configuration_error": False, "code": None}
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
    except Exception as error:
        result["refused"] = type(error).__name__
        result["configuration_error"] = isinstance(error, ConfigurationError)
        result["code"] = getattr(error, "code", None)
    result["insecure"] = [getattr(exporter_, "_insecure", None) for exporter_ in built]
    print("RESULT " + json.dumps(result), flush=True)
    os._exit(0)
    '''
)


@pytest.fixture(scope="module")
def shim_library(tmp_path_factory) -> Path:
    command = shim_compiler()
    pytest.importorskip("opentelemetry.exporter.otlp.proto.grpc.trace_exporter")
    assert HOOK in SHIM
    directory = tmp_path_factory.mktemp("ipv6_target_shim")
    (directory / "shim.c").write_text(SHIM.replace(HOOK, "        note(text);\n" + REDIRECT_V6 + HOOK[len("        note(text);\n"):]))
    library = directory / "shim.so"
    subprocess.run([*command, "-shared", "-fPIC", "-o", str(library), str(directory / "shim.c"), "-ldl"], check=True)
    return library


@pytest.fixture()
def sink():
    listener = Sink(False)
    if len(listener.socks) < 2:
        listener.close()
        pytest.skip("this machine has no ::1 listener")
    yield listener
    listener.close()


class Seen:
    def __init__(self, sink: Sink, markers: tuple[str, ...], connects: list[str]) -> None:
        blob = b"".join(sink.data)
        self.connections = sink.connections
        self.plain = blob.count(PREFACE)
        self.marker_bytes = sum(blob.count(marker.encode()) * len(marker) for marker in markers)
        self.connects = connects

    def __repr__(self) -> str:
        return (f"connections={self.connections} plain_h2={self.plain} marker_bytes={self.marker_bytes} "
                f"connects={self.connects}")


def run_case(shim_library: Path, tmp_path: Path, sink: Sink, path: str, mode: str, endpoint: str,
             extra: dict | None = None):
    markers = (secrets.token_hex(16), secrets.token_hex(16))
    log = tmp_path / "connects.log"
    log.write_text("")
    env = {k: v for k, v in os.environ.items()
           if k not in PROXY_ENV and k not in PROXY_SETTINGS and not k.startswith(("FI_", "OTEL_", "GRPC_"))}
    preload = [str(shim_library)] + [p for p in os.environ.get("LD_PRELOAD", "").split(":") if p]
    env.update(LD_PRELOAD=":".join(preload), GRPC_DNS_RESOLVER="native", FI_SHIM_LOG=str(log),
               FI_SHIM_V6_PORT=str(sink.port), MARK_API=markers[0], MARK_SECRET=markers[1],
               FI_LOGIN_FILE=str(tmp_path / "no-login.json"), PYTHONPATH=str(PYTHON), **MODE_ENV.get(mode, {}),
               **(extra or {}))
    done = subprocess.run([sys.executable, "-c", CHILD, path, mode, endpoint], env=env, timeout=120,
                          capture_output=True, cwd=str(tmp_path))
    time.sleep(0.3)
    lines = [line for line in done.stdout.decode(errors="replace").splitlines() if line.startswith("RESULT ")]
    assert lines, done.stderr.decode(errors="replace")[-3000:]
    connects = [line for line in log.read_text().splitlines() if line]
    return json.loads(lines[-1][len("RESULT "):]), Seen(sink, markers, connects)


@pytest.mark.parametrize("form", REMOTE_FORMS)
@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("path", PATHS)
def test_keyed_headers_get_no_plain_channel_to_a_bracketed_ipv6_or_scheme_prefixed_remote_target(
        shim_library, tmp_path, sink, path, mode, form):
    result, seen = run_case(shim_library, tmp_path, sink, path, mode, form.format(port=sink.port))
    observed = (result, seen)
    assert seen.marker_bytes == 0, observed
    assert seen.plain == 0, observed
    assert result["refused"] is not None and result["configuration_error"], observed
    assert result["code"] == "insecure_http_origin", observed
    assert result["insecure"] == [], observed
    assert seen.connections == 0, observed


# --- controls: channels that are allowed ---------------------------------------------------------------------------


@pytest.mark.parametrize("form", ("grpc://[::1]:{port}", "[::1]:{port}", "grpc://127.0.0.1:{port}",
                                  "127.0.0.1:{port}"))
@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("path", PATHS)
def test_keyed_headers_reach_a_loopback_collector_over_a_plain_channel(shim_library, tmp_path, sink, path, mode,
                                                                       form):
    result, seen = run_case(shim_library, tmp_path, sink, path, mode, form.format(port=sink.port))
    observed = (result, seen)
    assert result["refused"] is None and result["insecure"] == [True], observed
    assert seen.plain >= 1 and seen.marker_bytes > 0, observed
    # gRPC may dial 127.0.0.1 from an IPv6 socket, as ::ffff:127.0.0.1.
    loopback = {"::1"} if "[::1]" in form else {"127.0.0.1", "::ffff:127.0.0.1"}
    assert seen.connects and set(seen.connects) <= loopback, observed


@pytest.mark.parametrize("form", ("grpc://[2001:db8::1]:{port}", "[2001:db8::1]:{port}", "grpc://[2001:db8::1]"))
@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("path", PATHS)
def test_keyed_headers_reach_a_remote_ipv6_collector_over_a_plain_channel_with_the_opt_in(
        shim_library, tmp_path, sink, path, mode, form):
    result, seen = run_case(shim_library, tmp_path, sink, path, mode, form.format(port=sink.port),
                            {"FI_ALLOW_INSECURE_HTTP": "1"})
    observed = (result, seen)
    assert result["refused"] is None and result["insecure"] == [True], observed
    assert seen.plain >= 1 and seen.marker_bytes > 0, observed
    assert DOC_V6 in seen.connects, observed


@pytest.mark.parametrize("form", ("grpc://[2001:db8::1]:{port}", "[2001:db8::1]:{port}", "https://[2001:db8::1]:{port}"))
def test_insecure_false_keeps_tls_to_a_remote_ipv6_collector(shim_library, tmp_path, sink, form):
    result, seen = run_case(shim_library, tmp_path, sink, "factory", "tls_arg", form.format(port=sink.port))
    observed = (result, seen)
    assert result["refused"] is None and result["insecure"] == [False], observed
    assert seen.plain == 0 and seen.marker_bytes == 0, observed


# --- the target as read and judged, without a channel -----------------------------------------------------------------

KEYED = {"x-api-key": "planted-marker-header"}


@pytest.mark.parametrize("endpoint", [
    "grpc://[2001:db8::1]:4317", "foo://[2001:db8::1]:4317", "grpc://[::ffff:198.51.100.1]:4317", "grpc://[2001:db8::1]",
    "grpcs://[2001:db8::1]:4317", "GRPC://[2001:DB8::1]:4317", "[2001:db8::1]:4317", "[2001:db8::1]",
    "[2001:db8::2%eth0]:4317", "grpc://[2001:db8::2%25eth0]:4317", "[::1%lo]:4317", "grpc://[::1%lo]:4317",
    "grpc://[zz::1]:4317", "[2001:db8::1:4317", "grpc://198.51.100.1:4317", "198.51.100.1:4317", "collector.example:4317",
])
def test_a_plain_channel_with_keyed_headers_to_a_target_that_is_not_loopback_is_refused(endpoint, monkeypatch):
    from fi._core.http_security import require_secure_grpc_target
    from fi._otlp_headers import grpc_plain_choice
    from fi.errors import ConfigurationError

    monkeypatch.delenv("FI_ALLOW_INSECURE_HTTP", raising=False)
    with pytest.raises(ConfigurationError):
        require_secure_grpc_target(endpoint, KEYED, insecure=True)
    with pytest.raises(ConfigurationError):
        grpc_plain_choice(endpoint, True)


@pytest.mark.parametrize("endpoint", ["grpc://[2001:db8::1]:4317", "[2001:db8::1]", "grpcs://[2001:db8::1]:4317"])
def test_the_opt_in_allows_a_plain_channel_to_a_remote_ipv6_target(endpoint, monkeypatch):
    from fi._core.http_security import require_secure_grpc_target
    from fi._otlp_headers import grpc_plain_choice

    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    require_secure_grpc_target(endpoint, KEYED, insecure=True)
    assert grpc_plain_choice(endpoint, True) is True


@pytest.mark.parametrize("endpoint", ["[2001:db8::2%eth0]:4317", "grpc://[2001:db8::2%25eth0]:4317", "[::1%lo]:4317"])
def test_a_plain_channel_with_keyed_headers_to_a_target_with_a_zone_id_is_refused_with_the_opt_in_too(endpoint,
                                                                                                     monkeypatch):
    from fi._core.http_security import require_secure_grpc_target
    from fi.errors import ConfigurationError

    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    with pytest.raises(ConfigurationError):
        require_secure_grpc_target(endpoint, KEYED, insecure=True)


@pytest.mark.parametrize("endpoint", ["grpc://[::1]:4317", "[::1]:4317", "[::1]", "foo://[::1]", "127.0.0.1:4317",
                                      "grpc://127.0.0.1:4317", "localhost:4317"])
def test_a_plain_channel_to_a_loopback_target_passes(endpoint, monkeypatch):
    from fi._core.http_security import require_secure_grpc_target
    from fi._otlp_headers import grpc_loopback_target, grpc_plain_choice

    monkeypatch.delenv("FI_ALLOW_INSECURE_HTTP", raising=False)
    require_secure_grpc_target(endpoint, KEYED, insecure=True)
    assert grpc_plain_choice(endpoint, True) is False
    assert grpc_loopback_target(endpoint)


@pytest.mark.parametrize("endpoint", ["https://[2001:db8::1]:4317", "HTTPS://[2001:db8::1]:4317"])
def test_an_https_target_is_judged_as_tls_whatever_insecure_says(endpoint, monkeypatch):
    from fi._core.http_security import require_secure_grpc_target
    from fi._otlp_headers import grpc_plain_choice

    monkeypatch.delenv("FI_ALLOW_INSECURE_HTTP", raising=False)
    require_secure_grpc_target(endpoint, KEYED, insecure=True)
    assert grpc_plain_choice(endpoint, True) is False


@pytest.mark.parametrize("endpoint,host", [
    ("[2001:db8::1]:4317", "2001:db8::1"), ("grpc://[2001:DB8:0::1]:4317", "2001:db8::1"),
    ("[::ffff:198.51.100.1]", "::ffff:198.51.100.1"), ("[2001:db8::2%eth0]:4317", "2001:db8::2%eth0"), ("[::1]:4317", "::1"),
])
def test_a_bracketed_ipv6_target_is_read_as_its_address(endpoint, host):
    import ipaddress

    from fi._otlp_headers import _plain_grpc_host, grpc_dial_target, self_hosted_grpc_target

    assert _plain_grpc_host(grpc_dial_target(endpoint)) == str(ipaddress.IPv6Address(host))
    assert self_hosted_grpc_target(endpoint) is (host != "::1")
