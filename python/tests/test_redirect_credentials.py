"""Synthetic redirect responses through requests' real redirect machinery; no network."""

import json
import socket

import pytest
import requests
from requests.adapters import BaseAdapter

from fi.api.auth import APIKeyAuth
from fi.api.types import HttpMethod, RequestConfig
from fi.kb.client import KnowledgeBase
from fi.kb.types import KnowledgeBaseConfig


BASE = "https://platform.test/api"
KEY_HEADERS = {"X-Api-Key": "synthetic-api", "X-Secret-Key": "synthetic-secret"}
OFF_ORIGIN = [
    "https://other.test/api/landed",
    "http://platform.test/api/landed",
    "https://platform.test:8443/api/landed",
    "https://platform.test:0/api/landed",
    "//other.test/api/landed",
]


@pytest.fixture(autouse=True)
def isolated(monkeypatch, tmp_path):
    monkeypatch.delenv("FI_EXTRA_HEADERS", raising=False)
    monkeypatch.setenv("FI_LOGIN_FILE", str(tmp_path / "missing-login.json"))

    def no_network(*args, **kwargs):
        raise AssertionError("Unexpected network access")

    monkeypatch.setattr(socket.socket, "connect", no_network)
    monkeypatch.setattr(socket, "create_connection", no_network)
    monkeypatch.setattr(socket, "getaddrinfo", no_network)


class RedirectAdapter(BaseAdapter):
    def __init__(self, locations, status=302):
        self.locations = locations
        self.status = status
        self.calls = []

    def send(self, request, **kwargs):
        self.calls.append(request)
        response = requests.Response()
        response.request = request
        response.url = request.url
        response.status_code = 200
        response._content = json.dumps({"result": {
            "kb_id": "00000000-0000-0000-0000-000000000001",
            "kb_name": "sample", "file_ids": [],
        }}).encode()
        response._content_consumed = True
        if len(self.calls) <= len(self.locations):
            response.status_code = self.status
            response.headers["Location"] = self.locations[len(self.calls) - 1]
        return response

    def close(self):
        pass


def mounted(session, adapter):
    session.trust_env = False
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def client_with(adapter, client_type=APIKeyAuth, **kwargs):
    client = client_type(
        fi_api_key=KEY_HEADERS["X-Api-Key"],
        fi_secret_key=KEY_HEADERS["X-Secret-Key"],
        fi_base_url=BASE,
        **kwargs,
    )
    mounted(client._session, adapter)
    return client


def send(client, **kwargs):
    return client.request(RequestConfig(
        method=HttpMethod.GET, url=f"{BASE}/start", retry_attempts=1, **kwargs,
    ))


def assert_keys(request):
    for name, value in KEY_HEADERS.items():
        assert request.headers[name] == value


def assert_no_keys(request):
    assert "X-Api-Key" not in request.headers
    assert "X-Secret-Key" not in request.headers


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
@pytest.mark.parametrize("target", OFF_ORIGIN)
def test_origin_changing_redirect_strips_sdk_keys(status, target):
    adapter = RedirectAdapter([target], status=status)
    client = client_with(adapter)
    try:
        assert send(client).status_code == 200
    finally:
        client.close()
    assert len(adapter.calls) == 2
    assert_keys(adapter.calls[0])
    assert_no_keys(adapter.calls[1])


@pytest.mark.parametrize("target", [
    "/api/landed", "landed", "https://PLATFORM.test:443/api/landed",
    "https://platform.test/outside-base-path",
])
def test_same_origin_redirect_preserves_sdk_keys(target):
    adapter = RedirectAdapter([target])
    client = client_with(adapter)
    try:
        assert send(client).status_code == 200
    finally:
        client.close()
    assert len(adapter.calls) == 2
    for request in adapter.calls:
        assert_keys(request)


def test_redirect_chain_does_not_restore_stripped_keys():
    adapter = RedirectAdapter([
        "/api/next", "https://other.test/landing", f"{BASE}/back",
    ])
    client = client_with(adapter)
    try:
        assert send(client).status_code == 200
    finally:
        client.close()
    assert len(adapter.calls) == 4
    assert_keys(adapter.calls[0])
    assert_keys(adapter.calls[1])
    assert_no_keys(adapter.calls[2])
    assert_no_keys(adapter.calls[3])


