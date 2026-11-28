# ruff: noqa: F811
"""An endpoint is Future AGI only when the parser the HTTP client connects with says so.

``requests`` connects to the host parsed by ``urllib3``. A backslash ends the authority in ``urllib3``
but not in the standard library parser, so the two can disagree about the host. The SDK classifies an
endpoint as Future AGI-bound only if both parsers agree on the host and the authority is unambiguous.
For gRPC, the SDK uses the host gRPC dials, including the ``dns:`` forms. A gRPC exporter bound for
Future AGI does not load a credential provider specified in the environment.
"""

import pytest

from tests.experiments.unit.test_fi_bound_exporter_headers import (  # noqa: F401
    ambient,
    evals_exporter,
    export_spans,
    sink,
)


@pytest.fixture
def clean_hosts(monkeypatch):
    for name in ("FI_BASE_URL", "FI_GRPC_URL", "FI_TRACES_URL"):
        monkeypatch.delenv(name, raising=False)


def bound(endpoint):
    from fi._otlp_headers import is_future_agi_endpoint

    return is_future_agi_endpoint(endpoint)


AMBIGUOUS = [
    "https://other-origin.example\\@api.futureagi.com/v1/traces",
    "https://other-origin.example\\@api.futureagi.com:443/v1/traces",
    "https://api.futureagi.com\\@other-origin.example/v1/traces",
    "https://api.futureagi.com\\.other-origin.example/v1/traces",
    "evil\\@grpc.futureagi.com:443",
    "grpc.futureagi.com\\@evil:443",
    "https://%61pi.futureagi.com/v1/traces",
    "https://api.futureagi.com%2eother-origin.example/v1/traces",
    "https://api.futureagi.com%00.other-origin.example/v1/traces",
    "https://api.futureagi.com .other-origin.example/v1/traces",
    "https://api.futureagi.com\t.other-origin.example/v1/traces",
    "https://api.futureagi.com\x01.other-origin.example/v1/traces",
    "https://a@b@api.futureagi.com/v1/traces",
    "https://a@api.futureagi.com@other-origin.example/v1/traces",
    "dns:///evil\\@grpc.futureagi.com:443",
    "dns:///grpc.futureagi.com\\@evil:443",
]


@pytest.mark.parametrize("endpoint", AMBIGUOUS)
def test_an_ambiguous_authority_is_never_futureagi(clean_hosts, endpoint):
    assert bound(endpoint) is False


@pytest.mark.parametrize(
    "endpoint",
    [
        "dns:///grpc.futureagi.com:443",
        "dns:///GRPC.FUTUREAGI.COM.:443",
        "dns:///grpc.futureagi.com",
    ],
)
def test_a_dns_target_is_classified_by_the_host_grpc_dials(clean_hosts, endpoint):
    assert bound(endpoint) is True


@pytest.mark.parametrize(
    "endpoint",
    [
        "dns://grpc.futureagi.com/other-origin.example:443",
        "dns:///grpc.futureagi.com.other-origin.example:443",
        "dns:///othergrpc.futureagi.com:443",
        "ipv4:127.0.0.1:443",
        "ipv4:127.0.0.1:443,127.0.0.2:443",
        "ipv6:[::1]:443",
        "unix:/tmp/grpc.futureagi.com",
        "unix-abstract:grpc.futureagi.com",
        "vsock:1:443",
    ],
)
def test_other_grpc_targets_stay_the_users_own(clean_hosts, endpoint):
    assert bound(endpoint) is False


def test_a_configured_dns_target_host_counts(clean_hosts, monkeypatch):
    monkeypatch.setenv("FI_GRPC_URL", "dns:///grpc.eu.example.test:443")
    assert bound("grpc.eu.example.test:443") is True
    assert bound("dns:///grpc.eu.example.test.:443") is True
    assert bound("dns:///grpc.us.example.test:443") is False


def test_a_configured_ambiguous_value_is_not_a_futureagi_host(clean_hosts, monkeypatch):
    monkeypatch.setenv("FI_BASE_URL", "https://other-origin.example\\@api.eu.example.test")
    assert bound("https://api.eu.example.test/v1/traces") is False
    assert bound("https://other-origin.example/v1/traces") is False


# --- the host is the one requests connects to ---------------------------------------------------------


def test_sharp_s_and_ss_are_different_hosts(clean_hosts, monkeypatch):
    """``urllib3`` encodes ß as its own label (IDNA 2008); it does not map it to ss."""
    monkeypatch.setenv("FI_BASE_URL", "https://strasse.example.test")
    assert bound("https://strasse.example.test/v1/traces") is True
    assert bound("https://straße.example.test/v1/traces") is False
    assert bound("https://xn--strae-oqa.example.test/v1/traces") is False


def test_a_configured_sharp_s_host_matches_its_punycode_form(clean_hosts, monkeypatch):
    monkeypatch.setenv("FI_BASE_URL", "https://straße.example.test")
    assert bound("https://xn--strae-oqa.example.test/v1/traces") is True
    assert bound("https://STRAßE.example.test./v1/traces") is True
    assert bound("https://strasse.example.test/v1/traces") is False


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://ａpi.futureagi.com/tracer/v1/traces",
        "https://api.futureagi。com/tracer/v1/traces",
        "https://api．futureagi.com/tracer/v1/traces",
        "ｇrpc.futureagi.com:443",
    ],
)
def test_a_spelling_requests_refuses_is_not_futureagi(clean_hosts, endpoint):
    """``requests`` raises InvalidURL for these, and no client dials them as a Future AGI host."""
    assert bound(endpoint) is False


