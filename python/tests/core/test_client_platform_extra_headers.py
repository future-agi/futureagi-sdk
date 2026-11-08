"""FI_EXTRA_HEADERS and ``extra_headers=`` on the platform executor: the same scoped, per-request
headers the core namespaces send (``fi._extra_headers``). A platform call and a ``with_options`` copy
carry them when the platform origin is under ``base_url``; the setting is read on each call; the SDK's
own headers and a declared per-call header win; an origin off ``base_url`` gets none; a malformed
setting raises before anything is sent; a reflected value never reaches an error. No network
(``httpx.MockTransport``); every header value here is made up."""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Optional

import httpx
import pytest

import fi.errors as errors
from fi import AsyncFutureAGIClient, FutureAGIClient
from fi._core.policy import OperationSpec as Op
from fi._extra_headers import ENV_VAR, ExtraHeadersError
from tests.core._support import OPS, respond

BASE = "http://api.test"
TOKEN = "fake-identity-token-" + "x" * 12  # low entropy on purpose (never a real token)
PROXY = f"Bearer {TOKEN}"
KEYS = {"api_key": "k-test-1234", "secret_key": "s-test-1234"}
CAPABILITIES = "/omega/api/workspace/capabilities"
TABLE = {
    **OPS,
    "team.get": Op(name="team.get", family="platform", method="GET", path="/workspace/team", headers=("x-team",)),
}


@pytest.fixture(autouse=True)
def _setting(monkeypatch):
    monkeypatch.setenv(ENV_VAR, f"Proxy-Authorization={PROXY};X-Team=env-team")
    for name in ("FI_PLATFORM_BASE_URL", "FI_PLATFORM_TOKEN", "FI_WORKSPACE_ID", "FI_ORGANIZATION_ID"):
        monkeypatch.delenv(name, raising=False)


def _wire(client: Any, requests: list, answer: Optional[Callable[[httpx.Request], httpx.Response]] = None) -> None:
    """Send the client's core and platform requests to one recording MockTransport."""

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return answer(request) if answer is not None else respond(200, {"ok": 1})

    mock = httpx.MockTransport(handler)
    transport = client.generated_client._httpx_args["transport"]
    transport._wrapped = transport._wrapped_async = mock
    client._platform.shared._recorder._inner = mock
    client._platform.shared.table = TABLE


def _carries(request: httpx.Request, team: str = "argument-team") -> bool:
    return request.headers.get("Proxy-Authorization") == PROXY and request.headers.get("X-Team") == team


def test_platform_calls_and_copies_carry_the_extra_headers_core_calls_carry():
    requests: list = []
    client = FutureAGIClient(**KEYS, base_url=BASE, retries=0, extra_headers={"X-Team": "argument-team"})
    _wire(client, requests)
    client.users.current()
    client._platform.call("capabilities.get")
    copy = client.with_options(timeout=5)
    copy._platform.call("capabilities.get")
    copy.users.current()
    assert [r.url.path for r in requests][1:3] == [CAPABILITIES, CAPABILITIES]
    assert len(requests) == 4 and all(_carries(r) for r in requests)
    assert requests[1].headers["X-Api-Key"] == "k-test-1234"
    copy.close()
    client.close()


def test_async_platform_calls_and_copies_carry_them_too():
    async def go() -> list:
        requests: list = []
        client = AsyncFutureAGIClient(**KEYS, base_url=BASE, retries=0, extra_headers="X-Team=argument-team")
        _wire(client, requests)
        await client.request("GET", "/core-probe")
        await client._platform.call("capabilities.get")
        copy = client.with_options(timeout=5)
        await copy._platform.call("capabilities.get")
        await copy.request("GET", "/core-probe")
        await client.aclose()
        return requests

    requests = asyncio.run(go())
    assert [r.url.path for r in requests] == ["/core-probe", CAPABILITIES, CAPABILITIES, "/core-probe"]
    assert all(_carries(r) for r in requests)


def test_the_setting_is_read_on_each_platform_call(monkeypatch):
    requests: list = []
    client = FutureAGIClient(**KEYS, base_url=BASE, retries=0, extra_headers={"X-Arg": "argument-value"})
    _wire(client, requests)
    client._platform.call("capabilities.get")
    monkeypatch.setenv(ENV_VAR, "Proxy-Authorization=Bearer refreshed-token-yyyyyyyy")
    client._platform.call("capabilities.get")
    monkeypatch.delenv(ENV_VAR)
    client._platform.call("capabilities.get")
    first, refreshed, unset = (r.headers for r in requests)
    assert first["Proxy-Authorization"] == PROXY and first["X-Team"] == "env-team"
    assert refreshed["Proxy-Authorization"] == "Bearer refreshed-token-yyyyyyyy" and "X-Team" not in refreshed
    assert "Proxy-Authorization" not in unset
    assert [h.get("X-Arg") for h in (first, refreshed, unset)] == ["argument-value"] * 3
    client.close()


def test_the_sdks_own_headers_and_a_declared_header_win_over_extra_headers():
    requests: list = []
    client = FutureAGIClient(
        **KEYS,
        base_url=BASE,
        retries=0,
        workspace_id="ws-own",
        extra_headers={"x-workspace-id": "ws-extra", "Accept": "text/plain", "X-Team": "argument-team"},
    )
    _wire(client, requests)
    client._platform.call("team.get", headers={"X-Team": "caller-team"})
    client._platform.call("team.get")
    declared, plain = (r.headers for r in requests)
    assert declared["Proxy-Authorization"] == PROXY
    assert declared.get_list("X-Workspace-Id") == ["ws-own"] and declared.get_list("Accept") == ["application/json"]
    assert declared.get_list("X-Team") == ["caller-team"] and plain.get_list("X-Team") == ["argument-team"]
    client.close()