def test_redirect_strips_case_insensitive_key_names():
    adapter = RedirectAdapter([OFF_ORIGIN[0]])
    client = client_with(adapter)
    try:
        send(client, headers={"x-API-key": "synthetic-api", "x-secret-KEY": "synthetic-secret"})
    finally:
        client.close()
    assert_keys(adapter.calls[0])
    assert_no_keys(adapter.calls[1])


def test_extra_header_redirect_policy_still_applies(monkeypatch):
    monkeypatch.setenv("FI_EXTRA_HEADERS", "Proxy-Authorization=Bearer synthetic-proxy;X-Team=sample")
    adapter = RedirectAdapter(["/api/next", "https://other.test/landing"])
    client = client_with(adapter)
    try:
        send(client)
    finally:
        client.close()
    assert len(adapter.calls) == 3
    for request in adapter.calls[:2]:
        assert_keys(request)
        assert request.headers["Proxy-Authorization"] == "Bearer synthetic-proxy"
        assert request.headers["X-Team"] == "sample"
    assert_no_keys(adapter.calls[2])
    assert "Proxy-Authorization" not in adapter.calls[2].headers
    assert "X-Team" not in adapter.calls[2].headers


@pytest.mark.parametrize("method", ["post", "patch"])
@pytest.mark.parametrize("target", OFF_ORIGIN[:4])
def test_direct_upload_does_not_follow_redirects(monkeypatch, method, target):
    adapter = RedirectAdapter([target], status=307)
    session = mounted(requests.Session(), adapter)
    monkeypatch.setattr(requests.sessions, "Session", lambda: session)
    client = client_with(RedirectAdapter([]))
    try:
        kwargs = client._direct_kwargs({
            "url": f"{BASE}/upload", "headers": dict(KEY_HEADERS),
            "files": {"file": ("sample.txt", b"synthetic content")},
            "allow_redirects": True,
        })
        response = getattr(requests, method)(**kwargs)
    finally:
        client.close()
        session.close()
    assert len(adapter.calls) == 1
    assert response.status_code == 307
    assert_keys(adapter.calls[0])


@pytest.mark.parametrize("header", ["x-API-key", "x-secret-KEY"])
def test_direct_upload_guard_recognizes_either_key_header(header):
    client = client_with(RedirectAdapter([]))
    try:
        kwargs = client._direct_kwargs({
            "url": f"{BASE}/upload", "headers": {header: "synthetic-value"},
        })
    finally:
        client.close()
    assert kwargs["allow_redirects"] is False


@pytest.mark.parametrize("operation", ["create", "update"])
def test_knowledge_base_upload_uses_redirect_guard(monkeypatch, tmp_path, operation):
    adapter = RedirectAdapter(["https://other.test/api/model-hub/knowledge-base/"], status=307)
    session = mounted(requests.Session(), adapter)
    monkeypatch.setattr(requests.sessions, "Session", lambda: session)
    client = client_with(RedirectAdapter([]), client_type=KnowledgeBase)
    path = tmp_path / "sample.txt"
    path.write_text("synthetic content")
    try:
        if operation == "create":
            client.create_kb("sample", file_paths=[str(path)])
        else:
            client.kb = KnowledgeBaseConfig(
                id="00000000-0000-0000-0000-000000000001", name="sample", files=[],
            )
            client.update_kb("sample", file_paths=[str(path)])
    finally:
        client.close()
        session.close()
    assert len(adapter.calls) == 1
    assert_keys(adapter.calls[0])
    assert b"synthetic content" in adapter.calls[0].body


