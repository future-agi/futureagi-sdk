"""A loopback gRPC target named by FI_BASE_URL, FI_TRACES_URL or FI_GRPC_URL as a bracketed IPv6 address.

``[::1]`` and the IPv4-mapped ``[::ffff:127.0.0.1]`` are loopback addresses. When one of the three settings names
such an address, a gRPC exporter aimed at it is bound to the SDK's keys, exactly as it is for ``127.0.0.1``:
``insecure=True`` raises ``ConfigurationError`` (code ``insecure_loopback_grpc``) before a channel opens, and a
recording listener on that address receives 0 bytes. Without ``insecure`` the exporter opens TLS.
"""

import contextlib
import socket
import threading

import pytest

from fi.errors import ConfigurationError
from tests.experiments.unit.test_fi_bound_ambiguous_endpoints import build
from tests.experiments.unit.test_fi_bound_authority_forms import clean_hosts  # noqa: F401
from tests.experiments.unit.test_fi_bound_exporter_headers import ambient, export_spans  # noqa: F401
from tests.experiments.unit.test_fi_bound_grpc_target import keys  # noqa: F401

# The values the ``keys`` setup gives FI_API_KEY and FI_SECRET_KEY.
API_MARKER = "fi-key-value"
SECRET_MARKER = "fi-secret-value"
# The written host, and the listener address a socket dialing it reaches.
FORMS = {"ipv6": ("[::1]", ("::1", socket.AF_INET6)), "mapped": ("[::ffff:127.0.0.1]", ("127.0.0.1", socket.AF_INET))}
SETTINGS = {
    "FI_BASE_URL": "http://{host}:{port}",
    "FI_TRACES_URL": "https://{host}:{port}",
    "FI_GRPC_URL": "{host}:{port}",
}
TARGETS = ["{host}:{port}", "http://{host}:{port}", "https://{host}:{port}"]
ALL_FORMS = TARGETS + ["dns:///{host}:{port}", "//{host}:{port}"]


class Listener:
    """A TCP listener on one loopback address that keeps every byte each client sends."""

    def __init__(self, address, family):
        self.received = []
        self.sock = socket.socket(family)
        try:
            self.sock.bind((address, 0))
        except OSError:
            self.sock.close()
            pytest.skip(f"no loopback listener on {address}")
        self.sock.listen(8)
        self.sock.settimeout(0.2)
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.serve, daemon=True)

    @property
    def port(self):
        return self.sock.getsockname()[1]

    @property
    def data(self):
        return b"".join(self.received)

    def serve(self):
        while not self.stop.is_set():
            try:
                conn, _ = self.sock.accept()
            except OSError:
                continue
            conn.settimeout(0.5)
            data = b""
            try:
                while len(data) < 65536:
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


def marker_bytes(data):
    return sum(data.count(marker.encode()) * len(marker) for marker in (API_MARKER, SECRET_MARKER))


def build_and_send(endpoint, **config):
    """Build the exporter; if it is built, send one span through it. Returns the refusal, or None."""
    try:
        exporter = build("OTLP_GRPC", endpoint, timeout_ms=2000, **config)
    except ConfigurationError as refused:
        return refused
    with contextlib.suppress(Exception):
        export_spans(exporter)
    return None


@pytest.mark.parametrize("target", TARGETS)
@pytest.mark.parametrize("caller_headers", [False, True], ids=["sdk-headers", "caller-key-headers"])
@pytest.mark.parametrize("form", sorted(FORMS))
@pytest.mark.parametrize("setting", sorted(SETTINGS))
def test_insecure_true_is_refused_for_a_bracketed_loopback_target_a_setting_names(
    clean_hosts, ambient, keys, monkeypatch, setting, form, caller_headers, target
):
    host, (address, family) = FORMS[form]
    with Listener(address, family) as listener:
        monkeypatch.setenv(setting, SETTINGS[setting].format(host=host, port=listener.port))
        headers = {"x-api-key": API_MARKER, "x-secret-key": SECRET_MARKER} if caller_headers else None
        refused = build_and_send(target.format(host=host, port=listener.port), insecure=True, headers=headers)
    assert marker_bytes(listener.data) == 0
    assert listener.received == []
    assert refused is not None, "the exporter was built and sent"
    assert refused.code == "insecure_loopback_grpc"
    for part in (API_MARKER, SECRET_MARKER, address):
        assert part not in str(refused)


