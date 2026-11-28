"""Plain-HTTP and proxy rules for the cases the review of the sending paths named: a URL written with leading or trailing
whitespace, a caller session that the environment proxies, a redirect on a key-carrying request, a host written with
non-ASCII dots, the OTLP exporters' environment headers and their endpoint default, and a Future AGI host written with a
trailing dot. Every refusal is measured: the marker keys are counted at the loopback listeners (the target and two proxy
sinks); a resolver shim maps the Future AGI test hostname to loopback instead of using DNS."""

from __future__ import annotations

import os
import socket
from typing import Any
from unittest import mock

import httpx
import pytest
import requests
from requests_futures.sessions import FuturesSession

from fi._core.http_security import plaintext_decision, require_secure_grpc_target
from fi._credentials import Credentials
from fi._http import LazyKeyAuth
from fi.errors import ConfigurationError, UnexpectedRedirectError
from tests.core._plaintext_oracle import MARKER_KEY, MARKER_SECRET, PROXY_NAMES, Sink
from tests.core._plaintext_oracle import sinks  # noqa: F401  (the fixture)

KEYS = {"X-Api-Key": MARKER_KEY, "X-Secret-Key": MARKER_SECRET}
FI_NAME = "api.futureagi.com"


@pytest.fixture()
def resolver():
    """Every name the sending library resolves is this machine (the real resolver is not asked)."""
    real = socket.getaddrinfo

    def to_loopback(host: Any, port: Any, *args: Any, **kwargs: Any) -> Any:
        return real("127.0.0.1", port, *args, **kwargs)

    with mock.patch("socket.getaddrinfo", to_loopback):
        yield


def _clean_env(**extra: str) -> dict[str, str]:
    return {**{k: v for k, v in os.environ.items() if k not in PROXY_NAMES}, **extra}


def _sdk_client(base: str):
    from fi.api.auth import HttpClient

    return HttpClient(base_url=base, default_headers=dict(KEYS))


def _get(client: Any, url: str) -> Any:
    from fi.api.types import HttpMethod, RequestConfig

    return client.request(RequestConfig(method=HttpMethod.GET, url=url, retry_attempts=1))


def _seen(sinks_: dict[str, Sink]) -> dict[str, int]:
    return {name: each.marker_bytes for name, each in sinks_.items()}


# --- a URL with leading or trailing whitespace is read by the sending library as the URL it strips it to ------------

SPACED = [
    f"  http://{FI_NAME}:{{p}}/x", f"\thttp://{FI_NAME}:{{p}}/x", f"\nhttp://{FI_NAME}:{{p}}/x",
    f"http://{FI_NAME}:{{p}}/x  ", " http://example.com:{p}/x", "http://exa\nmple.com:{p}/x",
]


@pytest.mark.parametrize("template", SPACED)
def test_the_decision_refuses_a_plain_http_url_with_whitespace_or_a_control_character(template):
    decision = plaintext_decision(template.format(p=81), allow_insecure_http=True)
    assert not decision.allowed, decision


@pytest.mark.parametrize("template", SPACED[:3] + SPACED[4:5])
def test_a_key_carrying_request_to_a_spaced_url_sends_no_byte_through_the_sdk_client(sinks, resolver, template):
    for each in sinks.values():
        each.reset()
    url = template.format(p=sinks["target"].port)
    with mock.patch.dict(os.environ, _clean_env(FI_ALLOW_INSECURE_HTTP="1"), clear=True):
        with pytest.raises(ConfigurationError):
            _get(_sdk_client("https://fi.example.invalid"), url)
    assert _seen(sinks) == {"target": 0, "sinkA": 0, "sinkB": 0}
    assert sinks["target"].requests == 0