class EmptyRedirectAdapter(RedirectAdapter):
    """Redirects need not have JSON bodies, even for JSON upload endpoints."""

    def send(self, request, **kwargs):
        response = super().send(request, **kwargs)
        if response.is_redirect:
            response._content = b""
        return response


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
@pytest.mark.parametrize("method", ["post", "patch"])
def test_direct_same_origin_preserves_requests_semantics(monkeypatch, status, method):
    adapter = EmptyRedirectAdapter(["/api/upload-canonical"], status=status)
    session = mounted(requests.Session(), adapter)
    monkeypatch.setattr(requests.sessions, "Session", lambda: session)
    client = client_with(RedirectAdapter([]))
    try:
        response = getattr(requests, method)(**client._direct_kwargs({
            "url": f"{BASE}/upload", "headers": dict(KEY_HEADERS),
            "files": {"file": ("sample.txt", b"synthetic content")},
        }))
    finally:
        client.close()
        session.close()
    assert response.status_code == 200
    assert len(adapter.calls) == 2
    assert_keys(adapter.calls[1])
    expected_method = "GET" if status in (302, 303) or (status == 301 and method == "post") else method.upper()
    assert adapter.calls[1].method == expected_method
    assert [item.status_code for item in response.history] == [status]
    if status in (307, 308):
        assert adapter.calls[1].body == adapter.calls[0].body
        assert b"synthetic content" in adapter.calls[1].body
        assert adapter.calls[1].headers["Content-Type"] == adapter.calls[0].headers["Content-Type"]
    else:
        assert adapter.calls[1].body is None
        assert "Content-Type" not in adapter.calls[1].headers
        assert "Content-Length" not in adapter.calls[1].headers


@pytest.mark.parametrize("status", [307, 308])
@pytest.mark.parametrize("operation", ["create", "update"])
def test_knowledge_base_same_origin_upload(monkeypatch, tmp_path, status, operation):
    adapter = EmptyRedirectAdapter(["/api/canonical/model-hub/knowledge-base/"], status=status)
    session = mounted(requests.Session(), adapter)
    monkeypatch.setattr(requests.sessions, "Session", lambda: session)
    client = client_with(RedirectAdapter([]), client_type=KnowledgeBase)
    path = tmp_path / "sample.txt"
    path.write_text("synthetic content")
    try:
        if operation == "create":
            result = client.create_kb("sample", file_paths=[str(path)])
        else:
            client.kb = KnowledgeBaseConfig(
                id="00000000-0000-0000-0000-000000000001", name="sample", files=[],
            )
            result = client.update_kb("sample", file_paths=[str(path)])
        assert result is client
        assert client.kb.name == "sample"
    finally:
        client.close()
        session.close()
    assert len(adapter.calls) == 2
    assert adapter.calls[1].method == ("POST" if operation == "create" else "PATCH")
    assert adapter.calls[1].body == adapter.calls[0].body
    assert b"synthetic content" in adapter.calls[1].body
    assert_keys(adapter.calls[1])


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
@pytest.mark.parametrize("target", OFF_ORIGIN)
@pytest.mark.parametrize("method", ["post", "patch"])
def test_direct_cross_origin_never_sends_auth(monkeypatch, status, target, method):
    adapter = EmptyRedirectAdapter([target], status=status)
    session = mounted(requests.Session(), adapter)
    monkeypatch.setattr(requests.sessions, "Session", lambda: session)
    client = client_with(RedirectAdapter([]))
    try:
        response = getattr(requests, method)(**client._direct_kwargs({
            "url": f"{BASE}/upload",
            "headers": {**KEY_HEADERS, "Authorization": "Bearer synthetic-auth"},
            "json": {"name": "sample"},
        }))
    finally:
        client.close()
        session.close()
    assert len(adapter.calls) == 1
    assert response.status_code == status
    assert_keys(adapter.calls[0])


@pytest.mark.parametrize("target", OFF_ORIGIN)
def test_direct_chain_stops_before_origin_change(monkeypatch, target):
    adapter = EmptyRedirectAdapter(["/api/canonical", target], status=307)
    session_type = requests.sessions.Session
    sessions = []

    def new_session():
        session = mounted(session_type(), adapter)
        sessions.append(session)
        return session

    monkeypatch.setattr(requests.sessions, "Session", new_session)
    client = client_with(RedirectAdapter([]))
    try:
        response = requests.post(**client._direct_kwargs({
            "url": f"{BASE}/upload", "headers": dict(KEY_HEADERS), "json": {"name": "sample"},
        }))
    finally:
        client.close()
        for session in sessions:
            session.close()
    assert len(adapter.calls) == 2
    assert response.status_code == 307
    assert response.headers["Location"] == target
    assert [request.url for request in adapter.calls] == [f"{BASE}/upload", f"{BASE}/canonical"]
    assert adapter.calls[1].body == adapter.calls[0].body
    assert_keys(adapter.calls[1])


