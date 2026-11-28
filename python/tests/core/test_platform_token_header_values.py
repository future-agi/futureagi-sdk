"""A header value that holds ``FI_PLATFORM_TOKEN`` from the environment is judged as one that holds ``FI_API_KEY`` or
``FI_SECRET_KEY``: in any letter case, as written or in what it decodes to (a Basic credential, hex, every byte
percent-encoded, base64 at any offset, base64 of base64), when the token has eight characters or more. While such a
token is set, a header value longer than 64 KiB counts as holding it without being read.

Senders: ``HttpClient.request`` and the OTLP HTTP exporter (built, then one span exported). Host names ending in
``.test`` resolve to a loopback listener (``getaddrinfo`` is replaced for the test); the target and a ``CONNECT``-aware
proxy sink count connections and the token hits in what they received, decoded the same ways. Tokens and markers are
made at run time, one per test."""

import os
import secrets
import socket
import types

import pytest

from fi._core.proxy_routing import carries_credentials
from fi.api.auth import HttpClient
from fi.api.types import HttpMethod, RequestConfig
from fi.errors import ConfigurationError
from tests.core.test_header_key_scan_size_cap import PROXY_NAMES, Sink
from tests.core.test_header_key_scan_size_message import benign
from tests.core.test_header_value_key_forms import _decoded, forms

CAP = 64 * 1024
SIZE_WORDS = ("65,536", "64 KiB", "FI_PLATFORM_TOKEN")
FORMS = list(forms("placeholder-token"))


def made_token():
    return "pt" + "-A-" + secrets.token_hex(12)


@pytest.fixture
def token(monkeypatch):
    for name in ("FI_API_KEY", "FI_SECRET_KEY", "FI_PLATFORM_TOKEN", "FI_EXTRA_HEADERS",
                 "FI_ALLOW_INSECURE_HTTP") + PROXY_NAMES:
        monkeypatch.delenv(name, raising=False)
    for name in [name for name in os.environ if name.startswith("OTEL_EXPORTER_OTLP")]:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("FI_LOGIN_FILE", "/nonexistent/login.json")
    made = made_token()
    monkeypatch.setenv("FI_PLATFORM_TOKEN", made)
    return made


@pytest.fixture
def sinks(token, monkeypatch):
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


def hits(sink, text):
    """Occurrences of ``text`` in any letter case in what ``sink`` received, as received and decoded."""
    needle = text.lower().encode()
    return sum(each.lower().count(needle) for each in _decoded(bytes(sink.received)))


def via_http_client(base, headers):
    client = HttpClient(base_url=base)
    try:
        client.request(RequestConfig(method=HttpMethod.GET, url=f"{base}/probe", headers=headers, retry_attempts=1,
                                     timeout=30))
    finally:
        client.close()


def via_otlp_http_exporter(base, headers):
    from opentelemetry.sdk.trace import TracerProvider

    from fi.evals.otel._tracer_factories import _create_exporter
    from fi.evals.otel.config import ExporterConfig
    from fi.evals.otel.types import ExporterType

    exporter = _create_exporter(ExporterConfig(type=ExporterType.OTLP_HTTP, endpoint=f"{base}/v1/traces",
                                               headers=headers, timeout_ms=3000))
    span = TracerProvider().get_tracer("t").start_span("s")
    span.end()
    exporter.export([span])


SENDERS = {"HttpClient.request": via_http_client, "OTLP_HTTP exporter": via_otlp_http_exporter}


def outcome(send, base, headers):
    try:
        send(base, headers)
    except ConfigurationError as error:
        return error
    return None


def through_proxy(sinks, monkeypatch):
    for name in ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy"):
        monkeypatch.setenv(name, f"http://127.0.0.1:{sinks.proxy.port}")


# How the request would leave without the opt-in: straight to the plain-http host, or through the environment proxy.
ROUTES = {"direct": lambda sinks, monkeypatch: None, "environment proxy": through_proxy}


