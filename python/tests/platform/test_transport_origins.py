"""Redirects and caller-supplied clients of the platform transport, with https and loopback base URLs.

These run without ``FI_ALLOW_INSECURE_HTTP``. The clients answer through ``httpx.MockTransport``, which makes no
connection; requests over real connections are covered in ``tests/test_keyed_request_paths.py`` and
``tests/test_plain_http_key_guards.py``."""

from __future__ import annotations

import asyncio
import os

import fi.platform as fp
import httpx
import pytest
from fi.errors import KeyedRedirectRefusedError
from fi.platform import _transport

BASES = ["https://backend.test", "http://127.0.0.1:8000"]


@pytest.fixture(autouse=True)
def _no_backoff_and_no_opt_in(monkeypatch):
    monkeypatch.setattr(_transport.time, "sleep", lambda s: None)
    monkeypatch.delenv("FI_ALLOW_INSECURE_HTTP", raising=False)


def _client(base, handler, **kw) -> fp.Client:
    http = httpx.Client(transport=httpx.MockTransport(handler))
    return fp.Client(api_key="k", secret_key="s", base_url=base, http_client=http, **kw)


def _dataset_response() -> httpx.Response:
    return httpx.Response(200, json={"status": True, "result": {"message": "ok", "dataset_id": "d1", "dataset_name": "x"}})


def test_opt_in_is_not_set():
    assert os.environ.get("FI_ALLOW_INSECURE_HTTP") is None


@pytest.mark.parametrize("base", BASES)
def test_callers_client_is_neither_reconfigured_nor_closed(base):
    http = httpx.Client(base_url="https://my-service", timeout=5, transport=httpx.MockTransport(lambda r: _dataset_response()))
    with fp.Client(api_key="k", secret_key="s", base_url=base, http_client=http) as client:
        client.datasets.create(new_dataset_name="x")
    assert str(http.base_url).rstrip("/") == "https://my-service"
    assert http.timeout.read == 5
    assert not http.is_closed


@pytest.mark.parametrize("base", BASES)
def test_redirect_without_a_target_is_an_error(base):
    client = _client(base, lambda r: httpx.Response(301))
    with pytest.raises(KeyedRedirectRefusedError, match="not followed") as exc:
        client.datasets.list().first_page()
    assert exc.value.status_code == 301
    assert exc.value.get_error_code() == "KEYED_REDIRECT_REFUSED"


@pytest.mark.parametrize("base", BASES)
def test_redirect_within_the_origin_fetches_the_page_with_keys_and_workspace(base):
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if len(seen) == 1:
            return httpx.Response(307, headers={"location": "/model-hub/develops/get-datasets/"})
        return httpx.Response(200, json={"status": True, "result": {"datasets": [], "total_pages": 1}})

    page = _client(base, handler, workspace_id="w1").datasets.list().first_page()
    assert page.number == 0 and page.items == []
    assert page.raw == {"datasets": [], "total_pages": 1}
    target = f"{base}/model-hub/develops/get-datasets/"
    assert [(r.method, str(r.url)) for r in seen] == [("GET", target + "?page=0"), ("GET", target)]
    assert [(r.headers["x-api-key"], r.headers["x-secret-key"], r.headers["x-workspace-id"]) for r in seen] == [
        ("k", "s", "w1"), ("k", "s", "w1"),
    ]


@pytest.mark.parametrize("base", BASES)
def test_303_redirect_fetches_the_result_with_a_keyed_get(base):
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        request.read()
        return httpx.Response(303, headers={"location": f"{base}/done/"}) if len(seen) == 1 else _dataset_response()

    result = _client(base, handler).datasets.create(new_dataset_name="x")
    assert result.dataset_id == "d1" and result.dataset_name == "x" and result.message == "ok"
    assert [(r.method, str(r.url)) for r in seen] == [
        ("POST", f"{base}/model-hub/develops/create-empty-dataset/"), ("GET", f"{base}/done/"),
    ]
    assert seen[0].content and seen[1].content == b""
    assert all(r.headers["x-api-key"] == "k" and r.headers["x-secret-key"] == "s" for r in seen)


@pytest.mark.parametrize("base", BASES)
def test_redirect_off_the_origin_is_refused(base):
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.host)
        return httpx.Response(302, headers={"location": "https://other.example/collect"})

    with pytest.raises(KeyedRedirectRefusedError, match="not followed") as exc:
        _client(base, handler).datasets.list().first_page()
    assert seen == [httpx.URL(base).host]
    assert exc.value.get_error_code() == "KEYED_REDIRECT_REFUSED"


@pytest.mark.parametrize("base", BASES)
def test_callers_client_that_follows_redirects_itself_is_held_to_the_origin(base):
    origin = httpx.URL(base).host
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(f"{request.url.host} {request.headers.get('x-api-key')}")
        if request.url.host == origin:
            return httpx.Response(302, headers={"location": "https://other.test/collect"})
        return httpx.Response(200, json={"status": True, "result": {}})

    http = httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True)
    client = fp.Client(api_key="synthetic-key", secret_key="s", base_url=base, http_client=http)
    with pytest.raises(KeyedRedirectRefusedError, match="not followed") as exc:
        client.request("GET", "/probe/")
    assert seen == [f"{origin} synthetic-key"]
    assert exc.value.get_error_code() == "KEYED_REDIRECT_REFUSED"

    async def handler_async(request: httpx.Request) -> httpx.Response:
        return handler(request)

    async def scenario() -> None:
        seen.clear()
        http = httpx.AsyncClient(transport=httpx.MockTransport(handler_async), follow_redirects=True)
        async with fp.AsyncClient(api_key="synthetic-key", secret_key="s", base_url=base, http_client=http) as client:
            with pytest.raises(KeyedRedirectRefusedError, match="not followed") as exc:
                await client.request("POST", "/probe/", body={"x": 1})
            assert exc.value.get_error_code() == "KEYED_REDIRECT_REFUSED"

    asyncio.run(scenario())
    assert seen == [f"{origin} synthetic-key"]


@pytest.mark.parametrize("base", BASES)
def test_redirect_loop_stops_at_the_hop_limit(base):
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(302, headers={"location": f"{base}/again/"})

    with pytest.raises(fp.APIConnectionError, match="more than 5 redirects"):
        _client(base, handler).datasets.list().first_page()
    assert [(r.method, str(r.url)) for r in seen] == [
        ("GET", f"{base}/model-hub/develops/get-datasets/?page=0"),
    ] + [("GET", f"{base}/again/")] * 5
    assert all(r.headers["x-api-key"] == "k" and r.headers["x-secret-key"] == "s" for r in seen)
