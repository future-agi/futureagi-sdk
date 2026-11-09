"""Offline interleavings keep prompt cache identity tied to outgoing headers."""

from concurrent.futures import ThreadPoolExecutor
import threading

import pytest
from requests import HTTPError

from fi.api.auth import APIKeyAuth
from fi.prompt.client import Prompt, PromptResponseHandler
from test_prompt_identity_and_fidelity import AUTH, NAME, backend, snapshot


@pytest.mark.parametrize("stale", [False, True])
@pytest.mark.parametrize("selector", [{"version": "v1"}, {"label": "staging"}, {}, {"fallback": True}])
@pytest.mark.parametrize("header", ["X-Workspace-Id", "X-Region"])
def test_header_added_while_fetch_waits_for_cache_lock(backend, monkeypatch, stale, selector, header):
    arrived = threading.Event()
    original_get = backend.cache.get

    def observed_get(key):
        arrived.set()
        return original_get(key)

    monkeypatch.setattr(backend.cache, "get", observed_get)
    if selector.get("fallback"):
        backend.replies.append((404, {}))
        selector = {}
    backend.replies.append((200, {"result": snapshot("Workspace B published")}))
    with ThreadPoolExecutor(max_workers=1) as workers:
        with backend.cache._lock:
            pending = workers.submit(backend.fetch, **selector)
            assert arrived.wait(5), "Fetch did not reach the real cache lock"
            monkeypatch.setenv("FI_EXTRA_HEADERS", f"{header}=synthetic-workspace-b")
        first = pending.result(timeout=5)
    assert first.compile() == [{"role": "user", "content": "Workspace B published"}]
    assert backend.calls[-1]["headers"][header] == "synthetic-workspace-b"

    calls_after_fetch = len(backend.calls)
    keys = repr(list(backend.cache._store))
    assert all(value not in keys for value in (
        AUTH["fi_api_key"], AUTH["fi_secret_key"], "synthetic-workspace-b",
    ))

    # No request is active now; the next call uses the default workspace only.
    monkeypatch.delenv("FI_EXTRA_HEADERS")
    if stale:
        for item in backend.cache._store.values():
            item.expiry = 0
        backend.replies.append((503, {"message": "Synthetic unavailable"}))
        with pytest.raises(HTTPError):
            backend.fetch(**selector)
    else:
        backend.replies.append((200, {"result": snapshot("Default workspace published")}))
        found = backend.fetch(**selector)
        assert found.compile() == [{"role": "user", "content": "Default workspace published"}]
    assert len(backend.calls) == calls_after_fetch + 1
    if not stale:
        # The response remains a fresh cache hit for the identity sent on its request.
        monkeypatch.setenv("FI_EXTRA_HEADERS", f"{header}=synthetic-workspace-b")
        assert backend.fetch(**selector).compile() == first.compile()
        assert len(backend.calls) == calls_after_fetch + 1


def pause_request(monkeypatch, method):
    """Pause after the caller chose a cache scope, but before header merging."""
    arrived, resume = threading.Event(), threading.Event()
    original_request = APIKeyAuth.request

    def request(client, config, response_handler=None):
        if config.method.value == method and not arrived.is_set():
            arrived.set()
            assert resume.wait(5), "Request was not released"
        return original_request(client, config, response_handler)

    monkeypatch.setattr(APIKeyAuth, "request", request)
    return arrived, resume


