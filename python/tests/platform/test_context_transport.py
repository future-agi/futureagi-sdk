"""Shared Context auth/continuation conformance, with HTTP mocked at the boundary."""

from __future__ import annotations

import asyncio
import inspect

import httpx
import pytest
from fi.platform import (
    APIConnectionError,
    APIError,
    ApiKeyAuth,
    AsyncClient,
    AuthenticationError,
    Client,
    ContextAuth,
    PermissionDeniedError,
    RequestOptions,
)
from fi.platform._transport import NOT_GIVEN, operation_options

BASE = "https://backend.test"
TOKEN = "11111111-1111-4111-8111-111111111111." + "synthetic-" * 5
RESOLVE = "/model-hub/skills/contexts/resolve/"
MANIFEST = "/model-hub/skills/contexts/11111111-1111-4111-8111-111111111111/versions/7/manifest/"


async def call(client, method="GET", path=RESOLVE, **kwargs):
    result = client.request(method, path, **kwargs)
    return await result if inspect.isawaitable(result) else result


def response(result):
    return httpx.Response(200, json={"status": True, "result": result})


@pytest.fixture(params=[False, True], ids=["sync", "async"])
def factory(request):
    def make(handler=lambda r: response({}), **kwargs):
        http_cls, cls = (httpx.AsyncClient, AsyncClient) if request.param else (httpx.Client, Client)
        http = http_cls(transport=httpx.MockTransport(handler))
        return cls(base_url=BASE, http_client=http, **kwargs)
    return make


def test_context_only_with_and_without_stale_environment(factory, monkeypatch):
    async def run():
        for stale in (False, True):
            for key in ("FI_API_KEY", "FI_SECRET_KEY", "FI_WORKSPACE_ID"):
                monkeypatch.delenv(key, raising=False)
                if stale:
                    monkeypatch.setenv(key, "stale-broad-value")
            seen = []
            client = factory(lambda r: seen.append(r) or response({"resolution_id": "lease-v7", "resolution_expires_at": "2026-11-07T01:15:00Z"}), auth=ContextAuth(TOKEN))
            result = await call(client)
            assert result["resolution_id"] == "lease-v7"
            assert result["resolution_expires_at"] == "2026-11-07T01:15:00Z"
            assert seen[0].headers["authorization"] == f"Context {TOKEN}"
            assert not {"x-api-key", "x-secret-key", "x-workspace-id", "cookie"} & set(seen[0].headers)
            assert TOKEN not in repr(client._transport.config)

    asyncio.run(run())


@pytest.mark.parametrize("kwargs", [{"api_key": "broad"}, {"secret_key": "broad"}, {"api_key": ""}])
def test_mixed_config_fails_before_http(factory, kwargs):
    with pytest.raises(ValueError, match="cannot be combined"):
        factory(auth=ContextAuth(TOKEN), **kwargs)


@pytest.mark.parametrize("header", ["Authorization", "x-API-key", "X-Secret-Key", "Cookie", "Proxy-Authorization"])
def test_auth_header_overrides_rejected_in_all_layers(factory, header):
    async def run():
        with pytest.raises(ValueError, match="authentication header"):
            factory(auth=ContextAuth(TOKEN), default_headers={header: "hidden"})
        client = factory(auth=ContextAuth(TOKEN))
        with pytest.raises(ValueError, match="authentication header"):
            await call(client, options=RequestOptions(headers={header: "hidden"}))
        client._transport._http.headers[header] = "hidden"
        with pytest.raises(ValueError, match="authentication header"):
            await call(client)

    asyncio.run(run())


def test_injected_http_auth_and_cookies_rejected(factory):
    async def run():
        for mode in ("auth", "cookie"):
            client = factory(auth=ContextAuth(TOKEN))
            if mode == "auth":
                client._transport._http.auth = httpx.BasicAuth("broad", "secret")
            else:
                client._transport._http.cookies.set("session", "hidden")
            with pytest.raises(ValueError, match="without auth or cookies"):
                await call(client)

    asyncio.run(run())


def test_workspace_is_explicit_and_cannot_be_overridden(factory):
    async def run():
        seen = []
        client = factory(lambda r: seen.append(r) or response({}), auth=ContextAuth(TOKEN), workspace_id="workspace-1")
        await call(client, options=RequestOptions(headers={"x-workspace-id": "workspace-1"}))
        assert seen[0].headers.get_list("x-workspace-id") == ["workspace-1"]
        with pytest.raises(ValueError, match="workspace header"):
            await call(client, options=RequestOptions(headers={"X-WORKSPACE-ID": "workspace-2"}))
        with pytest.raises(ValueError, match="workspace header"):
            factory(auth=ContextAuth(TOKEN), default_headers={"x-workspace-id": "workspace-2"})
        assert len(seen) == 1

    asyncio.run(run())


def test_explicit_pair_ignores_ambient_keys_and_rejects_auth_overrides(factory, monkeypatch):
    async def run():
        monkeypatch.setenv("FI_API_KEY", "ambient")
        monkeypatch.setenv("FI_SECRET_KEY", "ambient")
        seen = []
        client = factory(lambda r: seen.append(r) or response({}), auth=ApiKeyAuth("explicit", "pair"))
        await call(client)
        assert seen[0].headers["x-api-key"] == "explicit"
        assert seen[0].headers["x-secret-key"] == "pair"
        assert "authorization" not in seen[0].headers
        with pytest.raises(ValueError, match="authentication header"):
            await call(client, options=RequestOptions(headers={"authorization": f"Context {TOKEN}"}))

    asyncio.run(run())