@pytest.mark.parametrize("target", ALL_FORMS)
@pytest.mark.parametrize("caller_headers", [False, True], ids=["sdk-headers", "caller-key-headers"])
@pytest.mark.parametrize("form", sorted(FORMS))
def test_a_bracketed_loopback_target_is_refused_with_the_code_of_127_0_0_1(
    clean_hosts, ambient, keys, monkeypatch, form, caller_headers, target
):
    headers = {"x-api-key": API_MARKER} if caller_headers else None
    codes = []
    for host in ("127.0.0.1", FORMS[form][0]):
        monkeypatch.setenv("FI_GRPC_URL", f"{host}:5999")
        with pytest.raises(ConfigurationError) as refused:
            build("OTLP_GRPC", target.format(host=host, port=5999), insecure=True, headers=headers, timeout_ms=500)
        codes.append(refused.value.code)
    assert codes[1] == codes[0]


@pytest.mark.parametrize("form", sorted(FORMS))
@pytest.mark.parametrize("setting", sorted(SETTINGS))
def test_the_bound_bracketed_loopback_exporter_opens_tls_without_insecure(
    clean_hosts, ambient, keys, monkeypatch, setting, form
):
    host, (address, family) = FORMS[form]
    # gRPC keeps its proxy handling for an IPv4-mapped TLS target, so the proxy settings are cleared here.
    for name in ("grpc_proxy", "https_proxy", "http_proxy", "HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY", "all_proxy"):
        monkeypatch.delenv(name, raising=False)
    with Listener(address, family) as listener:
        monkeypatch.setenv(setting, SETTINGS[setting].format(host=host, port=listener.port))
        assert build_and_send(f"{host}:{listener.port}") is None
    assert listener.received, "the exporter did not connect"
    assert listener.received[0][:1] == b"\x16"
    assert marker_bytes(listener.data) == 0


@pytest.mark.parametrize("form", sorted(FORMS))
def test_an_unnamed_bracketed_loopback_target_is_another_backend(clean_hosts, ambient, keys, form):
    host, (address, family) = FORMS[form]
    with Listener(address, family) as listener:
        assert build_and_send(f"{host}:{listener.port}", insecure=True) is None
    assert listener.received and listener.received[0].startswith(b"PRI ")
    assert marker_bytes(listener.data) == 0


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("[::1]:4317", "::1"),
        ("http://[::1]:4317", "::1"),
        ("https://[::ffff:127.0.0.1]:4317", "::ffff:7f00:1"),
        ("dns:///[::1]:4317", "::1"),
        ("dns:[::1]:4317", "::1"),
        ("DNS:///[::1]:4317", "::1"),
        ("dns://[2001:db8::1]/[::1]:4317", "::1"),
        ("dns://[2001:db8::1]", None),
        ("//[0:0::1]:4317", "::1"),
        ("[2001:db8::2%eth0]:4317", None),
        ("[::1]:99999", None),
        ("ipv6:[::1]:4317", "::1"),
        ("ipv6:///[::1]:4317", "::1"),
        ("ipv6:[::1]:99999", None),
        ("ipv6://[2001:db8::1]/[::1]:4317", "2001:db8::1"),
        ("ipv6:[::1]:4317,[::1]:4318", None),
        ("ipv6:[::1]", None),
        ("ipv6:[::1%lo,eth0]:4317", None),
        ("ipv6:[::1]:4317?label=local", "::1"),
        ("https://[2001:db8::1]:4317/v1/[::1%lo]", "2001:db8::1"),
        ("[::1%25lo]:4317", "::1"),
        ("http://[::1%lo]:4317", "::1"),
        ("[::1%25lo]:99999", None),
        ("https:///[::1%25lo]:4317", None),
        ("http://user@[::1%25lo]:4317", None),
        ("http://user@[::1]:4317", None),
        (" [::1]:4317", None),
    ],
)
def test_a_setting_registers_a_bracketed_address_in_its_compressed_form(clean_hosts, monkeypatch, value, expected):
    from fi._otlp_headers import future_agi_hosts

    monkeypatch.setenv("FI_GRPC_URL", value)
    added = future_agi_hosts() - {"api.futureagi.com", "grpc.futureagi.com"}
    assert added == ({expected} if expected else set())


def test_an_ipv6_host_is_not_matched_inside_another_address(clean_hosts, monkeypatch):
    from fi._otlp_headers import _mentions_future_agi_host

    monkeypatch.setenv("FI_GRPC_URL", "[::1]:4317")
    assert _mentions_future_agi_host("ipv6:[::1]:4317")
    assert not _mentions_future_agi_host("ipv6:[2001:db8::1]:4317")
