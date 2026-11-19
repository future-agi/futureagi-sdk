"""Every connector wrapper is exercised on a mock transport in both Python modes."""
from __future__ import annotations

import asyncio
import inspect
import json
import re
from pathlib import Path
from urllib.parse import quote

import httpx
import pytest

from fi import FutureAGIClient, AsyncFutureAGIClient
from fi._http import ClientRetryingTransport
from fi.errors import FutureAGIAPIError, UnexpectedRedirectError
from tests.connectors.surface import SURFACE, NAMESPACES, enabled, assert_absent

ROOT = Path(__file__).resolve().parents[3]
MAP = json.loads((ROOT / "openapi/connectors/wrapper-map.json").read_text())["operations"]
ROWS = [(name, MAP[name]) for methods in SURFACE.values() for name in methods]
SPECS = {key: json.loads((ROOT / f"openapi/connectors/{key}.json").read_text()) for key in ("ee", "fa")}


def contract(name, row):
    for path, item in SPECS[row["source"]]["paths"].items():
        for verb in ("get", "post", "put", "patch", "delete"):
            op = item.get(verb, {})
            if op.get("operationId") == row["operation_id"]:
                return verb.upper(), path, op
    raise AssertionError(name)


def payload(name):
    if name == "connectors.connect":
        return {"authorizeUrl": "https://provider.invalid/consent?state=opaque"}
    if name == "platform.credentials.list":
        return {"credentials": [{"id": "credential-one"}]}
    if name == "integrations_connections_list":
        return {"status": True, "result": {"connections": [{"id": "one"}], "metadata": {"total_count": 1}}}
    if name == "integrations_sync-logs_list":
        return {"status": True, "result": {"sync_logs": [{"id": "one"}], "metadata": {"total_count": 1}}}
    if name == "integrations_connections_slack_channels_list":
        return {"status": True, "result": {"channels": [{"id": "channel-one"}], "next_cursor": None}}
    return {"status": True, "result": {"id": "one"}} if name.startswith("integrations_") else {"id": "one"}


def make_client(asynchronous, handler, retries=0):
    cls = AsyncFutureAGIClient if asynchronous else FutureAGIClient
    client = cls(api_key="test-person-key", secret_key="test-person-secret", base_url="http://127.0.0.1:9",
                 platform_base_url="http://127.0.0.1:9/omega/api", organization_id="org-a", workspace_id="ws-a", retries=retries)
    mock = httpx.MockTransport(handler)
    client._platform.shared._recorder._inner = mock
    client._platform.shared._recorder._inner_async = mock
    client._platform.shared.backoff_base_s = 0
    client._platform.shared.sleep = lambda _: None
    client.generated_client.set_httpx_client(httpx.Client(base_url=client.base_url, transport=ClientRetryingTransport(wrapped=mock, wrapped_async=mock, retries=retries, backoff_base_s=0), auth=client._auth))
    client.generated_client.set_async_httpx_client(httpx.AsyncClient(base_url=client.base_url, transport=ClientRetryingTransport(wrapped=mock, wrapped_async=mock, retries=retries, backoff_base_s=0), auth=client._auth))
    return client


def invoke(client, row):
    method = row["methods"][0]
    fn = client
    for part in method["py"].split(".")[1:]:
        fn = getattr(fn, part)
    args, kwargs, keyword = [], {}, False
    for arg in method["py_args"]:
        if arg == "*":
            keyword = True
            continue
        value = {"body": {"display_name": "fixture"}, "mine": "1", "cursor": "opaque/cursor", "page_number": 0,
                 "page_size": 2, "page": 1, "limit": 2}.get(arg, "id /?value")
        if keyword:
            kwargs[arg] = value
        else:
            args.append(value)
    return fn(*args, **kwargs)


async def result(value):
    return await value if inspect.isawaitable(value) else value


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("name,row", ROWS, ids=[n for n, _ in ROWS])
def test_wire_contract(name, row, asynchronous):
    if not enabled(row["feature"]):
        assert_absent(make_client(asynchronous, lambda _: pytest.fail("unexpected request")), name)
        return
    seen = []
    def handler(request):
        seen.append(request)
        return httpx.Response(200, json=payload(name))
    client = make_client(asynchronous, handler)
    value = asyncio.run(result(invoke(client, row)))
    verb, path, op = contract(name, row)
    expected = re.sub(r"\{[^}]+\}", quote("id /?value", safe=""), path)
    request = seen[0]
    assert len(seen) == 1
    assert request.method == verb
    assert request.url.raw_path.split(b"?")[0].decode() == ("/omega/api" if row["source"] == "ee" else "") + expected
    assert request.headers["x-api-key"] == "test-person-key"
    assert request.headers["x-secret-key"] == "test-person-secret"
    assert request.headers["x-organization-id"] == "org-a"
    assert request.headers["x-workspace-id"] == "ws-a"
    assert "idempotency-key" not in request.headers
    if name == "connectors.connect":
        assert value == payload(name)["authorizeUrl"]
    elif name.endswith("_list") or name == "platform.credentials.list":
        assert value.items
    elif row["source"] == "fa":
        assert value == payload(name)["result"]
    else:
        assert value == payload(name)
    if "body" in row["methods"][0]["py_args"]:
        assert json.loads(request.content) == {"display_name": "fixture"}
    elif verb == "POST":
        assert json.loads(request.content) == {}
    else:
        assert not request.content


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("name,row", ROWS, ids=[n for n, _ in ROWS])
@pytest.mark.parametrize("status", [400, 401, 403, 404, 409, 413, 422, 429, 500, 503])
def test_typed_failures_never_change_tenant_or_follow_provider(name, row, status, asynchronous):
    if not enabled(row["feature"]):
        assert_absent(make_client(asynchronous, lambda _: pytest.fail("unexpected request")), name)
        return
    seen = []
    def handler(request):
        seen.append(request)
        return httpx.Response(status, json={"code": "scope_denied", "message": "not permitted"})
    with pytest.raises(FutureAGIAPIError) as exc:
        asyncio.run(result(invoke(make_client(asynchronous, handler), row)))
    assert exc.value.status_code == status
    expected = {400: "BadRequestError", 401: "AuthenticationError", 403: "PermissionDeniedError", 404: "NotFoundError",
                409: "ConflictError", 413: "PayloadTooLargeError", 422: "UnprocessableEntityError", 429: "RateLimitError"}.get(status, "ServerError")
    assert type(exc.value).__name__ == expected
    assert exc.value.code == "scope_denied"
    assert len(seen) == 1


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("name,row", ROWS, ids=[n for n, _ in ROWS])
def test_redirect_refused(name, row, asynchronous):
    if not enabled(row["feature"]):
        assert_absent(make_client(asynchronous, lambda _: pytest.fail("unexpected request")), name)
        return
    seen = []
    def handler(request):
        seen.append(request)
        return httpx.Response(302, headers={"Location": "https://provider.invalid/callback"})
    with pytest.raises(UnexpectedRedirectError):
        asyncio.run(result(invoke(make_client(asynchronous, handler), row)))
    assert len(seen) == 1