@pytest.mark.parametrize("by_name", [False, True])
@pytest.mark.parametrize("pause_method", ["GET", "DELETE"])
def test_delete_invalidates_the_identity_sent_on_the_delete(backend, monkeypatch, by_name, pause_method):
    backend.replies.append((200, {"result": snapshot("Default workspace published")}))
    default_client = backend.fetch(version="v1")
    monkeypatch.setenv("FI_EXTRA_HEADERS", "X-Workspace-Id=synthetic-workspace-b")
    backend.replies.append((200, {"result": snapshot("Workspace B published")}))
    backend.fetch(version="v1")
    monkeypatch.delenv("FI_EXTRA_HEADERS")

    if by_name:
        backend.replies.append((200, {"result": snapshot()}))
    backend.replies.append((204, None))
    arrived, resume = pause_request(monkeypatch, pause_method if by_name else "DELETE")
    with ThreadPoolExecutor(max_workers=1) as workers:
        pending = (workers.submit(Prompt.delete_template_by_name, NAME, **AUTH) if by_name
                   else workers.submit(default_client.delete))
        try:
            assert arrived.wait(5), "Delete did not reach the request boundary"
            monkeypatch.setenv("FI_EXTRA_HEADERS", "X-Workspace-Id=synthetic-workspace-b")
        finally:
            resume.set()
        assert pending.result(timeout=5) is True
    assert backend.calls[-1]["method"] == "DELETE"
    assert backend.calls[-1]["headers"]["X-Workspace-Id"] == "synthetic-workspace-b"

    calls_after_delete = len(backend.calls)
    monkeypatch.delenv("FI_EXTRA_HEADERS")
    assert backend.fetch(version="v1").compile() == [
        {"role": "user", "content": "Default workspace published"},
    ]
    assert len(backend.calls) == calls_after_delete
    monkeypatch.setenv("FI_EXTRA_HEADERS", "X-Workspace-Id=synthetic-workspace-b")
    backend.replies.append((503, {"message": "Synthetic unavailable"}))
    with pytest.raises(HTTPError):
        backend.fetch(version="v1")
    assert len(backend.calls) == calls_after_delete + 1


@pytest.mark.parametrize("cached_workspace_b", [False, True])
def test_failed_request_uses_only_the_sent_identity_for_stale_fallback(backend, monkeypatch, cached_workspace_b):
    backend.cache._ttl_sec = -1
    backend.replies.append((200, {"result": snapshot("Default workspace stale")}))
    backend.fetch(version="v1")
    if cached_workspace_b:
        monkeypatch.setenv("FI_EXTRA_HEADERS", "X-Workspace-Id=synthetic-workspace-b")
        backend.replies.append((200, {"result": snapshot("Workspace B stale")}))
        backend.fetch(version="v1")
        monkeypatch.delenv("FI_EXTRA_HEADERS")

    arrived, resume = pause_request(monkeypatch, "GET")
    backend.replies.append((503, {"message": "Synthetic unavailable"}))
    with ThreadPoolExecutor(max_workers=1) as workers:
        pending = workers.submit(backend.fetch, version="v1")
        try:
            assert arrived.wait(5), "Fetch did not reach the request boundary"
            monkeypatch.setenv("FI_EXTRA_HEADERS", "X-Workspace-Id=synthetic-workspace-b")
        finally:
            resume.set()
        if cached_workspace_b:
            assert pending.result(timeout=5).compile() == [
                {"role": "user", "content": "Workspace B stale"},
            ]
        else:
            with pytest.raises(HTTPError):
                pending.result(timeout=5)
    assert backend.calls[-1]["headers"]["X-Workspace-Id"] == "synthetic-workspace-b"


def test_response_completion_does_not_reread_the_environment_for_scope(backend, monkeypatch):
    monkeypatch.setenv("FI_EXTRA_HEADERS", "X-Workspace-Id=synthetic-workspace-b")
    original_parse = PromptResponseHandler._parse_success

    def parse(cls, response):
        assert response.request.headers["X-Workspace-Id"] == "synthetic-workspace-b"
        monkeypatch.delenv("FI_EXTRA_HEADERS")
        return original_parse(response)

    monkeypatch.setattr(PromptResponseHandler, "_parse_success", classmethod(parse))
    backend.replies.append((200, {"result": snapshot("Workspace B published")}))
    backend.fetch(version="v1")
    monkeypatch.setenv("FI_EXTRA_HEADERS", "X-Workspace-Id=synthetic-workspace-b")
    assert backend.fetch(version="v1").compile() == [
        {"role": "user", "content": "Workspace B published"},
    ]
    assert len(backend.calls) == 1
