# ruff: noqa: F811
"""A Future AGI gRPC exporter requires TLS and treats a blank endpoint as unset.

``insecure=True`` on an exporter that dials a Future AGI host is refused with ``ConfigurationError`` (code
``INSECURE_HTTP_REFUSED``), and ``OTEL_EXPORTER_OTLP_*INSECURE`` is not read for it. A listener that records
what a client sends shows a TLS handshake and none of the SDK's keys. An endpoint that is empty or only white
space is read as no endpoint, for every exporter type, and a guarded session adapter map also refuses
``move_to_end`` once it is sealed.
"""

import contextlib
import socket
import threading

import pytest

from fi.errors import ConfigurationError
from tests.experiments.unit.test_fi_bound_ambiguous_endpoints import build
from tests.experiments.unit.test_fi_bound_authority_forms import clean_hosts  # noqa: F401
from tests.experiments.unit.test_fi_bound_exporter_headers import ambient, export_spans  # noqa: F401
from tests.experiments.unit.test_fi_bound_grpc_target import channels, keys  # noqa: F401

INSECURE_CODE = "INSECURE_HTTP_REFUSED"
FI_GRPC_FORMS = [
    "api.futureagi.com:443",
    "grpc.futureagi.com:443",
    "dns:///grpc.futureagi.com:443",
    "https://grpc.futureagi.com:443",
    "//grpc.futureagi.com:443",
]
WHITESPACE = ["", " ", "\t", "\n", "\r\n", "\xa0", "\u2003"]


@pytest.fixture
def kinds(monkeypatch):
    """Which channel factory each gRPC exporter opens its channel with (versions differ in what they store)."""
    from opentelemetry.exporter.otlp.proto.grpc import exporter as grpc_exporter

    seen = []
    for name in ("secure_channel", "insecure_channel"):
        original = getattr(grpc_exporter, name)

        def make(*args, _name=name, _original=original, **kwargs):
            seen.append(_name)
            return _original(*args, **kwargs)

        monkeypatch.setattr(grpc_exporter, name, make)
    return seen


@pytest.mark.parametrize("endpoint", FI_GRPC_FORMS)
def test_insecure_is_refused_for_a_futureagi_grpc_exporter(clean_hosts, ambient, keys, channels, endpoint):
    with pytest.raises(ConfigurationError) as refused:
        build("OTLP_GRPC", endpoint, insecure=True)
    assert refused.value.code == INSECURE_CODE
    assert channels == []
    message = str(refused.value).lower()
    for part in ("fi-key-value", "fi-secret-value", "grpc.futureagi.com", "api.futureagi.com", endpoint.lower()):
        assert part not in message


@pytest.mark.parametrize("endpoint", FI_GRPC_FORMS)
@pytest.mark.parametrize("variable", ["OTEL_EXPORTER_OTLP_INSECURE", "OTEL_EXPORTER_OTLP_TRACES_INSECURE"])
def test_the_insecure_environment_setting_is_ignored_for_futureagi(
    clean_hosts, ambient, keys, kinds, monkeypatch, endpoint, variable
):
    monkeypatch.setenv(variable, "true")
    build("OTLP_GRPC", endpoint)
    assert kinds == ["secure_channel"]


def test_insecure_works_for_another_backend(clean_hosts, ambient, kinds):
    build("OTLP_GRPC", "collector.example.test:4317", insecure=True)
    assert kinds == ["insecure_channel"]


class RecordingListener:
    """A TCP listener that keeps the first bytes each client sends."""

    def __init__(self):
        self.received = []
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(8)
        self.sock.settimeout(0.2)
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.serve, daemon=True)

    @property
    def port(self):
        return self.sock.getsockname()[1]

    def serve(self):
        while not self.stop.is_set():
            try:
                conn, _ = self.sock.accept()
            except OSError:
                continue
            conn.settimeout(0.5)
            data = b""
            try:
                while len(data) < 4096:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    data += chunk
            except OSError:
                pass
            self.received.append(data)
            conn.close()

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.stop.set()
        self.thread.join(5)
        self.sock.close()


def send_one_span(exporter):
    with contextlib.suppress(Exception):
        export_spans(exporter)


def test_a_plaintext_listener_gets_no_futureagi_key_bytes(clean_hosts, ambient, keys, monkeypatch):
    with RecordingListener() as listener:
        monkeypatch.setenv("FI_GRPC_URL", f"127.0.0.1:{listener.port}")
        with pytest.raises(ConfigurationError) as refused:
            build("OTLP_GRPC", f"127.0.0.1:{listener.port}", insecure=True, timeout_ms=2000)
        assert refused.value.code == "insecure_loopback_grpc"
    assert listener.received == []


