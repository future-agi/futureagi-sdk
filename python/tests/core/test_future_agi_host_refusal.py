"""A request that carries credentials is not sent over plain http to a Future AGI host by any sender, whatever
``FI_ALLOW_INSECURE_HTTP`` says. The error is ``InsecureHttpRefusedError`` (code ``INSECURE_HTTP_REFUSED``, also a
``ConfigurationError``); the host is the one the library connects to: the case of the name, a trailing dot and non-ASCII dots
do not change it, and the user info is not the host. Other hosts keep their own rules. The marker keys are counted at a
loopback listener; every name resolves to this machine through a shim, so no real host is reached."""

from __future__ import annotations

import os
from unittest import mock

import pytest
from requests_futures.sessions import FuturesSession

import fi
from fi.errors import ConfigurationError
from tests.core._plaintext_oracle import MARKER_KEY, MARKER_SECRET, PROXY_NAMES
from tests.core._plaintext_oracle import sinks  # noqa: F401  (the fixture)
from tests.core.test_sender_rules import KEYS, _get, resolver  # noqa: F401  (the fixture)

FI_HOSTS = ["api.futureagi.com", "gateway.futureagi.com", "API.FutureAGI.com", "api.futureagi.com.", "futureagi.com", "eu.api.futureagi.com",
            "api。futureagi。com", "api．futureagi．com", "api｡futureagi｡com", "user@api.futureagi.com"]


def _env(flag):
    clean = {k: v for k, v in os.environ.items() if k not in PROXY_NAMES and k != "FI_ALLOW_INSECURE_HTTP"}
    return {**clean, **({} if flag is None else {"FI_ALLOW_INSECURE_HTTP": flag})}


def _http_client_sdk(base):
    from fi.api.auth import HttpClient

    return _get(HttpClient(base_url="http://127.0.0.1:1", default_headers=dict(KEYS)), f"{base}/x?q=secretquery")


def _http_client_caller(base):
    from fi.api.auth import HttpClient

    return _get(HttpClient(base_url="http://127.0.0.1:1", session=FuturesSession(), default_headers=dict(KEYS)), f"{base}/x?q=secretquery")


def _kb_create(base):
    from fi.kb.client import KnowledgeBase

    return KnowledgeBase(fi_api_key=MARKER_KEY, fi_secret_key=MARKER_SECRET, fi_base_url=base).create_kb(name="docs")


def _platform_sync(base):
    import fi.platform as fp

    with fp.Client(api_key=MARKER_KEY, secret_key=MARKER_SECRET, base_url=base, max_retries=0, timeout=5) as client:
        return client.request("GET", "/probe/")


def _gateway_destination(base):
    from fi.gateway._http_security import validate_destination

    return validate_destination(base, f"{base}/v1/chat")


SENDERS = [_http_client_sdk, _http_client_caller, _kb_create, _platform_sync, _gateway_destination]


@pytest.mark.parametrize("flag", [None, "1", "true"])
@pytest.mark.parametrize("host", FI_HOSTS)
@pytest.mark.parametrize("sender", SENDERS, ids=lambda f: f.__name__.lstrip("_"))
def test_plain_http_to_a_future_agi_host_is_refused_before_sending(sinks, resolver, sender, host, flag):
    if sender is _gateway_destination and "@" in host:
        pytest.skip("a gateway URL with user info is refused as an invalid URL before its host is judged")
    for each in sinks.values():
        each.reset()
    with mock.patch.dict(os.environ, _env(flag), clear=True):
        with pytest.raises(fi.InsecureHttpRefusedError) as info:
            sender(f"http://{host}:{sinks['target'].port}")
    error = info.value
    assert isinstance(error, ConfigurationError) and error.get_error_code() == "INSECURE_HTTP_REFUSED" and error.code == "INSECURE_HTTP_REFUSED"
    for text in (str(error), repr(error)):
        assert MARKER_KEY not in text and MARKER_SECRET not in text and "secretquery" not in text
    assert error.host.endswith("futureagi.com") and error.host == error.host.lower() and not error.host.endswith(".")
    assert all(each.marker_bytes == 0 for each in sinks.values())


@pytest.mark.parametrize("host", ["notfutureagi.com", "futureagi.com.example", "api.futureagi.com@other.example"])
def test_a_host_that_is_not_a_future_agi_host_is_not_refused_as_one(host):
    from fi._core.http_security import require_secure_credentials_url

    with mock.patch.dict(os.environ, _env(None), clear=True):
        with pytest.raises(ConfigurationError) as info:
            require_secure_credentials_url(f"http://{host}:81/x")
    assert not isinstance(info.value, fi.InsecureHttpRefusedError)


def test_the_error_is_the_one_0_7_1_publishes():
    import fi.utils.errors as ue

    assert fi.InsecureHttpRefusedError is ue.InsecureHttpRefusedError is fi.errors.InsecureHttpRefusedError
    assert issubclass(fi.InsecureHttpRefusedError, fi.errors.SDKException)
    error = fi.InsecureHttpRefusedError("api.futureagi.com")
    assert error.host == "api.futureagi.com" and error.get_error_code() == "INSECURE_HTTP_REFUSED"
    assert "api.futureagi.com" in str(error) and "https" in str(error)