def test_lease_stays_on_exact_version_after_label_moves(factory):
    async def run():
        seen = []
        def handle(req):
            seen.append(req)
            if req.url.path == RESOLVE:
                return response({"version": 7, "version_id": "version-7", "digest": "digest-7", "resolution_id": "lease-v7", "resolution_expires_at": "2026-11-07T01:15:00Z"})
            assert req.url.path == MANIFEST
            assert req.headers["x-context-resolution"] == "lease-v7"
            # The label now points to v8; continuation is v7, not another resolve.
            return response({"version": 7, "digest": "digest-7", "file_offset": int(req.url.params["file_offset"])})
        client = factory(handle, auth=ContextAuth(TOKEN))
        resolved = await call(client, query={"name": "demo", "label": "production"})
        options = RequestOptions(resolution_id=resolved["resolution_id"])
        for offset in (25, 50):
            result = await call(client, path=MANIFEST, query={"file_offset": offset}, options=options)
            assert result["version"] == 7 and result["file_offset"] == offset
        assert len(seen) == 3

    asyncio.run(run())


@pytest.mark.parametrize("status,code,error", [
    (401, "context_credential_expired", AuthenticationError),
    (403, "context_credential_revoked", PermissionDeniedError),
    (410, "resolution_expired", APIError),
    (422, "context_quarantined", APIError),
    (304, "", APIError),
])
def test_denials_do_not_retry_or_reresolve_even_for_downloads(factory, status, code, error):
    async def run():
        seen = []
        client = factory(lambda r: seen.append(r) or httpx.Response(status, json={"code": code}), auth=ContextAuth(TOKEN))
        with pytest.raises(error) as exc:
            await call(client, path=MANIFEST, decode="bytes", options=RequestOptions(resolution_id="lease"))
        assert len(seen) == 1 and exc.value.status_code == status

    asyncio.run(run())


def test_retry_retains_caller_operation_and_lease(factory):
    async def run():
        seen = []
        client = factory(lambda r: seen.append(r) or (httpx.Response(429, headers={"retry-after": "0"}) if len(seen) == 1 else response({})), auth=ContextAuth(TOKEN))
        await call(client, "POST", "/model-hub/skills/contexts/bindings/b/receipts/", body={"event_id": "event"},
                   options=RequestOptions(resolution_id="lease", idempotency_key="original-key"))
        assert len(seen) == 2
        assert seen[0].content == seen[1].content
        assert all(r.headers["idempotency-key"] == "original-key" and r.headers["x-context-resolution"] == "lease" for r in seen)

    asyncio.run(run())


def test_unknown_post_is_not_replayed(factory):
    async def run():
        seen = []
        def handle(req):
            seen.append(req)
            raise httpx.ReadError("lost response")
        client = factory(handle, auth=ContextAuth(TOKEN))
        with pytest.raises(APIConnectionError):
            await call(client, "POST", options=RequestOptions(idempotency_key="original-key"))
        assert len(seen) == 1

    asyncio.run(run())


@pytest.mark.parametrize("target", ["/other/", "https://evil.test/token", "https://user:pass@backend.test/other/"])
def test_context_redirects_fail_closed(factory, target):
    async def run():
        seen = []
        client = factory(lambda r: seen.append(r) or httpx.Response(307, headers={"location": target}), auth=ContextAuth(TOKEN))
        with pytest.raises(APIConnectionError, match="cannot follow redirects"):
            await call(client)
        assert len(seen) == 1

    asyncio.run(run())


def test_zip_bytes_are_lossless_and_empty_bytes_are_bytes(factory):
    async def run():
        for raw in (b"PK\x00\xff\xfe\x80\r\n", b""):
            client = factory(lambda r: httpx.Response(200, content=raw, headers={"content-type": "application/zip"}), auth=ContextAuth(TOKEN))
            assert await call(client, decode="bytes", options=RequestOptions(resolution_id="lease")) == raw

    asyncio.run(run())


def test_per_call_leases_do_not_leak_between_concurrent_reads(factory):
    async def run():
        seen = []
        client = factory(lambda r: seen.append(r) or response({}), auth=ContextAuth(TOKEN))
        await asyncio.gather(*(call(client, path=MANIFEST, options=RequestOptions(resolution_id=f"lease-{i}")) for i in range(8)))
        assert {r.headers["x-context-resolution"] for r in seen} == {f"lease-{i}" for i in range(8)}
        await call(client)
        assert "x-context-resolution" not in seen[-1].headers

    asyncio.run(run())


def test_typed_headers_never_overwrite_conflicting_defaults(factory):
    async def run():
        client = factory(auth=ContextAuth(TOKEN), default_headers={"x-context-resolution": "old"})
        with pytest.raises(ValueError, match="conflicting X-Context-Resolution"):
            await call(client, options=RequestOptions(resolution_id="new"))

    asyncio.run(run())


def test_operation_header_allowlist_and_collision_checks():
    original = RequestOptions(resolution_id="lease", headers={"X-Trace": "trace"})
    merged = operation_options(original, {"X-Context-Resolution": "lease", "Idempotency-Key": "key"})
    assert merged.resolution_id == "lease" and merged.headers["Idempotency-Key"] == "key"
    assert original.headers == {"X-Trace": "trace"}
    with pytest.raises(ValueError, match="conflicting"):
        operation_options(original, {"x-context-resolution": "other"})
    with pytest.raises(ValueError, match="may only carry"):
        operation_options(None, {"X-Workspace-Id": "scope"})
    for value in (None, NOT_GIVEN):
        with pytest.raises(ValueError, match="required"):
            operation_options(None, {"Idempotency-Key": value}, required=("Idempotency-Key",))
    for value in ("", "secret\r\nInjected: yes", "white space", "é", 1):
        with pytest.raises(ValueError, match="ASCII token") as exc:
            ContextAuth(value)
        assert str(value) not in str(exc.value) or value == ""
