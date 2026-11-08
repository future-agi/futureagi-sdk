"""Credential-named default query parameters are refused when a client is built.

``default_query`` is applied to every request URL, so a credential-named key would put
a secret in URLs, proxies and logs. One normalized name set (lowercase, ``-`` equals
``_``) is shared by the header scrub, the callback sinks, the send-time URL check and
this construction check; the error names the key, never the value.
"""
import inspect

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC
from fi.gateway import _constants
from fi.gateway._exceptions import AgentCCError
from fi.gateway._http_security import validate_destination
from fi.gateway._transport import _scrub
from fi.gateway._transport._sync import SyncBaseClient
from fi.gateway._transport._async import AsyncBaseClient
from fi.gateway._utils import redact_headers
from fi.gateway.callbacks import base as callback_base

pytestmark = [pytest.mark.anyio, pytest.mark.filterwarnings("ignore::DeprecationWarning")]
ORIGIN = "https://gateway.example.test"
MARKER = "synthetic-query-value-must-never-appear"
LISTED = (
    "authorization", "api_key", "key", "token", "access_token", "x_api_key", "x_goog_api_key",
    "x_auth_token", "x_access_token", "x_api_token", "password", "secret", "client_secret", "cookie",
)
ALLOWED = ("tenant", "region", "page", "limit", "keyword", "tokens", "monkey", "api", "secretary", "passwords")


@pytest.fixture
def anyio_backend():
    return "asyncio"


def spellings(name):
    base = name.replace("_", "-")
    return {name, name.upper(), name.title(), base, base.upper(), base.title(), name.swapcase()}


# The one shared set, spelled out: header names, sink keys and query names, normalized.
EXPECTED = (
    "authorization", "proxy_authorization", "cookie", "set_cookie", "x_api_key", "api_key",
    "x_goog_api_key", "x_agentcc_config", "x_auth_token", "x_access_token", "x_api_token",
    "x_agentcc_api_key", "x_secret_key", "virtual_key", "secret_key", "fi_api_key",
    "fi_secret_key", "access_token", "refresh_token", "client_secret", "password",
    "key", "token", "secret",
)


def test_the_listed_names_are_in_the_one_shared_set():
    assert set(_constants.CREDENTIAL_NAMES) == set(EXPECTED)
    assert set(LISTED) <= set(_constants.CREDENTIAL_NAMES)
    assert all(name == name.lower() and "-" not in name for name in _constants.CREDENTIAL_NAMES)
    assert _constants.is_credential_name("X-Api-Key") and _constants.is_credential_name("CLIENT_SECRET")
    assert not any(_constants.is_credential_name(name) for name in ALLOWED)


@pytest.mark.parametrize("name", sorted({s for n in LISTED for s in spellings(n)}))
@pytest.mark.parametrize("client_class", [AgentCC, AsyncAgentCC])
def test_construction_refuses_a_credential_named_default_query(client_class, name):
    with pytest.raises(AgentCCError) as caught:
        client_class(api_key="synthetic-sdk-key", base_url=ORIGIN, default_query={name: MARKER})
    assert name in str(caught.value) and MARKER not in str(caught.value)


@pytest.mark.parametrize("name", EXPECTED)
def test_every_name_in_the_shared_set_is_refused_everywhere(name):
    for variant in (name, name.replace("_", "-").upper()):
        with pytest.raises(AgentCCError) as sync_error:
            AgentCC(api_key="synthetic-sdk-key", base_url=ORIGIN, default_query={variant: MARKER})
        assert MARKER not in str(sync_error.value)
        with pytest.raises(AgentCCError):
            AsyncAgentCC(api_key="synthetic-sdk-key", base_url=ORIGIN, default_query={variant: MARKER})
        for base_class in (SyncBaseClient, AsyncBaseClient):
            with pytest.raises(AgentCCError) as base_error:
                base_class(api_key="synthetic-sdk-key", base_url=ORIGIN, default_query={variant: MARKER})
            assert MARKER not in str(base_error.value)


@pytest.mark.parametrize("name", LISTED)
@pytest.mark.parametrize("client_class", [AgentCC, AsyncAgentCC])
def test_with_options_refuses_a_credential_named_extra_query(client_class, name):
    parent = client_class(api_key="synthetic-sdk-key", base_url=ORIGIN, default_query={"tenant": "t1"})
    with pytest.raises(AgentCCError) as caught:
        parent.with_options(extra_query={name.title(): MARKER})
    assert name.title() in str(caught.value) and MARKER not in str(caught.value)
    # The parent is unchanged and still usable.
    assert parent._default_query == {"tenant": "t1"}
    parent.with_options(extra_query={"region": "eu"})


@pytest.mark.parametrize("name", ALLOWED)
def test_noncredential_names_are_accepted_at_construction_and_in_copies(name):
    client = AgentCC(api_key="synthetic-sdk-key", base_url=ORIGIN, default_query={name: "v"})
    assert client.with_options(extra_query={name + "2": "v"})._default_query == {name: "v", name + "2": "v"}


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("via", ["construction", "with_options"])
async def test_a_refused_query_never_reaches_the_wire(async_mode, via):
    sent = []

    def serve(request):
        sent.append(request)
        return httpx.Response(200, json={"id": "c", "object": "chat.completion", "created": 0, "model": "m", "choices": []})

    http = (httpx.AsyncClient if async_mode else httpx.Client)(transport=httpx.MockTransport(serve))
    cls = AsyncAgentCC if async_mode else AgentCC
    try:
        with pytest.raises(AgentCCError) as caught:
            if via == "construction":
                client = cls(api_key="synthetic-sdk-key", base_url=ORIGIN, http_client=http,
                             default_query={"Api-Key": MARKER}, max_retries=0)
            else:
                client = cls(api_key="synthetic-sdk-key", base_url=ORIGIN, http_client=http, max_retries=0)
                client = client.with_options(extra_query={"access-token": MARKER})
            result = client.chat.completions.create(model="m", messages=[])
            if inspect.isawaitable(result):
                await result
        assert sent == [] and MARKER not in str(caught.value)
    finally:
        result = http.aclose() if async_mode else http.close()
        if inspect.isawaitable(result):
            await result


def test_the_url_check_the_sinks_and_the_header_scrub_use_the_same_set():
    assert not hasattr(callback_base, "_CREDENTIAL_KEYS") or callback_base._CREDENTIAL_KEYS <= _constants.CREDENTIAL_NAMES
    assert {name.replace("-", "_") for name in _constants.CREDENTIAL_HEADER_NAMES} <= _constants.CREDENTIAL_NAMES
    for name in EXPECTED:
        header = name.replace("_", "-")
        # send-time URL check, in any spelling
        for spelling in (name, header, header.upper()):
            with pytest.raises(AgentCCError):
                validate_destination(ORIGIN, f"{ORIGIN}/v1/x?{spelling}={MARKER}")
        # sinks
        assert redact_headers({header.title(): "v"}) == {header.title(): "[REDACTED]"}
        assert callback_base.redact_credentials({header.title(): "v", "Plain": "v"}) == {
            header.title(): "[REDACTED]", "Plain": "v"}
        # header scrub, any spelling
        request = httpx.Request("GET", ORIGIN, headers={header.title(): "synthetic-value", "X-Plain": "v"})
        _scrub.scrub_reachable([request], frozenset())
        assert request.headers[header] == "[REDACTED]" and request.headers["x-plain"] == "v"
    for name in ALLOWED:
        validate_destination(ORIGIN, f"{ORIGIN}/v1/x?{name}=1")
