"""The hand-written transport, against an in-process httpx MockTransport (no backend)."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys

import fi.platform as fp
import httpx
import pytest
from fi.platform import _transport
from fi.utils.errors import SDKException

BASE = "http://backend.test"


@pytest.fixture(autouse=True)
def _no_backoff(monkeypatch):
    monkeypatch.setattr(_transport.time, "sleep", lambda s: None)


def _client(handler, **kw) -> fp.Client:
    http = httpx.Client(transport=httpx.MockTransport(handler))
    return fp.Client(api_key="k", secret_key="s", base_url=BASE, http_client=http, **kw)


def _dataset_response() -> httpx.Response:
    return httpx.Response(200, json={"status": True, "result": {"message": "ok", "dataset_id": "d1", "dataset_name": "x"}})


def test_write_is_not_retried_on_5xx_but_read_is():
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.method)
        if len([c for c in calls if c == request.method]) == 1:
            return httpx.Response(503, json={"detail": "busy"})
        return _dataset_response() if request.method == "POST" else httpx.Response(200, json={"status": True, "result": {"datasets": [], "total_pages": 1}})

    client = _client(handler, max_retries=2)
    with pytest.raises(fp.InternalServerError):  # a POST may already have been applied
        client.datasets.create(new_dataset_name="x")
    assert calls == ["POST"]
    client.datasets.list().first_page()  # a GET is safe to repeat
    assert calls == ["POST", "GET", "GET"]


def test_429_is_retried_for_any_method():
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(429, headers={"retry-after": "0"}) if len(calls) == 1 else _dataset_response()

    assert _client(handler, max_retries=1).datasets.create(new_dataset_name="x").dataset_id == "d1"
    assert len(calls) == 2


def test_connection_error_is_not_retried_for_a_write():
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        raise httpx.ConnectError("boom")

    with pytest.raises(fp.APIConnectionError):
        _client(handler, max_retries=2).datasets.create(new_dataset_name="x")
    assert len(calls) == 1


def test_callers_client_is_neither_reconfigured_nor_closed():
    http = httpx.Client(base_url="http://my-service", timeout=5, transport=httpx.MockTransport(lambda r: _dataset_response()))
    with fp.Client(api_key="k", secret_key="s", base_url=BASE, http_client=http) as client:
        client.datasets.create(new_dataset_name="x")
    assert str(http.base_url).rstrip("/") == "http://my-service"
    assert http.timeout.read == 5
    assert not http.is_closed


def test_request_goes_to_the_configured_base_url_with_its_own_timeout():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["timeout"] = request.extensions.get("timeout")
        return _dataset_response()

    _client(handler, timeout=7).datasets.create(new_dataset_name="x")
    assert seen["url"] == f"{BASE}/model-hub/develops/create-empty-dataset/"
    assert seen["timeout"]["read"] == 7


def test_non_json_success_body_is_an_api_error():
    client = _client(lambda r: httpx.Response(200, text="<html>maintenance</html>", headers={"content-type": "text/html"}))
    with pytest.raises(fp.APIError, match="non-JSON"):
        client.datasets.create(new_dataset_name="x")


def test_unfollowed_redirect_is_an_error_not_an_empty_result():
    client = _client(lambda r: httpx.Response(301, headers={"location": "https://api.futureagi.com/"}))
    with pytest.raises(fp.APIError) as exc:
        client.datasets.list().first_page()
    assert exc.value.status_code == 301


def test_field_errors_appear_in_the_message():
    client = _client(lambda r: httpx.Response(400, json={"status": False, "detail": {"new_dataset_name": ["This field may not be blank."]}}))
    with pytest.raises(fp.BadRequestError) as exc:
        client.datasets.create(new_dataset_name="")
    assert "new_dataset_name" in str(exc.value) and "may not be blank" in str(exc.value)
    assert exc.value.detail == {"new_dataset_name": ["This field may not be blank."]}


def test_errors_share_the_packages_base_exception():
    assert issubclass(fp.FutureAGIError, SDKException)
    client = _client(lambda r: httpx.Response(404, json={"detail": "nope"}))
    with pytest.raises(SDKException):
        client.datasets.get("missing")


def test_multipart_operation_sends_form_fields_and_files(tmp_path):
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["content_type"] = request.headers["content-type"]
        seen["body"] = request.read()
        return httpx.Response(200, json={"status": True, "result": {"detail": "ok", "kb_id": "kb1", "kb_name": "x", "file_ids": ["f1", "f2"]}})

    path = tmp_path / "notes.txt"
    path.write_bytes(b"from a path")
    client = _client(handler)
    result = client.knowledge_bases.create(name="x", files=[path, ("inline.txt", b"from bytes")])
    assert result.kb_id == "kb1"
    assert seen["content_type"].startswith("multipart/form-data")
    body = seen["body"]
    assert b'name="name"\r\n\r\nx' in body
    assert b'name="file"; filename="notes.txt"' in body and b"from a path" in body
    assert b'name="file"; filename="inline.txt"' in body and b"from bytes" in body


def test_files_on_a_json_operation_are_rejected():
    client = _client(lambda r: _dataset_response())
    with pytest.raises(TypeError, match="multipart"):
        client._transport.request(fp._generated.resources.OP_DATASETS_CREATE, body={"new_dataset_name": "x"}, files={"file": b"x"})


def test_import_fi_does_not_load_the_platform_client():
    code = "import fi, sys; print(json.dumps(['fi.platform' in sys.modules, fi.Client.__name__, 'fi.platform' in sys.modules]))"
    out = subprocess.run([sys.executable, "-c", "import json; " + code], capture_output=True, text=True, check=True).stdout
    assert json.loads(out) == [False, "Client", True]


def test_per_call_options_override_headers_timeout_and_retries():
    seen: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append({"headers": dict(request.headers), "timeout": request.extensions.get("timeout")})
        if len(seen) == 1:
            return httpx.Response(503)
        if request.method == "GET":
            return httpx.Response(200, json={"status": True, "result": {"datasets": [], "total_pages": 1}})
        return _dataset_response()

    client = _client(handler, timeout=30, max_retries=0, default_headers={"X-Team": "sdk", "User-Agent": "mine"})
    options = fp.RequestOptions(headers={"X-Trace": "t1", "X-Team": "override"}, timeout=3, max_retries=1)
    page = client.datasets.list(options=options).first_page()  # the first 503 is retried
    assert page.number == 0 and len(seen) == 2  # the per-call max_retries allowed one retry of the GET
    headers = seen[-1]["headers"]
    assert headers["x-api-key"] == "k" and headers["x-trace"] == "t1" and headers["x-team"] == "override" and headers["user-agent"] == "mine"
    assert seen[-1]["timeout"]["read"] == 3
    client.datasets.create(new_dataset_name="x")  # without options: client defaults
    assert seen[-1]["timeout"]["read"] == 30 and seen[-1]["headers"]["x-team"] == "sdk" and "x-trace" not in seen[-1]["headers"]


def test_client_request_reaches_any_endpoint_with_the_same_plumbing():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"], seen["body"], seen["auth"] = str(request.url), request.read(), request.headers.get("x-api-key")
        if request.method == "DELETE":
            return httpx.Response(404, json={"status": False, "detail": "gone"})
        return httpx.Response(200, json={"status": True, "result": {"ids": ["s1"]}, "message": "created"})

    client = _client(handler)
    assert client.request("POST", "/tracer/observation-span/create_otel_span/", body=[{"name": "s"}], query={"v": 1}) == {"ids": ["s1"]}
    assert seen["url"] == f"{BASE}/tracer/observation-span/create_otel_span/?v=1" and seen["body"] == b'[{"name":"s"}]' and seen["auth"] == "k"
    assert client.request("POST", "/x/", unwrap=None) == {"status": True, "result": {"ids": ["s1"]}, "message": "created"}
    with pytest.raises(fp.NotFoundError):
        client.request("DELETE", "/x/")
    with pytest.raises(ValueError, match="start with"):
        client.request("GET", "relative/")
    assert client.spans.ingest([{"name": "s"}]) == {"ids": ["s1"]}  # the hand-written resource method uses the same path


def test_async_client_request_and_options():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": True, "result": {"ids": [request.headers["x-trace"]]}})

    async def scenario() -> None:
        http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        async with fp.AsyncClient(api_key="k", secret_key="s", base_url=BASE, http_client=http) as client:
            assert await client.spans.ingest([{}], options=fp.RequestOptions(headers={"X-Trace": "a"})) == {"ids": ["a"]}
            assert await client.request("GET", "/x/", options=fp.RequestOptions(headers={"X-Trace": "b"})) == {"ids": ["b"]}

    asyncio.run(scenario())  # plain pytest, no asyncio plugin needed
