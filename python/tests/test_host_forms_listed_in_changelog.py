"""Keyed plain-``http://`` requests to the host forms the 0.8.1 CHANGELOG entry names.

Each case sends one keyed request from the ``fi.api`` ``HttpClient``, the platform ``Client`` or the ``Gateway`` and
reads what reached each listener on the loopback interface: the connection count and the number of bytes that hold
the marker key. The ``net`` fixture of ``test_plain_http_key_guards.py`` gives a target listener and a proxy
listener; the lookup shim below maps every name and address written here to ``127.0.0.1`` (the zone id forms, the
not-loopback addresses and the names alike), so no case reaches a host other than this one. The egress guard of the
test environment refuses a connection to any other address as a backstop.

Rules under test, as the CHANGELOG states them:

* ``LOCALHOST``, addresses in ``127.0.0.0/8`` and ``::1`` written in full are loopback: sent directly, through no
  proxy;
* ``2130706433`` and ``127.000.000.001`` (an IPv4 address in a whole-number or zero-padded form) and hosts with an
  IPv6 zone id (``%``) are refused, with or without the opt-in;
* ``0.0.0.0``, ``::ffff:127.0.0.1``, ``localhost.localdomain``, ``foo.localhost`` and ``host.docker.internal`` are
  not loopback: refused without the opt-in, sent directly with it.
"""

from __future__ import annotations

import socket
import threading

import pytest

from fi.gateway import AgentCCError
from tests.test_plain_http_key_guards import (  # noqa: F401
    Net,
    Sink,
    gateway_sync,
    legacy,
    net,
    platform_sync,
    refused,
    use_proxy,
)

SENDERS = {"http-client": legacy, "platform-sync": platform_sync, "gateway-sync": gateway_sync}
ERRORS = {"http-client": (ValueError,), "platform-sync": (ValueError,), "gateway-sync": (AgentCCError,)}

# Hosts as written in the URL, and the text the lookup shim may receive for them.
NUMERIC_AND_ZONE_ID_FORMS = ["2130706433", "127.000.000.001", "[fe80::1%25eth0]", "[::1%25lo]"]
NOT_LOOPBACK_FORMS = ["0.0.0.0", "[::ffff:127.0.0.1]", "localhost.localdomain", "foo.localhost", "host.docker.internal"]
_MAPPED_NAMES = {
    "localhost",
    "2130706433",
    "127.000.000.001",
    "0.0.0.0",
    "::ffff:127.0.0.1",
    "localhost.localdomain",
    "foo.localhost",
    "host.docker.internal",
}
_MAPPED_PREFIXES = ("fe80::1%", "::1%")


