"""A gateway base URL the SDK will not send keys to is refused with the code of its situation, before a connection:
``insecure_http_origin`` for user info, a backslash, an empty host, brackets in the user info, an ``@`` after the host of a
plain-http URL and a host written with non-ASCII dots; ``INSECURE_HTTP_REFUSED`` for a Future AGI host. The error's ``code``
and ``get_error_code()`` agree, it is also a ``ConfigurationError``, and its text holds neither the user info nor a key.
Every row is measured at a loopback listener: no connection and no marker byte. The helper functions answer in their own way
(``check_valid_key`` is ``False``, ``health_check`` is the error status) and send nothing either."""

from __future__ import annotations

import asyncio
import os
from typing import Any
from unittest import mock

import pytest

from fi.errors import ConfigurationError
from fi.gateway import AgentCC, AgentCCError, AsyncAgentCC
from tests.core._plaintext_oracle import MARKER_KEY, PROXY_NAMES, Sink

USER = "GWUSER-5e1c"
PASSWORD = "GWPASS-93ab"


@pytest.fixture(scope="module")
def target():
    sink = Sink()
    yield sink
    sink.close()


def _forms(port: int) -> dict[str, str]:
    return {
        "user info over http": f"http://{USER}:{PASSWORD}@127.0.0.1:{port}",
        "user info over https": f"https://{USER}:{PASSWORD}@127.0.0.1:{port}",
        "a name before the at sign": f"http://{USER}@127.0.0.1:{port}",
        "an at sign after the host": f"http://127.0.0.1:{port}/@elsewhere.test",
        "an at sign in the query": f"http://127.0.0.1:{port}/v1?x=@elsewhere.test",
        "a backslash": f"http://127.0.0.1:{port}\\@elsewhere.test",
        "a percent-encoded backslash": f"http://127.0.0.1:{port}%5C@elsewhere.test",
        "an empty host": "http:///x",
        "an empty host with a port": f"http://:{port}/x",
        "brackets in the user info": f"http://[{USER}]@127.0.0.1:{port}",
        "an ideographic full stop": f"http://127。0。0。1:{port}",
        "a fullwidth full stop": f"http://127．0．0．1:{port}",
        "a halfwidth ideographic full stop": f"http://127｡0｡0｡1:{port}",
    }


NAMES = list(_forms(1))


def _clean() -> Any:
    return mock.patch.dict(os.environ, {k: v for k, v in os.environ.items() if k not in PROXY_NAMES}, clear=True)


def _sync_call(base: str) -> None:
    client = AgentCC(api_key=MARKER_KEY, base_url=base, max_retries=0)
    try:
        client.models.list()
    finally:
        client.close()


def _async_call(base: str) -> None:
    async def go() -> None:
        client = AsyncAgentCC(api_key=MARKER_KEY, base_url=base, max_retries=0)
        try:
            await client.models.list()
        finally:
            await client.aclose()

    asyncio.run(go())


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("name", NAMES)
def test_a_gateway_client_refuses_the_url_with_the_code_of_its_situation(target, name, asynchronous):
    target.reset()
    base = _forms(target.port)[name]
    with _clean(), pytest.raises(AgentCCError) as refused:
        (_async_call if asynchronous else _sync_call)(base)
    error = refused.value
    assert error.code == "insecure_http_origin", repr(error)
    assert error.get_error_code() == "insecure_http_origin"
    assert isinstance(error, ConfigurationError)
    text = f"{error} {error!r} {error.args}"
    assert USER not in text and PASSWORD not in text and MARKER_KEY not in text
    assert target.marker_bytes == 0 and target.requests == 0, [bytes(c)[:80] for c in target.chunks]