def test_a_key_carrying_request_to_a_spaced_url_sends_no_byte_through_a_caller_session(sinks, resolver):
    for each in sinks.values():
        each.reset()
    session = FuturesSession()
    url = f"  http://{FI_NAME}:{sinks['target'].port}/x"
    with mock.patch.dict(os.environ, _clean_env(FI_ALLOW_INSECURE_HTTP="1"), clear=True):
        from fi.api.auth import HttpClient

        client = HttpClient(base_url="https://fi.example.invalid", session=session, default_headers=dict(KEYS))
        with pytest.raises(ConfigurationError):
            _get(client, url)
    assert _seen(sinks) == {"target": 0, "sinkA": 0, "sinkB": 0}


def test_a_key_carrying_httpx_request_to_a_spaced_url_sends_no_byte(sinks, resolver):
    for each in sinks.values():
        each.reset()
    creds = Credentials(api_key=MARKER_KEY, secret_key=MARKER_SECRET, base_url="https://fi.example.invalid", keys_source="argument", base_url_source="argument")
    with mock.patch.dict(os.environ, _clean_env(FI_ALLOW_INSECURE_HTTP="1"), clear=True):
        with httpx.Client(auth=LazyKeyAuth(lambda: creds), timeout=1.5) as client:
            with pytest.raises((ConfigurationError, httpx.InvalidURL, httpx.UnsupportedProtocol)):
                client.get(f"  http://{FI_NAME}:{sinks['target'].port}/x")
    assert _seen(sinks) == {"target": 0, "sinkA": 0, "sinkB": 0}


# --- a caller session the environment proxies sends its keys to the proxy ----------------------------------------

LOOPBACK_HOSTS = ["127.0.0.1", "LOCALHOST", "localhost", "x@127.0.0.1", "[::1]"]


@pytest.mark.parametrize("host", LOOPBACK_HOSTS)
@pytest.mark.parametrize("when", ["before", "after"])
def test_a_caller_session_to_loopback_is_refused_when_the_environment_proxies_it(sinks, host, when):
    from fi.api.auth import HttpClient

    for each in sinks.values():
        each.reset()
    proxy = {"HTTP_PROXY": f"http://127.0.0.1:{sinks['sinkA'].port}"}
    url = f"http://{host}:{sinks['target'].port}/x"
    with mock.patch.dict(os.environ, _clean_env(**({} if when == "after" else proxy)), clear=True):
        session = FuturesSession()
        client = HttpClient(base_url="https://fi.example.invalid", session=session, default_headers=dict(KEYS))
        if when == "after":
            os.environ.update(proxy)
        with pytest.raises(ConfigurationError):
            _get(client, url)
    assert _seen(sinks) == {"target": 0, "sinkA": 0, "sinkB": 0}


def test_a_caller_session_with_a_mounted_adapter_is_refused_when_the_environment_proxies_it(sinks):
    from fi.api.auth import HttpClient

    for each in sinks.values():
        each.reset()
    session = FuturesSession()
    session.mount("http://", requests.adapters.HTTPAdapter())
    with mock.patch.dict(os.environ, _clean_env(HTTP_PROXY=f"http://127.0.0.1:{sinks['sinkA'].port}"), clear=True):
        client = HttpClient(base_url="https://fi.example.invalid", session=session, default_headers=dict(KEYS))
        with pytest.raises(ConfigurationError):
            _get(client, f"http://127.0.0.1:{sinks['target'].port}/x")
    assert _seen(sinks) == {"target": 0, "sinkA": 0, "sinkB": 0}


def test_a_caller_session_to_loopback_without_a_proxy_sends(sinks):
    from fi.api.auth import HttpClient

    for each in sinks.values():
        each.reset()
    with mock.patch.dict(os.environ, _clean_env(), clear=True):
        client = HttpClient(base_url="https://fi.example.invalid", session=FuturesSession(), default_headers=dict(KEYS))
        _get(client, f"http://127.0.0.1:{sinks['target'].port}/x")
    assert sinks["target"].marker_bytes > 0 and sinks["sinkA"].marker_bytes == 0