@pytest.fixture(autouse=True)
def lookups(monkeypatch, net):
    """Maps the names and addresses of this module to ``127.0.0.1`` and records each mapped lookup."""
    seen: list[str] = []
    inner = socket.getaddrinfo

    def shim(host, *args, **kwargs):
        name = host.decode("ascii", "replace") if isinstance(host, bytes) else host
        if isinstance(name, str):
            lowered = name.strip("[]").lower()
            if lowered in _MAPPED_NAMES or lowered.startswith(_MAPPED_PREFIXES):
                seen.append(name)
                host = "127.0.0.1"
        return inner(host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", shim)
    return seen


class _SinkAt(Sink):
    """A ``Sink`` bound to a given loopback address."""

    def __init__(self, address: str, family: int = socket.AF_INET) -> None:
        self.connections = 0
        self.raw = b""
        self._lock = threading.Lock()
        self._sock = socket.socket(family, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((address, 0))
        self._sock.listen(32)
        self.port = self._sock.getsockname()[1]
        self._stop = False
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()


def _send(sender: str, base: str, **kwargs):
    """Sends one keyed request; returns the error raised while building the client or sending, if any."""
    try:
        return SENDERS[sender](base, **kwargs)
    except Exception as exc:
        return exc


def _report(net: Net, lookups: list, extra: Sink | None = None) -> str:
    text = net.report()
    if extra is not None:
        text = f"listener: {extra.connections} connections, {extra.marker_bytes()} marker bytes; " + text
    return f"{text}; mapped lookups: {lookups}"


def _nothing_sent(net: Net, lookups: list) -> None:
    counts = (net.target.connections, net.target.marker_bytes(), net.proxy.connections, net.proxy.marker_bytes())
    assert counts == (0, 0, 0, 0), _report(net, lookups)


def _opt_in(monkeypatch, how: str) -> dict:
    if how == "environment":
        monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
        return {}
    if how == "argument":
        return {"allow_insecure_http": True}
    return {}


senders = pytest.mark.parametrize("sender", list(SENDERS))


# ---------------------------------------------------------------------------------------------
# loopback forms: sent directly, proxy 0
# ---------------------------------------------------------------------------------------------


@senders
def test_upper_case_localhost_is_sent_directly_past_environment_proxy(monkeypatch, net, lookups, sender):
    use_proxy(monkeypatch, net, names=("HTTP_PROXY", "ALL_PROXY"), no_proxy="")
    exc = _send(sender, f"http://LOCALHOST:{net.target.port}")
    assert getattr(exc, "code", None) is None, f"{exc!r}; {_report(net, lookups)}"
    assert net.target.marker_bytes() > 0, _report(net, lookups)
    assert (net.proxy.connections, net.proxy.marker_bytes()) == (0, 0), _report(net, lookups)


@senders
@pytest.mark.parametrize("address", ["127.0.0.2", "127.255.255.254"])
def test_address_in_127_block_is_sent_directly_past_environment_proxy(monkeypatch, net, lookups, sender, address):
    try:
        listener = _SinkAt(address)
    except OSError:
        pytest.skip(f"cannot listen on {address}")
    try:
        use_proxy(monkeypatch, net, names=("HTTP_PROXY", "ALL_PROXY"), no_proxy="")
        exc = _send(sender, f"http://{address}:{listener.port}")
        assert getattr(exc, "code", None) is None, f"{exc!r}; {_report(net, lookups, listener)}"
        assert listener.marker_bytes() > 0, _report(net, lookups, listener)
        assert (net.proxy.connections, net.proxy.marker_bytes()) == (0, 0), _report(net, lookups, listener)
    finally:
        listener.close()


@senders
def test_ipv6_loopback_written_in_full_is_sent_directly_past_environment_proxy(monkeypatch, net, lookups, sender):
    try:
        listener = _SinkAt("::1", socket.AF_INET6)
    except OSError:
        pytest.skip("no IPv6 loopback")
    try:
        use_proxy(monkeypatch, net, names=("HTTP_PROXY", "ALL_PROXY"), no_proxy="")
        exc = _send(sender, f"http://[0:0:0:0:0:0:0:1]:{listener.port}")
        assert getattr(exc, "code", None) is None, f"{exc!r}; {_report(net, lookups, listener)}"
        assert listener.marker_bytes() > 0, _report(net, lookups, listener)
        assert (net.proxy.connections, net.proxy.marker_bytes()) == (0, 0), _report(net, lookups, listener)
    finally:
        listener.close()


# ---------------------------------------------------------------------------------------------
# 2130706433, 127.000.000.001 and zone ids: refused with or without the opt-in
# ---------------------------------------------------------------------------------------------


@senders
@pytest.mark.parametrize("host", NUMERIC_AND_ZONE_ID_FORMS)
@pytest.mark.parametrize("opted_in", ["none", "environment", "argument"])
@pytest.mark.parametrize("proxied", [False, True], ids=["no-proxy", "environment-proxy"])
def test_numeric_and_zone_id_forms_are_refused_with_or_without_opt_in(monkeypatch, net, lookups, sender, host, opted_in, proxied):
    if proxied:
        use_proxy(monkeypatch, net, names=("HTTP_PROXY", "ALL_PROXY"))
    exc = _send(sender, f"http://{host}:{net.target.port}", **_opt_in(monkeypatch, opted_in))
    _nothing_sent(net, lookups)
    refused(exc, *ERRORS[sender])


# ---------------------------------------------------------------------------------------------
# hosts that are not loopback for this rule: refused without the opt-in, sent directly with it
# ---------------------------------------------------------------------------------------------


@senders
@pytest.mark.parametrize("host", NOT_LOOPBACK_FORMS)
@pytest.mark.parametrize("proxied", [False, True], ids=["no-proxy", "environment-proxy"])
def test_not_loopback_forms_are_refused_without_opt_in(monkeypatch, net, lookups, sender, host, proxied):
    if proxied:
        use_proxy(monkeypatch, net, names=("HTTP_PROXY", "ALL_PROXY"))
    exc = _send(sender, f"http://{host}:{net.target.port}")
    _nothing_sent(net, lookups)
    refused(exc, *ERRORS[sender])


@senders
@pytest.mark.parametrize("host", NOT_LOOPBACK_FORMS)
@pytest.mark.parametrize("opted_in", ["environment", "argument"])
def test_not_loopback_forms_with_opt_in_are_sent_directly_past_environment_proxy(monkeypatch, net, lookups, sender, host, opted_in):
    use_proxy(monkeypatch, net, names=("HTTP_PROXY", "ALL_PROXY"))
    exc = _send(sender, f"http://{host}:{net.target.port}", **_opt_in(monkeypatch, opted_in))
    assert getattr(exc, "code", None) is None, f"{exc!r}; {_report(net, lookups)}"
    assert net.target.marker_bytes() > 0, _report(net, lookups)
    assert (net.proxy.connections, net.proxy.marker_bytes()) == (0, 0), _report(net, lookups)
    assert lookups, f"the request did not go through the lookup shim; {_report(net, lookups)}"