@pytest.mark.parametrize(
    ("base_url", "platform_base_url", "sent"),
    [
        (BASE, "http://platform.other.test/omega/api", False),
        ("http://api.test/tenant", "http://api.test/other/omega/api", False),
        ("http://api.test/tenant", None, True),
    ],
)
def test_only_a_platform_origin_under_the_base_url_gets_them(base_url, platform_base_url, sent):
    requests: list = []
    client = FutureAGIClient(
        **KEYS,
        base_url=base_url,
        retries=0,
        platform_base_url=platform_base_url,
        extra_headers={"X-Team": "argument-team"},
    )
    _wire(client, requests)
    client.users.current()
    client._platform.call("capabilities.get")
    core, platform = requests
    assert _carries(core) and platform.url.path.endswith("/omega/api/workspace/capabilities")
    if sent:
        assert _carries(platform)
    else:
        assert "Proxy-Authorization" not in platform.headers and "X-Team" not in platform.headers
    client.close()


@pytest.mark.parametrize("mode", ["sync", "async"])
def test_a_malformed_setting_raises_before_any_platform_request(monkeypatch, mode):
    monkeypatch.setenv(ENV_VAR, f"Proxy-Authorization {PROXY}")
    requests: list = []
    client: Any = (FutureAGIClient if mode == "sync" else AsyncFutureAGIClient)(**KEYS, base_url=BASE, retries=3)
    _wire(client, requests)
    with pytest.raises(ExtraHeadersError) as caught:
        result = client._platform.call("capabilities.get")
        if mode == "async":
            asyncio.run(result)
    assert TOKEN not in str(caught.value)
    assert requests == []


def test_a_reflected_extra_header_value_never_reaches_a_platform_error():
    requests: list = []
    client = FutureAGIClient(**KEYS, base_url=BASE, retries=0)
    _wire(client, requests, lambda r: respond(403, {"code": "forbidden", "message": f"proxy refused {PROXY}"}))
    with pytest.raises(errors.FutureAGIAPIError) as caught:
        client._platform.call("capabilities.get")
    assert requests[0].headers["Proxy-Authorization"] == PROXY
    assert "proxy refused" in str(caught.value)
    assert TOKEN not in str(caught.value) and TOKEN not in repr(caught.value.payload)
    client.close()


QUOTE, BACKSLASH, SLASH = 'fake-quote-"-header-value', "fake-backslash-\\-header-value", "fake-slash/header-value"
# raw JSON text that writes SLASH's "/" as the optional escape a JSON encoder may use, as a message and a key
SLASH_TEXT = (
    '{"code": "forbidden", "message": "proxy refused fake-slash\\/header-value", "fake-slash\\/header-value": 1}'
)


def _strings(value: Any) -> list:
    """Every string in a decoded value, keys included."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [s for item in value for s in _strings(item)]
    if isinstance(value, dict):
        return [s for k, v in value.items() for s in (str(k), *_strings(v))]
    return []


def _call(client: Any, mode: str) -> None:
    if mode == "sync":
        try:
            client._platform.call("capabilities.get")
        finally:
            client.close()
        return

    async def go() -> None:
        try:
            await client._platform.call("capabilities.get")
        finally:
            await client.aclose()

    asyncio.run(go())


@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize(
    ("value", "body"),
    [
        pytest.param(QUOTE, {"code": "forbidden", "message": f"proxy refused {QUOTE}", QUOTE: 1}, id="quote"),
        pytest.param(
            BACKSLASH, {"code": "forbidden", "message": f"proxy refused {BACKSLASH}", BACKSLASH: 1}, id="backslash"
        ),
        pytest.param(SLASH, SLASH_TEXT, id="slash-escape"),
    ],
)
def test_a_reflected_value_the_server_escaped_in_its_json_is_scrubbed_once_decoded(mode, value, body):
    requests: list = []
    client: Any = (FutureAGIClient if mode == "sync" else AsyncFutureAGIClient)(
        **KEYS, base_url=BASE, retries=0, extra_headers={"X-Probe": value}
    )
    _wire(client, requests, lambda r: respond(403, body))
    with pytest.raises(errors.FutureAGIAPIError) as caught:
        _call(client, mode)
    error = caught.value
    assert requests[0].headers["X-Probe"] == value
    assert error.code == "forbidden" and "proxy refused [redacted]" in str(error)  # scrubbed, not dropped
    assert value not in str(error)
    assert not [s for s in _strings(error.payload) if value in s]


@pytest.mark.parametrize("mode", ["sync", "async"])
def test_a_reflected_value_in_a_body_that_is_not_json_is_never_echoed(mode):
    requests: list = []
    client: Any = (FutureAGIClient if mode == "sync" else AsyncFutureAGIClient)(
        **KEYS, base_url=BASE, retries=0, extra_headers={"X-Probe": QUOTE}
    )
    _wire(client, requests, lambda r: respond(403, f"<html>proxy refused {QUOTE}</html>"))
    with pytest.raises(errors.FutureAGIAPIError) as caught:
        _call(client, mode)
    assert requests[0].headers["X-Probe"] == QUOTE
    assert caught.value.payload is None and "proxy refused" not in str(caught.value)
    assert QUOTE not in str(caught.value)