# --- the keys do not reach the host requests connects to -------------------------------------------------


@pytest.fixture
def through_sink(sink, monkeypatch):
    """Every plain-HTTP request goes to the local sink as a proxy, whatever its URL names."""
    for name in ("NO_PROXY", "no_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("HTTP_PROXY", sink.base)
    monkeypatch.setenv("http_proxy", sink.base)
    return sink


@pytest.fixture
def opted_in_sink(sink, monkeypatch):
    """Names under example.test resolve to the local sink and FI_ALLOW_INSECURE_HTTP=1 allows the plain transport.
    No proxy is set, so nothing leaves this machine."""
    import socket

    for name in ("HTTP_PROXY", "http_proxy", "NO_PROXY", "no_proxy", "HTTPS_PROXY", "https_proxy",
                 "ALL_PROXY", "all_proxy"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    real = socket.getaddrinfo

    def resolve(host, port, *args, **kwargs):
        if isinstance(host, str) and host.lower().rstrip(".").endswith("example.test"):
            host = "127.0.0.1"
        return real(host, port, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    return sink


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://other-origin.example\\@api.futureagi.com/tracer/v1/traces",
        "http://other-origin.example\\@api.futureagi.com:80/tracer/v1/traces",
    ],
)
@pytest.mark.parametrize("kind", ["OTLP_HTTP", "ARIZE", "PHOENIX", "LANGFUSE"])
def test_a_backslash_endpoint_gets_no_futureagi_key(
    through_sink, clean_hosts, ambient, monkeypatch, endpoint, kind
):
    """The exporter is refused when it is built (see test_fi_bound_ambiguous_endpoints), so the host
    urllib3 would dial receives nothing at all."""
    from fi.errors import ConfigurationError

    monkeypatch.setenv("FI_API_KEY", "fi-key-value")
    monkeypatch.setenv("FI_SECRET_KEY", "fi-secret-value")
    with pytest.raises(ConfigurationError):
        export_spans(evals_exporter(endpoint, kind=kind))
    assert through_sink.requests == []


def test_a_futureagi_endpoint_gets_only_the_sdk_keys(
    opted_in_sink, clean_hosts, ambient, monkeypatch
):
    monkeypatch.setenv("FI_API_KEY", "fi-key-value")
    monkeypatch.setenv("FI_SECRET_KEY", "fi-secret-value")
    port = opted_in_sink.server.server_address[1]
    monkeypatch.setenv("FI_BASE_URL", f"http://api.example.test:{port}")
    export_spans(evals_exporter(f"http://API.example.test:{port}/tracer/v1/traces", kind="OTLP_HTTP"))
    headers = opted_in_sink.requests[0]
    assert headers["x-api-key"] == "fi-key-value"
    assert headers["x-secret-key"] == "fi-secret-value"
    assert "x-ambient" not in headers and "authorization" not in headers


# --- gRPC credential providers ---------------------------------------------------------------------------


@pytest.fixture
def provider(monkeypatch):
    """A credential provider named in the environment; ``loaded`` records every time it is loaded."""
    import grpc
    import opentelemetry.exporter.otlp.proto.grpc.exporter as grpc_exporter

    loaded = []

    class EntryPoint:
        def __init__(self, name):
            self.name = name

        def load(self):
            loaded.append(self.name)
            return lambda: grpc.ssl_channel_credentials()

    def entry_points(*, group=None, name=None, **kwargs):
        assert group == "opentelemetry_otlp_credential_provider"
        return [EntryPoint(name)]

    monkeypatch.setattr(grpc_exporter, "entry_points", entry_points)
    monkeypatch.setenv("OTEL_PYTHON_EXPORTER_OTLP_GRPC_CREDENTIAL_PROVIDER", "ambient-provider")
    monkeypatch.setenv("OTEL_PYTHON_EXPORTER_OTLP_GRPC_TRACES_CREDENTIAL_PROVIDER", "ambient-provider")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_TRACES_CERTIFICATE", "/nonexistent/ca.pem")
    return loaded


def grpc_exporter_at(endpoint):
    from fi.evals.otel._tracer_factories import _create_exporter
    from fi.evals.otel.config import ExporterConfig, ExporterType

    return _create_exporter(
        ExporterConfig(type=ExporterType.OTLP_GRPC, endpoint=endpoint, insecure=False)
    )


@pytest.mark.parametrize(
    "endpoint",
    ["grpc.futureagi.com:443", "dns:///grpc.futureagi.com:443", "GRPC.FUTUREAGI.COM.:443"],
)
def test_a_futureagi_grpc_exporter_loads_no_credential_provider(
    clean_hosts, provider, monkeypatch, endpoint
):
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_TRACES_CERTIFICATE")
    grpc_exporter_at(endpoint)
    assert provider == []


def test_a_users_own_grpc_exporter_keeps_its_credential_provider(clean_hosts, provider, monkeypatch):
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_TRACES_CERTIFICATE")
    grpc_exporter_at("collector.example.test:4317")
    assert provider


def test_a_futureagi_grpc_exporter_loads_no_provider_when_a_traces_certificate_is_set(
    clean_hosts, provider, tmp_path, monkeypatch
):
    """The traces-specific path of the exporter loads the provider when a traces certificate is set."""
    ca = tmp_path / "ca.pem"
    ca.write_bytes(b"")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_TRACES_CERTIFICATE", str(ca))
    grpc_exporter_at("grpc.futureagi.com:443")
    assert provider == []
