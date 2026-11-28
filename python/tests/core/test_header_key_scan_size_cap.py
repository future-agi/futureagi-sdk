"""A header value longer than 64 KiB counts as holding a key without being scanned; a value up to 64 KiB is scanned.

The keyed checks read each header value for ``FI_API_KEY`` / ``FI_SECRET_KEY`` as written and as it decodes. A value of
up to 64 KiB is judged by that scan. A longer value is judged as holding a key at once, so the keyed rules (plain http to
a non-loopback host refused without the opt-in) apply to it, and a 1 MB value built to make the scan slow (nested
percent-encoding, many short base64 runs) is judged in a few milliseconds.

Keys and markers are made at run time, one per test. Host names resolve to the loopback address (``getaddrinfo`` is
replaced for the test); the listeners bind ``127.0.0.1`` and ``::1`` on one port, open a tunnel for ``CONNECT`` and
count the marker bytes they receive."""

import base64
import contextlib
import os
import secrets
import socket
import threading
import time
import types
import urllib.parse

import pytest

from fi._core.header_key_scan import holds_key
from fi._core.proxy_routing import carries_credentials
from fi.api.auth import HttpClient
from fi.api.types import HttpMethod, RequestConfig
from fi.errors import ConfigurationError

CAP = 64 * 1024
MB1 = 1024 * 1024
FAST = 0.05  # seconds for one judged 1 MB value
PROXY_NAMES = ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy", "NO_PROXY",
               "no_proxy")


def quoted(text):
    return urllib.parse.quote(text, safe="")


def b64(text):
    return base64.b64encode(text.encode("latin-1")).decode("ascii")


def filled(make, size):
    parts, total = [], 0
    while total < size:
        part = make()
        parts.append(part)
        total += len(part)
    return "".join(parts)[:size]


def base64_run(size):
    return base64.b64encode(os.urandom(size)).decode("ascii")[:size]


def nested_percent_encoding(size, key):
    """Short random runs, each percent-encoded three times over base64 of base64 of hex."""
    return filled(lambda: quoted(quoted(quoted(b64(b64(os.urandom(len(key)).hex()))))) + " ", size)


def many_base64_runs(size, key):
    """Short runs of base64 of base64 of hex, each about as long as the key, split by spaces."""
    return filled(lambda: b64(b64(os.urandom(len(key)).hex())) + " ", size)


def with_marker(marker, size):
    """A value of exactly ``size`` characters: a random base64 run with ``marker`` in the middle."""
    around = base64_run(size - len(marker))
    middle = len(around) // 2
    return around[:middle] + marker + around[middle:]


@pytest.fixture
def key(monkeypatch):
    for name in ("FI_API_KEY", "FI_SECRET_KEY", "FI_EXTRA_HEADERS", "FI_ALLOW_INSECURE_HTTP") + PROXY_NAMES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("FI_LOGIN_FILE", "/nonexistent/login.json")
    made = "fi-cap-key-" + secrets.token_hex(12)
    monkeypatch.setenv("FI_API_KEY", made)
    return made


@pytest.fixture
def marker():
    return "capmarker" + secrets.token_hex(10)


def test_a_value_one_character_over_the_cap_without_a_key_counts_as_holding_a_key(key):
    value = base64_run(CAP + 1)
    assert key.lower() not in value.lower()
    assert holds_key(value, [key])
    assert carries_credentials({"X-Trace": value})
    assert carries_credentials([("X-Trace", value.encode("latin-1"))])


def test_a_value_at_the_cap_without_a_key_does_not_count_as_holding_a_key(key):
    value = base64_run(CAP)
    assert key.lower() not in value.lower()
    assert not holds_key(value, [key])
    assert not carries_credentials({"X-Trace": value})
    assert not carries_credentials([("X-Trace", value.encode("latin-1"))])


def test_a_value_at_the_cap_holding_the_key_counts_as_holding_it(key):
    value = with_marker(b64("ab" + key), CAP)
    assert len(value) == CAP
    assert holds_key(value, [key])
    assert carries_credentials({"X-Trace": value})


def test_a_value_over_the_cap_holds_nothing_when_there_is_no_key():
    assert not holds_key(base64_run(CAP + 1), [])


@pytest.mark.parametrize("shape", [nested_percent_encoding, many_base64_runs],
                         ids=["nested percent-encoding", "many base64 runs"])
def test_a_slow_to_scan_1mb_value_is_judged_in_under_50_ms(key, shape):
    value = shape(MB1, key)
    assert len(value) == MB1 and key.lower() not in value.lower()
    headers = {"X-Trace": value}
    best = None
    for _ in range(3):
        start = time.perf_counter()
        keyed = carries_credentials(headers)
        seconds = time.perf_counter() - start
        best = seconds if best is None else min(best, seconds)
    assert best < FAST, f"1 MB value judged in {best:.3f} s (bound {FAST} s)"
    assert keyed