@pytest.mark.parametrize("name", NAMES)
def test_the_gateway_helpers_send_nothing_for_the_url(target, name):
    from fi.gateway._utils import check_valid_key, health_check

    target.reset()
    base = _forms(target.port)[name]
    with _clean():
        assert check_valid_key(MARKER_KEY, base) is False
        assert health_check(api_key=MARKER_KEY, base_url=base)["status"] != "ok"
    assert target.marker_bytes == 0 and target.requests == 0


@pytest.mark.parametrize("host", ["api.futureagi.com", "a.b.futureagi.com", "api。futureagi。com"])
@pytest.mark.parametrize("userinfo", ["", f"{USER}:{PASSWORD}@"])
def test_a_future_agi_host_keeps_its_own_code(target, host, userinfo):
    target.reset()
    with _clean(), pytest.raises(AgentCCError) as refused:
        _sync_call(f"http://{userinfo}{host}:{target.port}")
    assert refused.value.code == "INSECURE_HTTP_REFUSED" and refused.value.get_error_code() == "INSECURE_HTTP_REFUSED"
    assert USER not in str(refused.value) and PASSWORD not in str(refused.value)
    assert target.requests == 0


def test_a_loopback_gateway_url_without_the_situations_above_is_sent(target):
    target.reset()
    with _clean():
        try:
            _sync_call(f"http://127.0.0.1:{target.port}")
        except Exception as error:  # noqa: BLE001 - the empty answer of the listener is not a valid model list
            assert getattr(error, "code", None) != "insecure_http_origin", repr(error)
    assert target.requests == 1


# The error's code and get_error_code() agree for the refusals that carry one.
@pytest.mark.parametrize("code", [
    "insecure_http_origin", "insecure_loopback_grpc", "otel_env_key_headers", "unsupported_otlp_exporter",
    "custom_base_url_not_allowed", "missing_base_url", "invalid_base_url", "unreadable_tls_file",
])
def test_get_error_code_agrees_with_code_for_a_configuration_refusal(code):
    error = ConfigurationError("refused", code=code)
    assert error.get_error_code() == error.code == code


def test_get_error_code_of_a_plain_configuration_error_is_unchanged():
    assert ConfigurationError("bad option").get_error_code() == "CONFIGURATION_ERROR"
    assert ConfigurationError("bad option", code="invalid_revision").get_error_code() == "CONFIGURATION_ERROR"


@pytest.mark.parametrize("url", ["http://plain.example.test", f"http://{USER}@plain.example.test", "http://127。0。0。1:9", "http://:9/x"])
def test_the_shared_refusal_reports_the_same_code_through_both_accessors(url):
    from fi._core.http_security import require_secure_credentials_url

    with pytest.raises(ConfigurationError) as refused:
        require_secure_credentials_url(url, environ={})
    assert refused.value.get_error_code() == refused.value.code == "insecure_http_origin"


@pytest.mark.parametrize("url", [f"https://{USER}:{PASSWORD}@api.futureagi.com", f"https://{USER}@api.futureagi.com:8443/v1"])
def test_user_info_over_https_to_a_future_agi_host_is_refused_with_the_code_of_the_self_hosted_rule(url):
    from fi.gateway._http_security import validate_destination

    with _clean(), pytest.raises(AgentCCError) as refused:
        validate_destination(url, url)
    assert refused.value.code == "insecure_http_origin" and refused.value.get_error_code() == "insecure_http_origin"
    assert USER not in str(refused.value) and PASSWORD not in str(refused.value)


@pytest.mark.parametrize("code", [
    "insecure_http_origin", "insecure_sandbox_origin", "custom_base_url_not_allowed", "missing_base_url", "invalid_base_url",
])
def test_the_sandbox_configuration_error_answers_the_refusal_code_through_both_accessors(code):
    from fi.sandbox.errors import ConfigurationError as SandboxConfigurationError

    error = SandboxConfigurationError("refused", code=code)
    assert error.get_error_code() == error.code == code
    assert SandboxConfigurationError("bad option").get_error_code() == "CONFIGURATION_ERROR"
