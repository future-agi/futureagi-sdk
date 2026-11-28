"""Keyed plain-http requests to hosts written with non-ASCII characters, with and without the opt-in.

The HTTP libraries map some non-ASCII hosts to ASCII ones before they connect: ``\\u212a`` (KELVIN SIGN) reads as
``k``, so ``http://\\u212aey.example.test`` is sent to ``key.example.test``. The opt-in does not unlock a host written
with non-ASCII characters, whatever the libraries map it to, so each such request is refused with
``insecure_http_origin`` and reaches no listener.

Listeners run on the loopback interface. The ``net`` fixture of ``test_plain_http_key_guards`` applies here, and
every name ending in ``.test`` (``key.example.test``, the IDNA forms ``xn--...example.test``) and
``plain.example.tesk`` resolve to its target listener as well; other names fail to resolve, so no case reaches a
real host. Each case reads the connection count and the number of bytes holding the marker key at the target and
at the environment proxy.
"""

from __future__ import annotations

import socket

import pytest

from tests.test_plain_http_key_guards import (  # noqa: F401
    EXPECTED,
    gateway_sync,
    legacy,
    net,
    platform_sync,
    refused,
    use_proxy,
)

SENDERS = {"http-client": legacy, "platform-sync": platform_sync, "gateway-sync": gateway_sync}

# Hosts as written, each with the ASCII host the HTTP libraries send it to (or ``None`` when they send it to an
# IDNA ``xn--`` name or reject it).
HOSTS = {
    "kelvin-sign": ("\u212aey.example.test", "key.example.test"),
    "kelvin-sign-upper-case-rest": ("PLAIN.\u212aEY.TEST", "plain.key.test"),
    "kelvin-sign-twice": ("\u212a\u212a.example.test", "kk.example.test"),
    "kelvin-sign-last": ("plain.example.tes\u212a", "plain.example.tesk"),
    "capital-i-with-dot-above": ("\u0130t.example.test", None),
    "dotless-i": ("\u0131t.example.test", None),
    "angstrom-sign": ("\u212bngstrom.example.test", None),
    "long-s": ("\u017fite.example.test", None),
    "sharp-s": ("\u00dfite.example.test", None),
    "fullwidth-k": ("\uff4bey.example.test", None),
    "fullwidth-capital-k": ("\uff2bey.example.test", None),
}

OPT_IN = ["none", "environment", "argument"]
SENT_TO = {sent_to for _, sent_to in HOSTS.values() if sent_to}
LOOPBACK_NAMES = {"127.0.0.1", "::1", "localhost"}


@pytest.fixture(autouse=True)
def resolved_names(monkeypatch, net):
    """Names ending in ``.test`` and the hosts of ``SENT_TO`` resolve to the loopback interface (the target
    listener); any other name that is not a loopback name fails to resolve, so no lookup leaves the machine."""
    shimmed = socket.getaddrinfo

    def shim(host, *args, **kwargs):
        name = host.decode("ascii", "replace") if isinstance(host, bytes) else host
        if isinstance(name, str):
            folded = name.rstrip(".").lower()
            if folded in SENT_TO or folded.endswith(".test"):
                host = "127.0.0.1"
            elif folded not in LOOPBACK_NAMES:
                raise socket.gaierror(socket.EAI_NONAME, f"{name!r} is not resolved in this test")
        return shimmed(host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", shim)


def _send(monkeypatch, sender, base, opt_in):
    kwargs = {}
    if opt_in == "environment":
        monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    elif opt_in == "argument":
        kwargs["allow_insecure_http"] = True
    return SENDERS[sender](base, **kwargs)


def _counts(net):
    return (net.target.connections, net.target.marker_bytes(), net.proxy.connections, net.proxy.marker_bytes())


@pytest.mark.parametrize("opt_in", OPT_IN)
@pytest.mark.parametrize("host", list(HOSTS))
@pytest.mark.parametrize("sender", list(SENDERS))
def test_keyed_plain_http_to_non_ascii_host_is_refused(monkeypatch, net, sender, host, opt_in):
    use_proxy(monkeypatch, net)
    written, _sent_to = HOSTS[host]
    exc = _send(monkeypatch, sender, f"http://{written}:{net.target.port}", opt_in)
    assert _counts(net) == (0, 0, 0, 0), f"{sender} {ascii(written)} opt-in {opt_in}: {net.report()}"
    refused(exc, *EXPECTED[sender])


@pytest.mark.parametrize("opt_in", ["environment", "argument"])
@pytest.mark.parametrize("host", [name for name, (_, sent_to) in HOSTS.items() if sent_to])
@pytest.mark.parametrize("sender", list(SENDERS))
def test_ascii_host_the_libraries_map_to_is_unlocked_by_the_opt_in(monkeypatch, net, sender, host, opt_in):
    """The ASCII host written as such reaches the target listener directly: the listeners and the lookup shim
    record a keyed request that is sent."""
    use_proxy(monkeypatch, net)
    _written, sent_to = HOSTS[host]
    exc = _send(monkeypatch, sender, f"http://{sent_to}:{net.target.port}", opt_in)
    assert (net.proxy.connections, net.proxy.marker_bytes()) == (0, 0), f"{sender} {sent_to}: {net.report()}"
    if net.target.marker_bytes() == 0:
        # 0.9.0 refuses an opted-in plain-http request that an environment proxy would route, and its platform and
        # gateway clients take no allow_insecure_http argument: a refusal before any connection.
        assert exc is not None and _counts(net) == (0, 0, 0, 0), f"{sender} {sent_to}: {net.report()}"
        return
    assert net.target.connections >= 1, f"{sender} {sent_to}: {net.report()}"


def _fullwidth_digits(number: int) -> str:
    return "".join(chr(0xFF10 + int(digit)) for digit in str(number))


@pytest.mark.parametrize("opt_in", OPT_IN)
@pytest.mark.parametrize("sender", list(SENDERS))
def test_keyed_plain_http_with_port_in_fullwidth_digits_is_refused(monkeypatch, net, sender, opt_in):
    """``httpx`` reads a port written in fullwidth digits as the ASCII port; the authority is judged as written."""
    use_proxy(monkeypatch, net)
    base = f"http://plain.example.test:{_fullwidth_digits(net.target.port)}"
    exc = _send(monkeypatch, sender, base, opt_in)
    assert _counts(net) == (0, 0, 0, 0), f"{sender} {ascii(base)} opt-in {opt_in}: {net.report()}"
    refused(exc, *EXPECTED[sender])
