"""Real requests redirects with an offline adapter and precise cache assertions."""

import json

import pytest
from requests import ConnectionError, HTTPError, Response
from requests.adapters import HTTPAdapter
from requests_futures.sessions import FuturesSession

from fi.prompt.client import Prompt, PromptResponseHandler
from test_prompt_identity_and_fidelity import AUTH, NAME, backend, snapshot

_REAL_FUTURES_REQUEST = FuturesSession.request


def redirect_transport(monkeypatch, replies, header="X-Workspace-Id"):
    calls = []

    def send(adapter, request, **kwargs):
        calls.append({"method": request.method, "url": request.url,
                      "headers": dict(request.headers)})
        assert replies, "Unexpected offline adapter request"
        kind, payload = replies.pop(0)
        if kind == "connection-error":
            raise ConnectionError("Synthetic transport failure", request=request)
        response = Response()
        response.request = request
        response.url = request.url
        if kind == "redirect":
            assert header not in request.headers
            monkeypatch.setenv("FI_EXTRA_HEADERS", f"{header}=synthetic-workspace-b")
            response.status_code = 307
            response.headers["Location"] = request.url + ("&" if "?" in request.url else "?") + "redirected=1"
            response._content = b""
        else:
            response.status_code = kind
            response._content = b"" if payload is None else json.dumps(payload).encode()
        return response

    # Keep real preparation, futures, redirects, and the SDK's rebuild_auth;
    # replace only the adapter boundary so no sockets are opened.
    monkeypatch.setattr(FuturesSession, "request", _REAL_FUTURES_REQUEST)
    monkeypatch.setattr(HTTPAdapter, "send", send)
    return calls


@pytest.mark.parametrize("stale", [False, True])
@pytest.mark.parametrize("selector", [{"version": "v1"}, {"label": "staging"}, {}, {"fallback": True}])
@pytest.mark.parametrize("header", ["X-Workspace-Id", "X-Region"])
def test_redirected_fetch_scopes_by_response_request_headers(backend, monkeypatch, stale, selector, header):
    replies = [(404, {})] if selector.get("fallback") else []
    if selector.get("fallback"):
        selector = {}
    replies.extend([("redirect", None), (200, {"result": snapshot("Workspace B published")})])
    calls = redirect_transport(monkeypatch, replies, header)
    first = backend.fetch(**selector)
    assert first.compile() == [{"role": "user", "content": "Workspace B published"}]
    assert header not in calls[-2]["headers"]
    assert calls[-1]["headers"][header] == "synthetic-workspace-b"
    calls_after_fetch = len(calls)
    keys = repr(list(backend.cache._store))
    assert all(value not in keys for value in (*AUTH.values(), "synthetic-workspace-b"))
    monkeypatch.delenv("FI_EXTRA_HEADERS")
    if stale:
        for item in backend.cache._store.values():
            item.expiry = 0
        replies.append((503, {"message": "Synthetic unavailable"}))
        with pytest.raises(HTTPError):
            backend.fetch(**selector)
    else:
        replies.append((200, {"result": snapshot("Default workspace published")}))
        found = backend.fetch(**selector)
        assert found.compile() == [{"role": "user", "content": "Default workspace published"}], calls
    assert len(calls) == calls_after_fetch + 1
    # Redirected responses must also remain reusable under their final identity.
    monkeypatch.setenv("FI_EXTRA_HEADERS", f"{header}=synthetic-workspace-b")
    if stale:
        replies.append((503, {"message": "Synthetic unavailable"}))
    assert backend.fetch(**selector).compile() == first.compile()
    assert len(calls) == calls_after_fetch + 1 + int(stale)


@pytest.mark.parametrize("by_name", [False, True])
def test_redirected_delete_invalidates_final_sent_identity(backend, monkeypatch, by_name):
    backend.replies.append((200, {"result": snapshot("Default workspace published")}))
    default = backend.fetch(version="v1")
    default_key = next(iter(backend.cache._store))
    monkeypatch.setenv("FI_EXTRA_HEADERS", "X-Workspace-Id=synthetic-workspace-b")
    backend.replies.append((200, {"result": snapshot("Workspace B published")}))
    backend.fetch(version="v1")
    workspace_b_key = next(key for key in backend.cache._store if key != default_key)
    monkeypatch.delenv("FI_EXTRA_HEADERS")
    replies = ([(200, {"result": snapshot()})] if by_name else []) + [("redirect", None), (204, None)]
    calls = redirect_transport(monkeypatch, replies)
    assert (Prompt.delete_template_by_name(NAME, **AUTH) if by_name else default.delete()) is True
    assert len(calls) == (3 if by_name else 2)
    assert calls[-1]["method"] == "DELETE"
    assert "X-Workspace-Id" not in calls[-2]["headers"]
    assert calls[-1]["headers"]["X-Workspace-Id"] == "synthetic-workspace-b"
    assert default_key in backend.cache._store, "Workspace-B DELETE wrongly evicted the default workspace"
    assert workspace_b_key not in backend.cache._store, "Deleted workspace-B entry was not invalidated"


