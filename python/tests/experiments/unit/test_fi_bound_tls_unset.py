# ruff: noqa: F811
"""A gRPC exporter for Future AGI is TLS whatever ``insecure`` holds, and Future AGI hosts take HTTP only over https.

``insecure=None`` is upstream's "decide from the environment and the scheme" value, so on a Future AGI host
the exporter is built with ``insecure=False`` instead: an ``http://`` target, ``OTEL_EXPORTER_OTLP_INSECURE`` and
``OTEL_EXPORTER_OTLP_TRACES_INSECURE`` leave the channel TLS. A listener that answers the HTTP/2 preface with
SETTINGS (so a plain client goes on to send its headers) sees a TLS handshake and no key bytes.

Requests over HTTP to a Future AGI host raise ``InsecureHttpRefusedError`` (a ``ConfigurationError``, code
``INSECURE_HTTP_REFUSED``). Loopback and a self-managed base named in ``FI_BASE_URL`` can use ``http://``.
"""

import contextlib
import socket
import threading
import time

import pytest

from fi.errors import ConfigurationError
from tests.experiments.unit.test_fi_bound_ambiguous_endpoints import build
from tests.experiments.unit.test_fi_bound_authority_forms import clean_hosts  # noqa: F401
from tests.experiments.unit.test_fi_bound_exporter_headers import (  # noqa: F401
    ambient,
    export_spans,
    sink,
)
from tests.experiments.unit.test_fi_bound_grpc_target import keys  # noqa: F401

SETTINGS = b"\x00\x00\x00\x04\x00\x00\x00\x00\x00"
KEY_BYTES = (b"fi-key-value", b"fi-secret-value", b"x-api-key", b"x-secret-key")
INSECURE_VARIABLES = {
    "none": {},
    "general": {"OTEL_EXPORTER_OTLP_INSECURE": "true"},
    "traces": {"OTEL_EXPORTER_OTLP_TRACES_INSECURE": "true"},
    "both": {"OTEL_EXPORTER_OTLP_INSECURE": "true", "OTEL_EXPORTER_OTLP_TRACES_INSECURE": "true"},
}


class Recorder:
    """A TCP listener that keeps what each client sends and answers an HTTP/2 preface with SETTINGS."""

    def __init__(self):
        self.received = []
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(8)
        self.sock.settimeout(0.2)
        self.stop = threading.Event()
        self.threads = [threading.Thread(target=self.serve, daemon=True)]

    @property
    def port(self):
        return self.sock.getsockname()[1]

    def serve(self):
        while not self.stop.is_set():
            try:
                conn, _ = self.sock.accept()
            except OSError:
                continue
            worker = threading.Thread(target=self.talk, args=(conn,), daemon=True)
            self.threads.append(worker)
            worker.start()

    def talk(self, conn):
        conn.settimeout(0.3)
        data = b""
        answered = False
        deadline = time.monotonic() + 2.5
        while time.monotonic() < deadline and len(data) < 16384:
            try:
                chunk = conn.recv(4096)
            except TimeoutError:
                continue
            except OSError:
                break
            if not chunk:
                break
            data += chunk
            if data.startswith(b"PRI ") and not answered:
                answered = True
                with_error = False
                try:
                    conn.sendall(SETTINGS)
                except OSError:
                    with_error = True
                if with_error:
                    break
        self.received.append(data)
        conn.close()

    def __enter__(self):
        self.threads[0].start()
        return self

    def __exit__(self, *exc):
        self.stop.set()
        for thread in self.threads:
            thread.join(5)
        self.sock.close()


def send_one_span(exporter):
    # The listener is no collector; only what it received matters.
    with contextlib.suppress(Exception):
        export_spans(exporter)


def tls_only(recorder):
    assert recorder.received, "the exporter did not connect"
    for data in recorder.received:
        assert data[:1] == b"\x16", data[:16]
        assert not data.startswith(b"PRI ")
        assert all(part not in data for part in KEY_BYTES)


@pytest.mark.parametrize("variables", INSECURE_VARIABLES.values(), ids=INSECURE_VARIABLES.keys())
@pytest.mark.parametrize("scheme", ["", "http://"], ids=["host", "http"])
def test_an_unset_insecure_value_opens_a_tls_channel(clean_hosts, ambient, keys, monkeypatch, scheme, variables):
    for name, value in variables.items():
        monkeypatch.setenv(name, value)
    with Recorder() as recorder:
        monkeypatch.setenv("FI_GRPC_URL", f"127.0.0.1:{recorder.port}")
        send_one_span(build("OTLP_GRPC", f"{scheme}127.0.0.1:{recorder.port}", insecure=None, timeout_ms=2000))
    tls_only(recorder)