@pytest.mark.parametrize("target", ["next", "/api/next", "https://PLATFORM.test:443/api/next", "/outside-base-path"])
def test_direct_extra_headers_and_response_hooks(monkeypatch, target):
    monkeypatch.setenv("FI_EXTRA_HEADERS", "Proxy-Authorization=Bearer synthetic-proxy;X-Team=sample")
    adapter = EmptyRedirectAdapter([target], status=308)
    session = mounted(requests.Session(), adapter)
    monkeypatch.setattr(requests.sessions, "Session", lambda: session)
    client = client_with(RedirectAdapter([]))
    seen = []
    try:
        response = requests.patch(**client._direct_kwargs({
            "url": f"{BASE}/upload", "headers": dict(KEY_HEADERS),
            "hooks": {"response": lambda response, **kwargs: seen.append(response.status_code)},
        }))
    finally:
        client.close()
        session.close()
    assert response.status_code == 200
    assert seen == [308, 200]
    assert len(adapter.calls) == 2
    assert_keys(adapter.calls[1])
    if target == "/outside-base-path":
        assert "Proxy-Authorization" not in adapter.calls[1].headers
        assert "X-Team" not in adapter.calls[1].headers
    else:
        assert adapter.calls[1].headers["Proxy-Authorization"] == "Bearer synthetic-proxy"
        assert adapter.calls[1].headers["X-Team"] == "sample"


def test_direct_explicit_no_redirects_is_respected(monkeypatch):
    adapter = EmptyRedirectAdapter(["/api/canonical"], status=307)
    session = mounted(requests.Session(), adapter)
    monkeypatch.setattr(requests.sessions, "Session", lambda: session)
    client = client_with(RedirectAdapter([]))
    try:
        response = requests.post(**client._direct_kwargs({
            "url": f"{BASE}/upload", "headers": dict(KEY_HEADERS), "allow_redirects": False,
        }))
    finally:
        client.close()
        session.close()
    assert response.status_code == 307
    assert len(adapter.calls) == 1


def test_direct_redirect_limit_is_preserved(monkeypatch):
    adapter = EmptyRedirectAdapter(["/api/loop"] * 40, status=307)
    session = mounted(requests.Session(), adapter)
    monkeypatch.setattr(requests.sessions, "Session", lambda: session)
    client = client_with(RedirectAdapter([]))
    try:
        with pytest.raises(requests.TooManyRedirects):
            requests.post(**client._direct_kwargs({
                "url": f"{BASE}/upload", "headers": dict(KEY_HEADERS),
            }))
    finally:
        client.close()
        session.close()
    assert len(adapter.calls) == 31


@pytest.mark.parametrize("target", OFF_ORIGIN)
def test_session_off_origin_strips_all_auth_headers(monkeypatch, target):
    monkeypatch.setenv("FI_EXTRA_HEADERS", "Proxy-Authorization=Bearer synthetic-proxy")
    adapter = RedirectAdapter([target])
    client = client_with(adapter)
    try:
        assert send(client, headers={"Authorization": "Bearer synthetic-auth"}).status_code == 200
    finally:
        client.close()
    assert_no_keys(adapter.calls[1])
    assert "Authorization" not in adapter.calls[1].headers
    assert "Proxy-Authorization" not in adapter.calls[1].headers


@pytest.mark.parametrize("direct", [False, True])
def test_http_upgrade_does_not_forward_authorization(monkeypatch, direct):
    adapter = EmptyRedirectAdapter(["https://platform.test/api/next"])
    client = APIKeyAuth(
        fi_api_key=KEY_HEADERS["X-Api-Key"], fi_secret_key=KEY_HEADERS["X-Secret-Key"],
        fi_base_url="http://platform.test/api",
    )
    mounted(client._session, adapter)
    session = mounted(requests.Session(), adapter)
    monkeypatch.setattr(requests.sessions, "Session", lambda: session)
    try:
        if direct:
            response = requests.post(**client._direct_kwargs({
                "url": "http://platform.test/api/start", "headers": {"Authorization": "Bearer synthetic-auth"},
            }))
            assert response.status_code == 302
            assert len(adapter.calls) == 1
        else:
            response = client.request(RequestConfig(
                method=HttpMethod.GET, url="http://platform.test/api/start", retry_attempts=1,
                headers={"Authorization": "Bearer synthetic-auth"},
            ))
            assert response.status_code == 200
            assert len(adapter.calls) == 2
            assert_no_keys(adapter.calls[1])
            assert "Authorization" not in adapter.calls[1].headers
    finally:
        client.close()
        session.close()