@pytest.mark.parametrize("cached_workspace_b", [False, True])
def test_redirected_failure_uses_only_final_identity_stale_data(backend, monkeypatch, cached_workspace_b):
    backend.cache._ttl_sec = -1
    backend.replies.append((200, {"result": snapshot("Default workspace stale")}))
    backend.fetch(version="v1")
    if cached_workspace_b:
        monkeypatch.setenv("FI_EXTRA_HEADERS", "X-Workspace-Id=synthetic-workspace-b")
        backend.replies.append((200, {"result": snapshot("Workspace B stale")}))
        backend.fetch(version="v1")
        monkeypatch.delenv("FI_EXTRA_HEADERS")
    replies = [("redirect", None), (503, {"message": "Synthetic unavailable"})]
    calls = redirect_transport(monkeypatch, replies)
    if cached_workspace_b:
        assert backend.fetch(version="v1").compile() == [
            {"role": "user", "content": "Workspace B stale"},
        ]
    else:
        with pytest.raises(HTTPError):
            backend.fetch(version="v1")
    assert len(calls) == 2
    assert calls[-1]["headers"]["X-Workspace-Id"] == "synthetic-workspace-b"


def test_redirect_scope_does_not_reread_environment_after_response(backend, monkeypatch):
    original_parse = PromptResponseHandler._parse_success

    def parse(cls, response):
        assert response.request.headers["X-Workspace-Id"] == "synthetic-workspace-b"
        monkeypatch.delenv("FI_EXTRA_HEADERS")
        return original_parse(response)

    monkeypatch.setattr(PromptResponseHandler, "_parse_success", classmethod(parse))
    replies = [("redirect", None), (200, {"result": snapshot("Workspace B published")})]
    calls = redirect_transport(monkeypatch, replies)
    first = backend.fetch(version="v1")
    monkeypatch.setenv("FI_EXTRA_HEADERS", "X-Workspace-Id=synthetic-workspace-b")
    assert backend.fetch(version="v1").compile() == first.compile()
    assert len(calls) == 2


def test_redirected_transport_failure_does_not_use_unconfirmed_stale_scope(backend, monkeypatch):
    backend.cache._ttl_sec = -1
    backend.replies.append((200, {"result": snapshot("Default workspace stale")}))
    backend.fetch(version="v1")
    replies = [("redirect", None), ("connection-error", None)] * 3
    calls = redirect_transport(monkeypatch, replies)
    with pytest.raises(ConnectionError, match="Synthetic transport failure"):
        backend.fetch(version="v1")
    assert len(calls) == 6
    assert calls[-1]["headers"]["X-Workspace-Id"] == "synthetic-workspace-b"


@pytest.mark.parametrize("by_name", [False, True])
def test_redirected_failed_delete_preserves_both_identities(backend, monkeypatch, by_name):
    backend.replies.append((200, {"result": snapshot("Default workspace published")}))
    default = backend.fetch(version="v1")
    monkeypatch.setenv("FI_EXTRA_HEADERS", "X-Workspace-Id=synthetic-workspace-b")
    backend.replies.append((200, {"result": snapshot("Workspace B published")}))
    backend.fetch(version="v1")
    keys = set(backend.cache._store)
    monkeypatch.delenv("FI_EXTRA_HEADERS")
    replies = ([(200, {"result": snapshot()})] if by_name else []) + [
        ("redirect", None), (503, {"message": "Synthetic unavailable"}),
    ]
    calls = redirect_transport(monkeypatch, replies)
    with pytest.raises(HTTPError):
        Prompt.delete_template_by_name(NAME, **AUTH) if by_name else default.delete()
    assert set(backend.cache._store) == keys
    assert default.template is not None
    assert len(calls) == (3 if by_name else 2)
    assert calls[-1]["headers"]["X-Workspace-Id"] == "synthetic-workspace-b"


def test_multiple_redirects_use_all_final_identity_headers(backend, monkeypatch):
    calls = []

    def send(adapter, request, **kwargs):
        calls.append(request)
        response = Response()
        response.request = request
        response.url = request.url
        if len(calls) <= 2:
            extra = "X-Workspace-Id=synthetic-workspace-b"
            if len(calls) == 2:
                extra += ";X-Region=synthetic-region"
            monkeypatch.setenv("FI_EXTRA_HEADERS", extra)
            response.status_code = 307
            response.headers["Location"] = request.url + "&redirected=1"
            response._content = b""
        else:
            response.status_code = 200
            response._content = json.dumps({"result": snapshot("Final workspace")}).encode()
        return response

    monkeypatch.setattr(FuturesSession, "request", _REAL_FUTURES_REQUEST)
    monkeypatch.setattr(HTTPAdapter, "send", send)
    first = backend.fetch(version="v1")
    assert len(calls) == 3
    assert "X-Workspace-Id" not in calls[0].headers
    assert "X-Region" not in calls[1].headers
    assert calls[2].headers["X-Region"] == "synthetic-region"
    assert backend.fetch(version="v1").compile() == first.compile()
    assert len(calls) == 3
    keys = repr(list(backend.cache._store))
    assert "synthetic-workspace-b" not in keys
    assert "synthetic-region" not in keys


@pytest.mark.parametrize("status", [302, 307])
def test_redirect_without_header_change_preserves_cache_hits(backend, monkeypatch, status):
    calls = []

    def send(adapter, request, **kwargs):
        calls.append(request)
        response = Response()
        response.request = request
        response.url = request.url
        if len(calls) == 1:
            response.status_code = status
            response.headers["Location"] = request.url + "&redirected=1"
            response._content = b""
        else:
            response.status_code = 200
            response._content = json.dumps({"result": snapshot("Default workspace published")}).encode()
        return response

    monkeypatch.setattr(FuturesSession, "request", _REAL_FUTURES_REQUEST)
    monkeypatch.setattr(HTTPAdapter, "send", send)
    first = backend.fetch(version="v1")
    again = backend.fetch(version="v1")
    assert again.compile() == first.compile() == [{"role": "user", "content": "Default workspace published"}]
    assert len(calls) == 2