def test_a_listener_sees_a_tls_handshake_and_no_key_from_the_default_futureagi_exporter(
    clean_hosts, ambient, keys, monkeypatch
):
    with RecordingListener() as listener:
        monkeypatch.setenv("FI_GRPC_URL", f"127.0.0.1:{listener.port}")
        send_one_span(build("OTLP_GRPC", f"127.0.0.1:{listener.port}", timeout_ms=2000))
    assert listener.received, "the exporter did not connect"
    first = listener.received[0]
    assert first[:1] == b"\x16", first[:16]
    assert not first.startswith(b"PRI ")
    for data in listener.received:
        assert b"fi-key-value" not in data and b"fi-secret-value" not in data


def test_a_listener_sees_plaintext_http2_from_an_exporter_for_another_backend(clean_hosts, ambient, keys):
    with RecordingListener() as listener:
        send_one_span(build("OTLP_GRPC", f"127.0.0.1:{listener.port}", insecure=True, timeout_ms=2000))
    assert listener.received and listener.received[0].startswith(b"PRI ")
    assert all(b"fi-key-value" not in data for data in listener.received)


@pytest.mark.parametrize("insecure", [None, False, True], ids=["none", "false", "true"])
def test_an_http_target_on_port_80_for_futureagi_is_refused_and_dials_nothing(
    clean_hosts, ambient, keys, channels, monkeypatch, insecure
):
    """``http://grpc.futureagi.com:80`` is refused whatever ``insecure`` holds: no channel and no connection."""
    real = socket.getaddrinfo
    with RecordingListener() as listener:

        def resolve(host, port, *args, **kwargs):
            if isinstance(host, str) and host.lower().rstrip(".").endswith("futureagi.com"):
                host, port = "127.0.0.1", listener.port
            return real(host, port, *args, **kwargs)

        monkeypatch.setattr(socket, "getaddrinfo", resolve)
        with pytest.raises(ConfigurationError) as refused:
            send_one_span(build("OTLP_GRPC", "http://grpc.futureagi.com:80", insecure=insecure, timeout_ms=2000))
    assert refused.value.code == INSECURE_CODE
    assert channels == []
    received = b"".join(listener.received)
    assert (len(listener.received), received.count(b"fi-key-value") + received.count(b"fi-secret-value")) == (0, 0)


# --- a blank endpoint is an unset endpoint -------------------------------------------------------------


def target_of(exporter):
    return exporter._endpoint


def header_names(exporter):
    headers = getattr(exporter, "_headers", None)
    if headers is None:
        headers = exporter._client._headers
    pairs = headers.items() if isinstance(headers, dict) else headers
    return {str(name).lower() for name, _ in pairs}


@pytest.mark.parametrize("blank", WHITESPACE, ids=[repr(b) for b in WHITESPACE])
@pytest.mark.parametrize("kind", ["FUTUREAGI", "OTLP_HTTP", "OTLP_GRPC", "ARIZE", "PHOENIX", "LANGFUSE"])
def test_a_blank_endpoint_is_the_same_as_none(clean_hosts, ambient, keys, kind, blank):
    unset = build(kind, None)
    blanked = build(kind, blank)
    assert target_of(blanked) == target_of(unset)
    assert header_names(blanked) == header_names(unset)


@pytest.mark.parametrize("blank", WHITESPACE, ids=[repr(b) for b in WHITESPACE])
def test_a_blank_base_url_is_the_default_futureagi_endpoint(clean_hosts, ambient, keys, monkeypatch, blank):
    unset = build("FUTUREAGI", None)
    monkeypatch.setenv("FI_BASE_URL", blank)
    blanked = build("FUTUREAGI", None)
    assert target_of(blanked) == target_of(unset) == "https://api.futureagi.com/tracer/v1/traces"
    assert {"x-api-key", "x-secret-key"} <= header_names(blanked)


@pytest.mark.parametrize("wrapped", [" https://collector.example.test/v1/traces", "https://collector.example.test/v1/traces\n"])
def test_a_wrapped_endpoint_is_refused(clean_hosts, ambient, wrapped):
    with pytest.raises(ConfigurationError) as refused:
        build("OTLP_HTTP", wrapped)
    assert refused.value.code == "insecure_http_origin"


# --- the session's adapter map ------------------------------------------------------------------------


def test_a_sealed_adapter_map_refuses_move_to_end():
    from fi._otlp_headers import futureagi_session

    session = futureagi_session()
    with pytest.raises(ConfigurationError) as refused:
        session.adapters.move_to_end("https://")
    assert refused.value.code == "unsupported_session_adapter"
