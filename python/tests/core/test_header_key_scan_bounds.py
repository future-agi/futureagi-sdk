"""The header key check costs time bounded by the size of the value, and a key inside a large value counts as a key.

``carries_credentials`` reads every header value for ``FI_API_KEY`` / ``FI_SECRET_KEY`` (as written and as the value
decodes). A value of 64 KB or 1 MB (one long base64 run, a long hex run, percent-encoded base64 of base64) is judged
within a bounded time per call, and a loopback request through the SDK client with a 64 KB header that holds no key
completes within a bounded time. A large value that holds the key (inside a base64 run or random words, in any of the
encodings the check reads) counts as carrying a key: a value of up to 64 KiB characters by the scan, and a longer value
for its length, without a scan; the plain-http rule refuses it before a connection is opened.

The keys are made at run time. The request target is a loopback listener that reads a whole request head of any size
and answers ``200``; the plain-http controls use the loopback sinks of ``test_header_key_senders`` (``rig``)."""

import base64
import os
import random
import secrets
import socket
import string
import threading
import time
import urllib.parse

import pytest

from fi._core.proxy_routing import carries_credentials
from fi.api.auth import HttpClient
from fi.api.types import HttpMethod, RequestConfig
from tests.experiments.unit.test_header_key_senders import proxied, refused, remote, rig  # noqa: F401  (rig by name)

KB64 = 64 * 1024
MB1 = 1024 * 1024
# Seconds per judged value (the median of three calls), and per loopback request (the median of three requests). A scan
# whose work grows with the value's size takes milliseconds for these sizes, and a loopback request without the scan
# takes about 10 ms; the bounds leave room for a loaded machine.
BOUND = {KB64: 0.1, MB1: 0.75}
REQUEST_BOUND = 0.25


def base64_run(size):
    return base64.b64encode(os.urandom(size)).decode("ascii")[:size]