@pytest.mark.parametrize("variables", INSECURE_VARIABLES.values(), ids=INSECURE_VARIABLES.keys())
def test_the_default_insecure_value_opens_a_tls_channel(clean_hosts, ambient, keys, monkeypatch, variables):
    for name, value in variables.items():
        monkeypatch.setenv(name, value)
    with Recorder() as recorder:
        monkeypatch.setenv("FI_GRPC_URL", f"http://127.0.0.1:{recorder.port}")
        send_one_span(build("OTLP_GRPC", f"http://127.0.0.1:{recorder.port}", timeout_ms=2000))
    tls_only(recorder)


@pytest.mark.parametrize("value", [True, 1, "true", "yes"])
def test_any_truthy_insecure_value_is_refused_for_futureagi(clean_hosts, ambient, keys, value):
    with pytest.raises(ConfigurationError) as refused:
        build("OTLP_GRPC", "grpc.futureagi.com:443", insecure=value)
    assert refused.value.code == "INSECURE_HTTP_REFUSED"


@pytest.mark.parametrize("variables", INSECURE_VARIABLES.values(), ids=INSECURE_VARIABLES.keys())
@pytest.mark.parametrize("insecure", [None, False, "default"], ids=["none", "false", "default"])
def test_an_http_target_on_port_80_for_futureagi_is_refused_and_gets_no_connection(
    clean_hosts, ambient, keys, monkeypatch, insecure, variables
):
    """``http://grpc.futureagi.com:80`` with an unset or false ``insecure`` is refused before any channel opens."""
    for name, value in variables.items():
        monkeypatch.setenv(name, value)
    options = {} if insecure == "default" else {"insecure": insecure}
    real = socket.getaddrinfo
    with Recorder() as recorder:

        def resolve(host, port, *args, **kwargs):
            if isinstance(host, str) and host.lower().rstrip(".").endswith("futureagi.com"):
                host, port = "127.0.0.1", recorder.port
            return real(host, port, *args, **kwargs)

        monkeypatch.setattr(socket, "getaddrinfo", resolve)
        with pytest.raises(ConfigurationError) as refused:
            send_one_span(build("OTLP_GRPC", "http://grpc.futureagi.com:80", timeout_ms=2000, **options))
    assert refused.value.code == "INSECURE_HTTP_REFUSED"
    received = b"".join(recorder.received)
    assert (len(recorder.received), sum(received.count(part) for part in KEY_BYTES)) == (0, 0)


@pytest.mark.parametrize("variables", INSECURE_VARIABLES.values(), ids=INSECURE_VARIABLES.keys())
def test_an_unset_insecure_value_keeps_the_environment_choice_for_another_backend(
    clean_hosts, ambient, monkeypatch, variables
):
    for name, value in variables.items():
        monkeypatch.setenv(name, value)
    with Recorder() as recorder:
        send_one_span(build("OTLP_GRPC", f"127.0.0.1:{recorder.port}", insecure=None, timeout_ms=2000))
    assert recorder.received
    plain = recorder.received[0].startswith(b"PRI ")
    assert plain == bool(variables)


# --- HTTP exporters: a Future AGI host takes https only ------------------------------------------------

HTTP_KINDS = ["FUTUREAGI", "OTLP_HTTP", "ARIZE", "PHOENIX", "LANGFUSE"]
FUTUREAGI_HTTP = [
    "http://api.futureagi.com/tracer/v1/traces",
    "http://api.futureagi.com:80/tracer/v1/traces",
    "http://API.FutureAGI.com./tracer/v1/traces",
    "http://eu.api.futureagi.com/tracer/v1/traces",
    "http://futureagi.com/tracer/v1/traces",
]