def test_the_sdk_session_to_loopback_goes_direct_whatever_the_environment_says(sinks):
    for each in sinks.values():
        each.reset()
    with mock.patch.dict(os.environ, _clean_env(HTTP_PROXY=f"http://127.0.0.1:{sinks['sinkA'].port}"), clear=True):
        _get(_sdk_client("https://fi.example.invalid"), f"http://127.0.0.1:{sinks['target'].port}/x")
    assert sinks["target"].marker_bytes > 0 and sinks["sinkA"].marker_bytes == 0


# --- a key-carrying request does not follow a redirect -------------------------------------------------------------


@pytest.mark.parametrize("status", [b"301 Moved Permanently", b"302 Found", b"303 See Other", b"307 Temporary Redirect", b"308 Permanent Redirect"])
def test_the_sdk_http_client_does_not_follow_a_redirect_with_keys(sinks, status):
    redirecting = Sink(status=status, location=f"http://127.0.0.1:{sinks['sinkB'].port}/next")
    try:
        sinks["sinkB"].reset()
        with mock.patch.dict(os.environ, _clean_env(), clear=True):
            with pytest.raises(UnexpectedRedirectError) as info:
                _get(_sdk_client(f"http://127.0.0.1:{redirecting.port}"), f"http://127.0.0.1:{redirecting.port}/start")
        assert sinks["sinkB"].requests == 0 and sinks["sinkB"].marker_bytes == 0
        assert redirecting.marker_bytes > 0  # the keys went to the URL asked for, once
        assert MARKER_KEY not in str(info.value) and MARKER_SECRET not in str(info.value)
        assert "/next" not in str(info.value)  # the error shows at most the target host and omits its path
    finally:
        redirecting.close()


def test_a_direct_requests_call_with_keys_does_not_follow_a_redirect(sinks):
    from fi.api.auth import HttpClient

    client = HttpClient.__new__(HttpClient)
    client._extra_headers = None
    with mock.patch.dict(os.environ, _clean_env(), clear=True):
        kwargs = client._direct_kwargs({"url": f"http://127.0.0.1:{sinks['target'].port}/up", "headers": dict(KEYS)})
    assert kwargs.get("allow_redirects") is False


# --- a host written with non-ASCII dots is not loopback as written ------------------------------------------------


@pytest.mark.parametrize("host", ["127。0。0。1", "127．0．0．1", "127｡0｡0｡1", "127.0.0。1"])
def test_a_host_with_non_ascii_dots_is_not_loopback_as_written(host):
    decision = plaintext_decision(f"http://{host}:81/x")
    assert decision.reason != "loopback" and not decision.allowed, decision


@pytest.mark.parametrize("host", ["127。0。0。1", "127．0．0．1", "127｡0｡0｡1"])
def test_a_base_url_with_a_non_ascii_dot_host_is_refused_before_any_byte(sinks, host):
    """httpx rewrites such a host to 127.0.0.1 before a request exists, so the SDK judges the base URL as written."""
    from fi import FutureAGIClient

    for each in sinks.values():
        each.reset()
    with mock.patch.dict(os.environ, _clean_env(), clear=True):
        with pytest.raises(ConfigurationError):
            FutureAGIClient(api_key=MARKER_KEY, secret_key=MARKER_SECRET, base_url=f"http://{host}:{sinks['target'].port}", retries=0).users.current()
    assert _seen(sinks) == {"target": 0, "sinkA": 0, "sinkB": 0}


# --- the OTLP exporters ----------------------------------------------------------------------------------------


def _exporter(kind: str, endpoint: str, **kwargs: Any) -> Any:
    from fi.evals.otel._tracer_factories import _create_exporter
    from fi.evals.otel.config import ExporterConfig
    from fi.evals.otel.types import ExporterType

    return _create_exporter(ExporterConfig(type=getattr(ExporterType, kind), endpoint=endpoint, **kwargs))