def hex_run(size):
    return secrets.token_hex(size // 2 + 1)[:size]


def quoted_base64_of_base64(size):
    raw = os.urandom(size)
    return urllib.parse.quote(base64.b64encode(base64.b64encode(raw)).decode("ascii"), safe="")[:size]


def random_words(size):
    pick = random.Random(secrets.randbits(64))
    alphabet = string.ascii_letters + string.digits
    parts, total = [], 0
    while total < size:
        word = "".join(pick.choice(alphabet) for _ in range(pick.randint(64, 256)))
        parts.append(word)
        total += len(word) + 1
    return " ".join(parts)[:size]


SHAPES = {"base64 run": base64_run, "hex run": hex_run, "percent-encoded base64 of base64": quoted_base64_of_base64}
TIMED = [(KB64, "base64 run"), (KB64, "percent-encoded base64 of base64"),
         (MB1, "base64 run"), (MB1, "hex run"), (MB1, "percent-encoded base64 of base64")]


@pytest.fixture
def key(monkeypatch):
    for name in ("FI_API_KEY", "FI_SECRET_KEY", "FI_EXTRA_HEADERS"):
        monkeypatch.delenv(name, raising=False)
    made = "fi-scan-" + secrets.token_hex(12)
    monkeypatch.setenv("FI_API_KEY", made)
    return made


def median_seconds(call, bound):
    """The median of three timed calls of ``call``; the third call is skipped when the first two fall on the same side
    of ``bound`` (the median is then known)."""
    times = []
    for _ in range(3):
        start = time.perf_counter()
        call()
        times.append(time.perf_counter() - start)
        if len(times) == 2 and (min(times) > bound or max(times) <= bound):
            break
    return sorted(times)[len(times) // 2]


@pytest.mark.parametrize("size,shape", TIMED, ids=[f"{size // 1024}KB {shape}" for size, shape in TIMED])
def test_judging_a_large_header_value_takes_bounded_time(key, size, shape):
    value = SHAPES[shape](size)
    assert len(value) == size and key.lower() not in value.lower()
    headers = {"X-Trace": value}
    seconds = median_seconds(lambda: carries_credentials(headers), BOUND[size])
    assert seconds <= BOUND[size], f"{size} bytes ({shape}) judged in {seconds:.3f} s (bound {BOUND[size]} s)"


class HeadListener:
    """A loopback listener that reads a request head of any size, answers ``200`` with ``{}``, and keeps what it read."""

    def __init__(self):
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(8)
        self.sock.settimeout(0.1)
        self.port = self.sock.getsockname()[1]
        self.connections = 0
        self.received = bytearray()
        self.stop = threading.Event()
        threading.Thread(target=self.serve, daemon=True).start()

    def serve(self):
        while not self.stop.is_set():
            try:
                conn, _ = self.sock.accept()
            except OSError:
                continue
            self.connections += 1
            threading.Thread(target=self.talk, args=(conn,), daemon=True).start()

    def talk(self, conn):
        conn.settimeout(1.0)
        data = bytearray()
        deadline = time.monotonic() + 30
        try:
            while b"\r\n\r\n" not in data and time.monotonic() < deadline:
                try:
                    chunk = conn.recv(65536)
                except TimeoutError:
                    continue
                if not chunk:
                    break
                data += chunk
            self.received += data
            if b"\r\n\r\n" in data:
                conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nContent-Type: application/json\r\n\r\n{}")
        except OSError:
            pass
        finally:
            conn.close()

    def close(self):
        self.stop.set()
        self.sock.close()


@pytest.fixture
def listener():
    made = HeadListener()
    yield made
    made.close()


@pytest.mark.parametrize("shape", ["base64 run", "percent-encoded base64 of base64"])
def test_a_loopback_request_with_a_64kb_header_without_a_key_completes_in_bounded_time(key, listener, shape):
    value = SHAPES[shape](KB64)
    assert key.lower() not in value.lower()
    base = f"http://127.0.0.1:{listener.port}"

    def one_request():
        client = HttpClient(base_url=base)
        try:
            config = RequestConfig(method=HttpMethod.GET, url=f"{base}/probe", headers={"X-Trace": value},
                                   retry_attempts=1, timeout=60)
            assert client.request(config).status_code == 200
        finally:
            client.close()

    seconds = median_seconds(one_request, REQUEST_BOUND)
    assert listener.connections >= 1 and value.encode("ascii") in bytes(listener.received)
    assert bytes(listener.received).lower().count(key.encode("ascii")) == 0
    assert seconds <= REQUEST_BOUND, f"loopback request with a 64 KB {shape} header took {seconds:.3f} s"


def b64(text, offset_pad=""):
    return base64.b64encode((offset_pad + text).encode("ascii")).decode("ascii")


def every_byte_quoted(text):
    return "".join(f"%{byte:02X}" for byte in text.encode("ascii"))


FORMS = {
    "as written": lambda key: key,
    "upper case": lambda key: key.upper(),
    "base64 at offset 2": lambda key: b64(key, "ab"),
    "every byte percent-encoded": every_byte_quoted,
    "hex": lambda key: key.encode("ascii").hex(),
    "basic credential": lambda key: "Basic " + b64("user:" + key),
}
CARRIERS = {"base64 run": base64_run, "random words": random_words}


@pytest.mark.parametrize("carrier", list(CARRIERS))
@pytest.mark.parametrize("form", list(FORMS))
@pytest.mark.parametrize("size", [KB64, MB1], ids=["64KB", "1MB"])
def test_a_key_inside_a_large_value_counts_as_a_key(key, size, form, carrier):
    hidden = FORMS[form](key)
    around = CARRIERS[carrier](size)
    middle = size // 2
    value = around[:middle] + " " + hidden + " " + around[middle:]
    assert carries_credentials({"X-Trace": value})
    assert carries_credentials([("X-Trace", value.encode("latin-1"))])


def wire_hits(rig, key):  # noqa: F811
    blob = b"".join(b"".join(sink.data) for sink in rig.sinks).lower()
    return blob.count(key.encode("ascii")) + blob.count(b64(key, "ab").encode("ascii").lower())


@pytest.mark.parametrize("with_proxy", [False, True], ids=["direct", "environment proxy"])
def test_a_large_value_holding_the_key_is_refused_on_plain_http_before_a_connection(rig, key, monkeypatch, with_proxy):  # noqa: F811
    if with_proxy:
        proxied(rig, monkeypatch)
    value = base64_run(MB1 // 2) + b64(key, "ab") + base64_run(MB1 // 2)
    base = remote(rig.target)
    client = HttpClient(base_url=base)
    try:
        client.request(RequestConfig(method=HttpMethod.GET, url=f"{base}/probe", headers={"X-Trace": value},
                                     retry_attempts=1))
        error = None
    except Exception as caught:  # noqa: BLE001 - the kind of failure is what the test reads
        error = caught
    finally:
        client.close()
    assert refused(error), error
    assert key not in str(error)
    assert rig.connections() == 0 and wire_hits(rig, key) == 0