class Sink:
    """A listener on ``127.0.0.1`` and ``::1`` (one port) that reads a request head of any size, opens a tunnel for
    ``CONNECT``, answers ``200`` with ``{}`` and keeps what it received."""

    def __init__(self):
        self.received = bytearray()
        self.connections = 0
        self.stop = threading.Event()
        self.socks = self.bind_both()
        self.port = self.socks[0].getsockname()[1]
        for sock in self.socks:
            sock.listen(16)
            sock.settimeout(0.1)
            threading.Thread(target=self.serve, args=(sock,), daemon=True).start()

    @staticmethod
    def bind_both():
        for _ in range(50):
            v4 = socket.socket()
            v4.bind(("127.0.0.1", 0))
            try:
                v6 = socket.socket(socket.AF_INET6)
                v6.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
                v6.bind(("::1", v4.getsockname()[1]))
            except OSError:
                v4.close()
                continue
            return [v4, v6]
        pytest.skip("no ::1 listener on this machine")

    def serve(self, sock):
        while not self.stop.is_set():
            try:
                conn, _ = sock.accept()
            except OSError:
                continue
            self.connections += 1
            threading.Thread(target=self.talk, args=(conn,), daemon=True).start()

    def talk(self, conn):
        conn.settimeout(0.5)
        data = bytearray()
        deadline = time.monotonic() + 20
        try:
            while time.monotonic() < deadline and not self.stop.is_set():
                try:
                    chunk = conn.recv(65536)
                except TimeoutError:
                    continue
                if not chunk:
                    break
                data += chunk
                self.received += chunk
                if b"\r\n\r\n" not in data:
                    continue
                head, data = data.split(b"\r\n\r\n", 1)
                if head.startswith(b"CONNECT "):
                    conn.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
                    continue
                conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nContent-Type: application/json\r\n"
                             b"Connection: close\r\n\r\n{}")
                break
        except OSError:
            pass
        finally:
            with contextlib.suppress(OSError):
                conn.close()

    def marker_bytes(self, marker):
        return bytes(self.received).count(marker.encode("ascii")) * len(marker)

    def close(self):
        self.stop.set()
        for sock in self.socks:
            with contextlib.suppress(OSError):
                sock.close()


@pytest.fixture
def sinks(key, monkeypatch):
    real = socket.getaddrinfo

    def resolve(host, *args, **kwargs):
        name = host.decode("ascii", "replace") if isinstance(host, bytes) else host
        if isinstance(name, str) and name.endswith(".test"):
            host = "127.0.0.1"
        return real(host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    from fi.api import auth

    monkeypatch.setattr(auth, "time", types.SimpleNamespace(sleep=lambda seconds: None))
    made = types.SimpleNamespace(target=Sink(), proxy=Sink())
    yield made
    made.target.close()
    made.proxy.close()


def send(base, value):
    """``HttpClient.request`` of ``GET base/probe`` with the header ``X-Trace: value``: the error raised, or ``None``."""
    client = HttpClient(base_url=base)
    try:
        response = client.request(RequestConfig(method=HttpMethod.GET, url=f"{base}/probe",
                                                headers={"X-Trace": value}, retry_attempts=1, timeout=30))
        assert response.status_code == 200
        return None
    except ConfigurationError as error:
        return error
    finally:
        client.close()


def refused(error):
    return isinstance(error, ConfigurationError) and error.code == "insecure_http_origin"


def wait_for(sink, marker):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and sink.marker_bytes(marker) == 0:
        time.sleep(0.02)
    return sink.marker_bytes(marker)


@pytest.mark.parametrize("through_proxy", [False, True], ids=["direct", "environment proxy"])
def test_a_value_over_the_cap_is_refused_on_plain_http_to_a_non_loopback_host(sinks, key, marker, monkeypatch,
                                                                             through_proxy):
    if through_proxy:
        for name in ("HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy"):
            monkeypatch.setenv(name, f"http://127.0.0.1:{sinks.proxy.port}")
    value = with_marker(marker, CAP + 1)
    error = send(f"http://plain.example.test:{sinks.target.port}", value)
    delivered = sinks.target.marker_bytes(marker) + sinks.proxy.marker_bytes(marker)
    assert delivered == 0, f"{delivered} marker bytes received"
    assert sinks.target.connections == 0 and sinks.proxy.connections == 0
    assert refused(error), error
    assert marker not in str(error) and key not in str(error)


@pytest.mark.parametrize("host", ["127.0.0.1", "[::1]"])
def test_a_value_over_the_cap_reaches_a_loopback_host(sinks, marker, host):
    assert send(f"http://{host}:{sinks.target.port}", with_marker(marker, CAP + 1)) is None
    assert wait_for(sinks.target, marker) == len(marker)


def test_a_value_over_the_cap_reaches_a_non_loopback_host_with_the_opt_in(sinks, marker, monkeypatch):
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    assert send(f"http://plain.example.test:{sinks.target.port}", with_marker(marker, CAP + 1)) is None
    assert wait_for(sinks.target, marker) == len(marker)


def test_a_value_at_the_cap_without_a_key_reaches_a_non_loopback_host(sinks, marker):
    assert send(f"http://plain.example.test:{sinks.target.port}", with_marker(marker, CAP)) is None
    assert wait_for(sinks.target, marker) == len(marker)
