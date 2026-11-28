"""IPv6 loopback settings bind the OTLP gRPC exporter to TLS."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

import grpc
import pytest

from fi.errors import ConfigurationError
from tests.experiments.unit.test_fi_bound_ambiguous_endpoints import build
from tests.experiments.unit.test_fi_bound_authority_forms import clean_hosts  # noqa: F401
from tests.experiments.unit.test_fi_bound_exporter_headers import ambient  # noqa: F401
from tests.experiments.unit.test_fi_bound_grpc_target import channels  # noqa: F401
from tests.experiments.unit.test_fi_bound_grpc_tls_only import kinds  # noqa: F401

SETTINGS = ("FI_BASE_URL", "FI_TRACES_URL", "FI_GRPC_URL")
HEADERS = {"x-api-key": "zone-key-value", "x-secret-key": "zone-secret-value"}
MARKERS = tuple(value.encode("ascii") for value in HEADERS.values())


class Receiver(grpc.ServerInterceptor):
    def __init__(self):
        self.calls = []
        self.marker_bytes = 0

    def intercept_service(self, continuation, handler_call_details):
        self.calls.append(handler_call_details.method)
        for _, value in handler_call_details.invocation_metadata:
            data = value if isinstance(value, bytes) else value.encode("utf-8")
            self.marker_bytes += sum(data.count(marker) * len(marker) for marker in MARKERS)
        return continuation(handler_call_details)


@contextmanager
def loopback_receiver():
    receiver = Receiver()
    with ThreadPoolExecutor(max_workers=1) as workers:
        server = grpc.server(workers, interceptors=(receiver,))
        try:
            port = server.add_insecure_port("[::1]:0")
        except RuntimeError:
            pytest.skip("no IPv6 loopback listener")
        if not port:
            pytest.skip("no IPv6 loopback listener")
        server.start()
        try:
            yield port, receiver
        finally:
            server.stop(0).wait()


@pytest.mark.parametrize("setting", SETTINGS)
@pytest.mark.parametrize(
    "form",
    [
        pytest.param("ipv6:[::1]:{port}", id="ipv6-scheme"),
        pytest.param("ipv6:///[::1]:{port}", id="ipv6-empty-authority"),
        pytest.param("ipv6://[::1]:{port}", id="ipv6-authority"),
        pytest.param("ipv6://[::1]", id="ipv6-authority-no-port"),
        pytest.param("ipv6:[0:0:0:0:0:0:0:1]:{port}", id="ipv6-expanded"),
        pytest.param("[::1%25lo]:{port}", id="encoded-zone"),
        pytest.param("[::1%lo]:{port}", id="literal-zone"),
        pytest.param("http://[::1%25lo]:{port}", id="http-encoded-zone"),
        pytest.param("[::1]:{port}", id="plain-loopback"),
    ],
)
def test_ipv6_loopback_setting_requires_tls(clean_hosts, ambient, channels, monkeypatch, setting, form):
    with loopback_receiver() as (port, receiver):
        monkeypatch.setenv(setting, form.format(port=port))
        with pytest.raises(ConfigurationError) as refused:
            build("OTLP_GRPC", f"[::1]:{port}", insecure=True, headers=HEADERS, timeout_ms=500)
    assert refused.value.code == "insecure_loopback_grpc"
    assert channels == []
    assert receiver.calls == []
    assert receiver.marker_bytes == 0


@pytest.mark.parametrize("setting", SETTINGS)
def test_non_loopback_zone_does_not_bind_the_loopback_collector(clean_hosts, ambient, monkeypatch, setting):
    from fi._otlp_headers import future_agi_hosts

    monkeypatch.setenv(setting, "[2001:db8::2%25eth0]:4317")
    assert future_agi_hosts() == {"api.futureagi.com", "grpc.futureagi.com"}
    exporter = build("OTLP_GRPC", "[::1]:4317", insecure=True)
    exporter.shutdown()


def test_unbound_loopback_collector_accepts_insecure(clean_hosts, ambient):
    exporter = build("OTLP_GRPC", "[::1]:4317", insecure=True)
    exporter.shutdown()


def one_span():
    from opentelemetry.sdk.trace import TracerProvider

    with TracerProvider().get_tracer("zone-test").start_as_current_span("zone-span") as span:
        pass
    return span


@pytest.mark.parametrize("setting", SETTINGS)
@pytest.mark.parametrize(
    "form",
    [
        pytest.param("ipv6://[::1]:{port}", id="ipv6-authority"),
        pytest.param("ipv6://[::1]", id="ipv6-authority-no-port"),
        pytest.param("ipv6:///[::1]:{port}", id="ipv6-empty-authority"),
    ],
)
def test_ipv6_authority_setting_sends_no_plaintext_rpc(clean_hosts, ambient, monkeypatch, setting, form):
    """An exporter that is built anyway exports one span, so the receiver counts what a plaintext channel sends."""
    with loopback_receiver() as (port, receiver):
        monkeypatch.setenv(setting, form.format(port=port))
        try:
            exporter = build("OTLP_GRPC", f"[::1]:{port}", insecure=True, headers=HEADERS, timeout_ms=500)
        except ConfigurationError as refused:
            code = refused.code
        else:
            code = None
            try:
                exporter.export([one_span()])
            finally:
                exporter.shutdown()
    assert (code, len(receiver.calls), receiver.marker_bytes) == ("insecure_loopback_grpc", 0, 0)


# Every setting form that binds an address, with the address it binds.
BOUND_FORMS = [
    ("[::1]:4317", "::1"),
    ("[::1]", "::1"),
    ("http://[::1]:4317", "::1"),
    ("https://[::1]:4317", "::1"),
    ("//[::1]:4317", "::1"),
    ("dns:[::1]:4317", "::1"),
    ("dns:///[::1]:4317", "::1"),
    ("dns://8.8.8.8/[::1]:4317", "::1"),
    ("dns://resolver/[::1]:4317", "::1"),
    ("ipv6:[::1]:4317", "::1"),
    ("ipv6:///[::1]:4317", "::1"),
    ("ipv6://[::1]:4317", "::1"),
    ("ipv6://[::1]", "::1"),
    ("ipv6://[::1]:4317/", "::1"),
    ("IPV6:[::1]:4317", "::1"),
    ("ipv6:%5B::1%5D:4317", "::1"),
    ("ipv6:/[::1]:4317", "::1"),
    ("ipv6:[::1]:4317?x", "::1"),
    ("ipv6:[::1%25lo]:4317", "::1"),
    ("[::1%25lo]:4317", "::1"),
    ("[::1%lo]:4317", "::1"),
    ("http://[::1%25lo]:4317", "::1"),
    ("ipv6:[::ffff:127.0.0.1]:4317", "::ffff:7f00:1"),
    ("ipv6://[::ffff:127.0.0.1]:4317", "::ffff:7f00:1"),
    ("ipv6:[0:0:0:0:0:0:0:1]:4317", "::1"),
    ("ipv6://[0:0:0:0:0:0:0:1]:4317", "::1"),
    ("ipv6://[::1]:4317/[::2]:4317", "::1"),
    ("ipv6:[2001:db8::1]:4317", "2001:db8::1"),
    ("ipv6://[2001:db8::1]:4317", "2001:db8::1"),
    ("localhost:4317", "localhost"),
    ("127.0.0.1:4317", "127.0.0.1"),
    ("https://api.futureagi.com", "api.futureagi.com"),
    ("api.futureagi.com:443", "api.futureagi.com"),
    ("DNS:///[::1]:4317", "::1"),
    ("dns://[2001:db8::1]/[::1]:4317", "::1"),
    ("//[0:0::1]:4317", "::1"),
    ("ipv6://[2001:db8::1]/[::1]:4317", "2001:db8::1"),
    ("ipv6:[::1]:4317?label=local", "::1"),
    ("https://[2001:db8::1]:4317/v1/[::1%lo]", "2001:db8::1"),
    ("http://[::1%lo]:4317", "::1"),
    ("[::ffff:127.0.0.1]:4317", "::ffff:7f00:1"),
    ("http://[::ffff:127.0.0.1]:4317", "::ffff:7f00:1"),
    ("https://[::ffff:127.0.0.1]:4317", "::ffff:7f00:1"),
    ("dns:///[::ffff:127.0.0.1]:4317", "::ffff:7f00:1"),
    ("//[::ffff:127.0.0.1]:4317", "::ffff:7f00:1"),
    ("127.0.0.1:5999", "127.0.0.1"),
    ("http://127.0.0.1:5999", "127.0.0.1"),
    ("https://127.0.0.1:5999", "127.0.0.1"),
    ("dns:///127.0.0.1:5999", "127.0.0.1"),
    ("[::1]:5999", "::1"),
    ("http://[::1]:5999", "::1"),
    ("https://[::1]:5999", "::1"),
    ("dns:///[::1]:5999", "::1"),
    ("//[::1]:5999", "::1"),
    ("[::ffff:127.0.0.1]:5999", "::ffff:7f00:1"),
    ("http://[::ffff:127.0.0.1]:5999", "::ffff:7f00:1"),
    ("https://[::ffff:127.0.0.1]:5999", "::ffff:7f00:1"),
    ("dns:///[::ffff:127.0.0.1]:5999", "::ffff:7f00:1"),
    ("//[::ffff:127.0.0.1]:5999", "::ffff:7f00:1"),
]


@pytest.mark.parametrize(("form", "address"), BOUND_FORMS)
@pytest.mark.parametrize("setting", SETTINGS)
def test_a_bound_setting_form_binds_its_address(clean_hosts, monkeypatch, setting, form, address):
    from fi._otlp_headers import future_agi_hosts

    monkeypatch.setenv(setting, form)
    assert future_agi_hosts() == {"api.futureagi.com", "grpc.futureagi.com", address}


@pytest.mark.parametrize(
    "form",
    [
        "ipv6://host/[::1]:4317",
        "ipv6://[2001:db8::2%25eth0]:4317",
        "ipv6:[::1]",
        "ipv6:[::1]:0",
        "ipv6:[::1]:65536",
        "ipv6://[::1]:65536",
        "ipv6:////[::1]:4317",
        "ipv6:///%2F[::1]:4317",
        "ipv6:////[2001:db8::1]:4317",
        "ipv6:///%2F[2001:db8::1]:4317",
        "ipv6:///%2f[2001:db8::1]:4317",
    ],
)
def test_ipv6_setting_forms_that_name_no_loopback_address(clean_hosts, monkeypatch, form):
    from fi._otlp_headers import future_agi_hosts

    monkeypatch.setenv("FI_GRPC_URL", form)
    assert future_agi_hosts() == {"api.futureagi.com", "grpc.futureagi.com"}


@pytest.mark.parametrize("form", ["ipv6://[::1]:{port}", "ipv6://[::1]", "ipv6:///[::1]:{port}"])
@pytest.mark.parametrize("insecure_env", [None, "true"], ids=["insecure-false", "otlp-insecure-env"])
def test_ipv6_authority_setting_keeps_tls(clean_hosts, ambient, kinds, monkeypatch, form, insecure_env):
    """With insecure=False the channel uses TLS for any setting; with insecure unset, a bound setting keeps TLS when
    the OTLP environment asks for an insecure channel."""
    monkeypatch.setenv("FI_GRPC_URL", form.format(port=4317))
    config = {"headers": HEADERS}
    if insecure_env is not None:
        monkeypatch.setenv("OTEL_EXPORTER_OTLP_TRACES_INSECURE", insecure_env)
        config["insecure"] = None
    exporter = build("OTLP_GRPC", "[::1]:4317", **config)
    exporter.shutdown()
    assert kinds == ["secure_channel"]