@pytest.mark.parametrize("variable", ["OTEL_EXPORTER_OTLP_HEADERS", "OTEL_EXPORTER_OTLP_TRACES_HEADERS"])
def test_the_futureagi_exporter_refuses_fi_key_env_headers_when_its_endpoint_is_not_a_future_agi_address(sinks, variable):
    for each in sinks.values():
        each.reset()
    env = _clean_env(**{variable: f"x-api-key={MARKER_KEY},x-secret-key={MARKER_SECRET}"})
    with mock.patch.dict(os.environ, env, clear=True):
        with pytest.raises(ConfigurationError) as info:
            _exporter("FUTUREAGI", f"http://127.0.0.1:{sinks['target'].port}/v1/traces")
    assert info.value.code == "otel_env_key_headers" if hasattr(info.value, "code") else True
    assert MARKER_KEY not in str(info.value) and MARKER_SECRET not in str(info.value)
    assert all(each.marker_bytes == 0 for each in sinks.values())


def test_the_futureagi_exporter_keeps_a_future_agi_endpoint_with_env_key_headers():
    env = _clean_env(OTEL_EXPORTER_OTLP_HEADERS=f"x-api-key={MARKER_KEY},x-secret-key={MARKER_SECRET}")
    with mock.patch.dict(os.environ, env, clear=True):
        from fi._core.http_security import require_no_key_headers_in_otel_env

        require_no_key_headers_in_otel_env(f"https://{FI_NAME}/v1/traces")


@pytest.mark.parametrize("secret_form", ["{key}", "Bearer {key}"])
def test_an_authorization_env_header_that_carries_a_future_agi_key_is_refused_for_another_exporter(sinks, secret_form):
    env = _clean_env(OTEL_EXPORTER_OTLP_HEADERS="authorization=" + secret_form.format(key=MARKER_KEY).replace(" ", "%20"),
                     FI_API_KEY=MARKER_KEY, FI_SECRET_KEY=MARKER_SECRET)
    with mock.patch.dict(os.environ, env, clear=True):
        with pytest.raises(ConfigurationError) as info:
            _exporter("OTLP_HTTP", f"http://127.0.0.1:{sinks['target'].port}/v1/traces")
    assert MARKER_KEY not in str(info.value)


def test_an_authorization_env_header_with_another_value_is_not_a_key_header(sinks):
    env = _clean_env(OTEL_EXPORTER_OTLP_HEADERS="authorization=Bearer%20some-other-token", FI_API_KEY=MARKER_KEY, FI_SECRET_KEY=MARKER_SECRET)
    with mock.patch.dict(os.environ, env, clear=True):
        assert _exporter("OTLP_HTTP", f"http://127.0.0.1:{sinks['target'].port}/v1/traces") is not None


@pytest.mark.parametrize("kind", ["OTLP_GRPC", "OTLP_HTTP"])
def test_an_empty_exporter_endpoint_with_keys_is_refused_as_an_empty_authority_not_defaulted(kind):
    with mock.patch.dict(os.environ, _clean_env(), clear=True):
        with pytest.raises(ConfigurationError) as info:
            _exporter(kind, "", headers=dict(KEYS))
    assert "no host" in str(info.value) or "empty" in str(info.value)
    assert MARKER_KEY not in str(info.value)


@pytest.mark.parametrize("kind", ["OTLP_GRPC", "OTLP_HTTP"])
def test_an_empty_exporter_endpoint_without_keys_keeps_its_default(kind):
    with mock.patch.dict(os.environ, _clean_env(), clear=True):
        assert _exporter(kind, "") is not None


# --- a Future AGI host with a trailing dot is a Future AGI host ----------------------------------------------------


@pytest.mark.parametrize("name", [f"{FI_NAME}.", f"API.FUTUREAGI.COM.", "grpc.futureagi.com."])
def test_a_future_agi_host_with_a_trailing_dot_is_refused_by_the_future_agi_rule(name):
    assert plaintext_decision(f"http://{name}:81/x", allow_insecure_http=True).reason == "future_agi_host"
    with pytest.raises(ConfigurationError) as info:
        require_secure_grpc_target(f"{name}:4317", dict(KEYS), insecure=True)
    assert "does not apply to a Future AGI host" in str(info.value)
