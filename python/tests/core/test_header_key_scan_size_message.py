"""A refusal that rests on the 64 KiB scan limit says so.

While ``FI_API_KEY`` or ``FI_SECRET_KEY`` is set, a header value longer than 65,536 characters is not scanned and counts
as holding a key, so plain http to a host that is not loopback is refused without ``FI_ALLOW_INSECURE_HTTP=1``. When no
credential header and no scanned value holds a key, the message names the limit and what to do (an https:// address or
a shorter value); the error class and ``code`` are the plain-http refusal's own. A refusal for a key the scan found, or
for a credential header, carries the plain-http message alone.

Senders: ``HttpClient.request`` (``requests``), the OTLP HTTP exporter (a ``requests`` session) and the OTLP gRPC
exporter. Host names resolve to a loopback listener (``getaddrinfo`` is replaced for the test) that counts connections
and the marker bytes it receives. Keys and markers are made at run time."""

import base64
import os
import secrets
import socket
import types

import pytest

from fi.api.auth import HttpClient
from fi.api.types import HttpMethod, RequestConfig
from fi.errors import ConfigurationError
from tests.core.test_header_key_scan_size_cap import PROXY_NAMES, Sink

CAP = 64 * 1024
SIZE_WORDS = ("65,536", "64 KiB")


def benign(size, marker):
    """A value of exactly ``size`` characters: a random base64 run with ``marker`` in the middle."""
    around = base64.b64encode(os.urandom(size)).decode("ascii")[: size - len(marker)]
    return around[: len(around) // 2] + marker + around[len(around) // 2:]


@pytest.fixture
def key(monkeypatch):
    for name in ("FI_API_KEY", "FI_SECRET_KEY", "FI_EXTRA_HEADERS", "FI_ALLOW_INSECURE_HTTP") + PROXY_NAMES:
        monkeypatch.delenv(name, raising=False)
    for name in [name for name in os.environ if name.startswith("OTEL_EXPORTER_OTLP")]:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("FI_LOGIN_FILE", "/nonexistent/login.json")
    made = "MARKERKEY-A-" + secrets.token_hex(12)
    monkeypatch.setenv("FI_API_KEY", made)
    return made


@pytest.fixture
def marker():
    return "sizemarker" + secrets.token_hex(10)


@pytest.fixture
def sink(key, monkeypatch):
    real = socket.getaddrinfo

    def resolve(host, *args, **kwargs):
        name = host.decode("ascii", "replace") if isinstance(host, bytes) else host
        if isinstance(name, str) and name.endswith(".test"):
            host = "127.0.0.1"
        return real(host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    from fi.api import auth

    monkeypatch.setattr(auth, "time", types.SimpleNamespace(sleep=lambda seconds: None))
    made = Sink()
    yield made
    made.close()


def via_http_client(base, headers):
    client = HttpClient(base_url=base)
    try:
        client.request(RequestConfig(method=HttpMethod.GET, url=f"{base}/probe", headers=headers, retry_attempts=1,
                                     timeout=30))
    finally:
        client.close()


def via_exporter(kind):
    def build(base, headers):
        from fi.evals.otel._tracer_factories import _create_exporter
        from fi.evals.otel.config import ExporterConfig
        from fi.evals.otel.types import ExporterType

        if kind == "grpc":
            config = ExporterConfig(type=ExporterType.OTLP_GRPC, endpoint=base, headers=headers, timeout_ms=1000)
        else:
            config = ExporterConfig(type=ExporterType.OTLP_HTTP, endpoint=f"{base}/v1/traces", headers=headers,
                                    timeout_ms=1000)
        _create_exporter(config)

    return build


SENDERS = {
    "HttpClient.request (requests)": via_http_client,
    "OTLP HTTP exporter (requests session)": via_exporter("http"),
    "OTLP gRPC exporter": via_exporter("grpc"),
}


def refusal(send, base, headers):
    with pytest.raises(ConfigurationError) as caught:
        send(base, headers)
    assert caught.value.code == "insecure_http_origin", caught.value
    return str(caught.value)


@pytest.mark.parametrize("sender", list(SENDERS))
def test_a_benign_value_over_the_limit_is_refused_with_a_message_naming_the_limit(sink, key, marker, sender):
    message = refusal(SENDERS[sender], f"http://plain.example.test:{sink.port}", {"X-Trace": benign(CAP + 1, marker)})
    assert all(word in message for word in SIZE_WORDS), message
    assert "https://" in message and "FI_ALLOW_INSECURE_HTTP=1" in message
    assert key not in message and marker not in message
    assert sink.connections == 0 and sink.marker_bytes(marker) == 0


@pytest.mark.parametrize("sender", list(SENDERS))
def test_a_refusal_for_a_found_key_or_a_key_header_does_not_name_the_limit(sink, key, marker, sender):
    base = f"http://plain.example.test:{sink.port}"
    for headers in ({"X-Trace": benign(CAP, "pre-" + key)},
                    {"X-Api-Key": key, "X-Trace": benign(CAP + 1, marker)},
                    {"X-Trace": benign(CAP + 1, marker), "X-Other": f"pre-{key}-post"}):
        message = refusal(SENDERS[sender], base, headers)
        assert not any(word in message for word in SIZE_WORDS), message
        assert key not in message and marker not in message
    assert sink.connections == 0 and sink.marker_bytes(marker) == 0


def test_an_exporter_with_no_endpoint_and_a_value_over_the_limit_is_refused_naming_the_limit(key, marker):
    from fi._core.http_security import require_endpoint_with_keys

    with pytest.raises(ConfigurationError) as caught:
        require_endpoint_with_keys("", {"X-Trace": benign(CAP + 1, marker)})
    message = str(caught.value)
    assert caught.value.code == "insecure_http_origin"
    assert all(word in message for word in SIZE_WORDS), message
    assert key not in message and marker not in message
    with pytest.raises(ConfigurationError) as caught:
        require_endpoint_with_keys("", {"X-Trace": benign(CAP, key)})
    assert not any(word in str(caught.value) for word in SIZE_WORDS)