@pytest.mark.parametrize("case", FORMS)
def test_a_header_value_holding_the_platform_token_in_any_encoding_is_a_key(token, case):
    value = forms(token)[case]
    assert carries_credentials({"X-Trace": value}) is True
    assert carries_credentials([(b"Proxy-Authorization", value.encode("latin-1"))]) is True
    assert carries_credentials({"X-Trace": "other header text"}) is False


def test_the_platform_token_is_looked_for_from_eight_characters(token, monkeypatch):
    monkeypatch.setenv("FI_PLATFORM_TOKEN", "pt" + secrets.token_hex(3))
    assert carries_credentials({"X-Team": "team-" + os.environ["FI_PLATFORM_TOKEN"] + "-blue"}) is True
    monkeypatch.setenv("FI_PLATFORM_TOKEN", "p" + secrets.token_hex(3))
    assert carries_credentials({"X-Team": "team-" + os.environ["FI_PLATFORM_TOKEN"] + "-blue"}) is False


@pytest.mark.parametrize("case", FORMS)
@pytest.mark.parametrize("route", list(ROUTES))
@pytest.mark.parametrize("sender", list(SENDERS))
def test_the_platform_token_in_a_header_value_reaches_no_sink_over_plain_http(sinks, token, monkeypatch, sender, route,
                                                                            case):
    ROUTES[route](sinks, monkeypatch)
    error = outcome(SENDERS[sender], f"http://plain.example.test:{sinks.target.port}", {"X-Trace": forms(token)[case]})
    seen = {"target": (sinks.target.connections, hits(sinks.target, token) * len(token)),
            "proxy": (sinks.proxy.connections, hits(sinks.proxy, token) * len(token))}
    assert seen == {"target": (0, 0), "proxy": (0, 0)}, f"connections and token bytes per sink: {seen}"
    assert isinstance(error, ConfigurationError) and error.code == "insecure_http_origin", error
    assert token not in str(error)


# With the opt-in and an environment proxy, a keyed request goes straight to the plain-http host: the SDK's own session
# and the exporter's session send it without that proxy, as for FI_API_KEY and FI_SECRET_KEY.
@pytest.mark.parametrize("case", FORMS)
@pytest.mark.parametrize("sender", list(SENDERS))
def test_with_the_opt_in_the_platform_token_in_a_header_value_reaches_no_environment_proxy(sinks, token, monkeypatch,
                                                                                         sender, case):
    through_proxy(sinks, monkeypatch)
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    error = outcome(SENDERS[sender], f"http://plain.example.test:{sinks.target.port}", {"X-Trace": forms(token)[case]})
    seen = {"target": sinks.target.connections, "proxy": (sinks.proxy.connections, hits(sinks.proxy, token) * len(token))}
    assert seen == {"target": 1, "proxy": (0, 0)}, f"connections and token bytes: {seen}"
    assert error is None, error
    assert hits(sinks.target, token) >= 1


@pytest.mark.parametrize("sender", list(SENDERS))
def test_a_value_over_the_cap_is_refused_while_the_platform_token_is_set(sinks, token, monkeypatch, sender):
    marker = "capmarker" + secrets.token_hex(10)
    base = f"http://plain.example.test:{sinks.target.port}"
    error = outcome(SENDERS[sender], base, {"X-Trace": benign(CAP + 1, marker)})
    delivered = sinks.target.marker_bytes(marker) + sinks.proxy.marker_bytes(marker)
    assert (delivered, sinks.target.connections) == (0, 0), f"{delivered} marker bytes received"
    assert isinstance(error, ConfigurationError) and error.code == "insecure_http_origin", error
    assert all(word in str(error) for word in SIZE_WORDS), str(error)
    assert marker not in str(error) and token not in str(error)
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    assert outcome(SENDERS[sender], base, {"X-Trace": benign(CAP + 1, marker)}) is None
    assert sinks.target.marker_bytes(marker) == len(marker)