@pytest.fixture
def mapped(monkeypatch, sink):
    """Names under futureagi.com resolve to the local sink, so nothing leaves this machine."""
    real = socket.getaddrinfo

    def resolve(host, port, *args, **kwargs):
        if isinstance(host, str) and host.lower().rstrip(".").endswith("futureagi.com"):
            host, port = "127.0.0.1", sink.server.server_address[1]
        return real(host, port, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    return sink


@pytest.mark.parametrize("endpoint", FUTUREAGI_HTTP)
@pytest.mark.parametrize("kind", HTTP_KINDS)
def test_a_futureagi_host_over_http_is_refused_and_gets_no_key(
    mapped, clean_hosts, ambient, keys, kind, endpoint
):
    with pytest.raises(ConfigurationError) as refused:
        send_one_span(build(kind, endpoint))
    assert refused.value.code == "INSECURE_HTTP_REFUSED"
    assert mapped.requests == []
    message = str(refused.value).lower()
    assert "fi-key-value" not in message and "fi-secret-value" not in message


def test_a_futureagi_base_url_over_http_is_refused(mapped, clean_hosts, ambient, keys, monkeypatch):
    monkeypatch.setenv("FI_BASE_URL", "http://api.futureagi.com")
    with pytest.raises(ConfigurationError) as refused:
        send_one_span(build("FUTUREAGI", None))
    assert refused.value.code == "INSECURE_HTTP_REFUSED"
    assert mapped.requests == []


def test_a_loopback_host_over_http_works(clean_hosts, ambient, keys, sink):
    send_one_span(build("FUTUREAGI", sink.base + "/tracer/v1/traces"))
    assert len(sink.requests) == 1
    assert sink.requests[0]["x-api-key"] == "fi-key-value"


def test_a_self_hosted_base_named_in_the_base_url_works_over_http(clean_hosts, ambient, keys, sink, monkeypatch):
    monkeypatch.setenv("FI_BASE_URL", sink.base)
    send_one_span(build("FUTUREAGI", None))
    assert len(sink.requests) == 1
    assert sink.requests[0]["x-api-key"] == "fi-key-value"


def test_https_to_a_futureagi_host_is_built(clean_hosts, ambient, keys):
    exporter = build("FUTUREAGI", "https://api.futureagi.com/tracer/v1/traces")
    assert exporter is not None


# --- items that change public text and one blank rule ----------------------------------------------------


def target_of(exporter):
    return exporter._endpoint


@pytest.mark.parametrize("kind", ["ARIZE", "PHOENIX", "LANGFUSE"])
@pytest.mark.parametrize("blank", [" ", "\t", "  \n"])
def test_a_blank_traces_endpoint_setting_is_an_unset_one(clean_hosts, ambient, monkeypatch, kind, blank):
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", raising=False)
    unset = build(kind, None)
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", blank)
    blanked = build(kind, None)
    assert target_of(blanked) == target_of(unset)


@pytest.mark.parametrize("kind", ["ARIZE", "PHOENIX", "LANGFUSE"])
def test_a_blank_traces_endpoint_setting_falls_back_to_the_general_one(clean_hosts, ambient, monkeypatch, kind):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", " ")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "https://collector.example.test")
    assert target_of(build(kind, None)) == "https://collector.example.test/v1/traces"


BANNED = ("never", "cleartext", "evil", "attack", "leak", "vulnerab", "exploit", "forward", "look like")


def public_text():
    from fi import _otlp_headers

    return {
        "_normalized_host": _otlp_headers._normalized_host.__doc__,
        "futureagi_session": _otlp_headers.futureagi_session.__doc__,
        "_ADAPTER_REFUSAL": _otlp_headers._ADAPTER_REFUSAL,
        "grpc_dial_target": _otlp_headers.grpc_dial_target.__doc__,
    }


@pytest.mark.parametrize("name", ["_normalized_host", "futureagi_session", "_ADAPTER_REFUSAL", "grpc_dial_target"])
def test_the_public_text_states_behaviour_and_no_risk(name):
    text = public_text()[name].lower()
    assert [word for word in BANNED if word in text] == []


def test_the_adapter_refusal_names_the_rule_and_the_remedy():
    from fi._otlp_headers import _ADAPTER_REFUSAL

    assert "only" in _ADAPTER_REFUSAL and "HTTPAdapter" in _ADAPTER_REFUSAL
    assert "remove" in _ADAPTER_REFUSAL.lower() or "use" in _ADAPTER_REFUSAL.lower()


def test_the_dial_target_example_is_a_neutral_one():
    from fi._otlp_headers import grpc_dial_target

    assert "resolver" not in grpc_dial_target.__doc__.lower()
    assert "dns://collector.example/other.example" not in grpc_dial_target.__doc__


def test_the_unsafe_target_check_has_a_neutral_name():
    from fi import _otlp_headers

    assert not hasattr(_otlp_headers, "refuse_unsafe_exporter_target")
    assert callable(_otlp_headers.refuse_unreadable_exporter_target)
