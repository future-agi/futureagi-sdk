"""The hand-written transport, against an in-process httpx MockTransport (no backend)."""

from __future__ import annotations

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


def test_import_fi_does_not_load_the_platform_client():
    code = "import fi, sys; print(json.dumps(['fi.platform' in sys.modules, fi.Client.__name__, 'fi.platform' in sys.modules]))"
    out = subprocess.run([sys.executable, "-c", "import json; " + code], capture_output=True, text=True, check=True).stdout
    assert json.loads(out) == [False, "Client", True]