@pytest.mark.parametrize("asynchronous", [False, True])
def test_unsafe_connect_is_not_retried_after_service_error(asynchronous):
    if not enabled("oauth_connect"):
        assert_absent(make_client(asynchronous, lambda _: pytest.fail("unexpected request")), "connectors.connect")
        return
    seen = []
    def handler(request):
        seen.append(request)
        return httpx.Response(503, json={"code": "unavailable"})
    with pytest.raises(FutureAGIAPIError):
        asyncio.run(result(invoke(make_client(asynchronous, handler, retries=2), MAP["connectors.connect"])))
    assert len(seen) == 1


def test_no_credential_mutations_or_oauth_completion():
    client = make_client(False, lambda _: pytest.fail("unexpected request"))
    for namespace, methods in {"credentials": ("create", "delete", "revoke", "rotate"),
                               "connectors": ("complete_oauth",), "integrations": ("slack_install",)}.items():
        if enabled(NAMESPACES[namespace]):
            for name in methods:
                assert not hasattr(getattr(client, namespace), name)
        else:
            assert not hasattr(client, namespace)
    for row in MAP.values():
        if "unwrapped" in row:
            assert row.get("languages") == {"py": "NOT-OFFERED", "ts": "NOT-OFFERED"}


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("namespace", ["connectors", "integrations"])
@pytest.mark.parametrize("status,code,expected", [(404, "product_not_admitted", "ProductNotAvailableError"),
    (409, "idempotency_key_in_progress", "IdempotencyKeyInProgressError"),
    (422, "idempotency_key_reused", "IdempotencyKeyReusedError")])
def test_narrow_error_codes(namespace, status, code, expected, asynchronous):
    client = make_client(asynchronous, lambda _: httpx.Response(status, json={"status": False, "code": code}))
    if not enabled(NAMESPACES[namespace]):
        assert not hasattr(client, namespace)
        return
    with pytest.raises(FutureAGIAPIError) as exc:
        asyncio.run(result(getattr(client, namespace).get("one")))
    assert type(exc.value).__name__ == expected
    assert exc.value.code == code


@pytest.mark.parametrize("asynchronous", [False, True])
def test_with_options_keeps_connector_policy_and_uses_copy_settings(asynchronous):
    seen = []
    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"id": "one"})
    client = make_client(asynchronous, handler)
    quick = client.with_options(timeout=0.75, retries=0)
    if enabled("mcp_core"):
        assert asyncio.run(result(quick.connectors.get("one"))) == {"id": "one"}
        assert seen[0].extensions["timeout"]["read"] == 0.75
    else:
        assert_absent(quick, "connectors.get")
        assert not seen
    assert quick._platform.shared is client._platform.shared


@pytest.mark.parametrize("asynchronous", [False, True])
def test_numbered_and_cursor_pagination(asynchronous):
    seen = []
    def handler(request):
        seen.append(request)
        if "slack/channels" in request.url.path:
            following = request.url.params.get("cursor")
            return httpx.Response(200, json={"result": {"channels": [{"id": "two" if following else "one"}], "next_cursor": None if following else "opaque/next"}})
        page = int(request.url.params["page_number"])
        return httpx.Response(200, json={"result": {"connections": [{"id": str(page)}], "metadata": {"total_count": 2}}})
    client = make_client(asynchronous, handler)
    async def walk():
        if not enabled("data_integrations"):
            assert_absent(client, "integrations_connections_list")
            assert_absent(client, "integrations_connections_slack_channels_list")
            return
        page = await result(client.integrations.list(page_size=50))
        if asynchronous:
            assert [item["id"] async for item in page] == ["0", "1"]
        else:
            assert [item["id"] for item in page] == ["0", "1"]
        if not enabled("slack_channels"):
            assert_absent(client, "integrations_connections_slack_channels_list")
            return
        channels = await result(client.integrations.slack_channels("connection"))
        if asynchronous:
            assert [item["id"] async for item in channels] == ["one", "two"]
        else:
            assert [item["id"] for item in channels] == ["one", "two"]
    asyncio.run(walk())
    assert len(seen) == 2 * (int(enabled("data_integrations")) + int(enabled("slack_channels")))
    if enabled("slack_channels"):
        assert seen[-1].url.params["cursor"] == "opaque/next"
