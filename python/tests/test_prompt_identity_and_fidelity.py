"""Offline regressions for prompt identity, snapshots, and payload fidelity."""

import copy
import json
from collections import deque
from concurrent.futures import Future
from types import SimpleNamespace

import pytest
from requests import HTTPError, Request, Response
from requests_futures.sessions import FuturesSession

from fi.prompt.cache import PromptCache
from fi.prompt.client import Prompt
from fi.prompt.types import MessageBase, ModelConfig, PromptTemplate


BASE_URL = "https://prompts.example.test"
AUTH = dict(fi_api_key="synthetic-key", fi_secret_key="synthetic-secret", fi_base_url=BASE_URL)
TEMPLATE_ID = "00000000-0000-0000-0000-000000000001"
NAME = "shared-prompt"


def snapshot(text="Published prompt"):
    return {
        "id": TEMPLATE_ID, "name": NAME, "version": "v1",
        "prompt_config": [{"configuration": {"model": "test-model"},
                           "messages": [{"role": "user", "content": text}]}],
    }


@pytest.fixture
def backend(monkeypatch):
    calls, replies, clients = [], deque(), []
    cache = PromptCache(max_workers=0)
    monkeypatch.setattr("fi.prompt.client.prompt_cache", cache)
    monkeypatch.delenv("FI_EXTRA_HEADERS", raising=False)

    def request(session, **kwargs):
        calls.append(copy.deepcopy(kwargs))
        assert replies, "Unexpected HTTP request"
        status, payload = replies.popleft()
        response = Response()
        response.status_code = status
        response._content = b"" if payload is None else json.dumps(payload).encode()
        response.request = Request(kwargs["method"], kwargs["url"], params=kwargs["params"]).prepare()
        response.url = response.request.url
        future = Future()
        future.set_result(response)
        return future

    def fetch(**kwargs):
        client = Prompt.get_template_by_name(NAME, **{**AUTH, **kwargs})
        clients.append(client)
        return client

    monkeypatch.setattr(FuturesSession, "request", request)
    yield SimpleNamespace(calls=calls, replies=replies, cache=cache, fetch=fetch, clients=clients)
    for client in clients:
        client.close()


@pytest.mark.parametrize("selector", [{"version": "v1"}, {"label": "production"}, {}])
@pytest.mark.parametrize("changed", [
    {"fi_base_url": "https://another.example.test"},
    {"fi_api_key": "synthetic-other-key"},
    {"fi_secret_key": "synthetic-other-secret"},
])
def test_cache_identity_isolates_fresh_entries(backend, selector, changed):
    backend.replies.extend([(200, {"result": snapshot("Account A")}),
                            (200, {"result": snapshot("Account B")})])
    first = backend.fetch(**selector)
    second = backend.fetch(**selector, **changed)
    assert first.compile() == [{"role": "user", "content": "Account A"}]
    assert second.compile() == [{"role": "user", "content": "Account B"}]
    assert len(backend.calls) == 2


@pytest.mark.parametrize("changed", [
    {"fi_base_url": "https://another.example.test"},
    {"fi_api_key": "synthetic-other-key"},
    {"fi_secret_key": "synthetic-other-secret"},
])
def test_cache_identity_isolates_stale_fallback(backend, changed):
    backend.cache._ttl_sec = -1
    backend.replies.extend([(200, {"result": snapshot("Account A")}),
                            (503, {"message": "Temporarily unavailable"})])
    backend.fetch(version="v1")
    with pytest.raises(HTTPError):
        backend.fetch(version="v1", **changed)
    assert len(backend.calls) == 2


def test_cache_identity_uses_effective_environment_credentials(backend, monkeypatch):
    monkeypatch.setenv("FI_API_KEY", "synthetic-environment-key-a")
    monkeypatch.setenv("FI_SECRET_KEY", "synthetic-environment-secret-a")
    backend.replies.extend([(200, {"result": snapshot("Account A")}),
                            (200, {"result": snapshot("Account B")})])
    backend.fetch(version="v1", fi_api_key=None, fi_secret_key=None)
    monkeypatch.setenv("FI_API_KEY", "synthetic-environment-key-b")
    monkeypatch.setenv("FI_SECRET_KEY", "synthetic-environment-secret-b")
    second = backend.fetch(version="v1", fi_api_key=None, fi_secret_key=None)
    assert second.compile() == [{"role": "user", "content": "Account B"}]
    assert len(backend.calls) == 2


def test_cache_identity_uses_effective_workspace_header(backend, monkeypatch):
    monkeypatch.setenv("FI_EXTRA_HEADERS", "X-Workspace-Id=synthetic-workspace-a")
    backend.replies.extend([(200, {"result": snapshot("Workspace A")}),
                            (200, {"result": snapshot("Workspace B")})])
    backend.fetch(version="v1")
    monkeypatch.setenv("FI_EXTRA_HEADERS", "X-Workspace-Id=synthetic-workspace-b")
    second = backend.fetch(version="v1")
    assert second.compile() == [{"role": "user", "content": "Workspace B"}]
    assert len(backend.calls) == 2


def test_cache_identity_keeps_same_identity_cache_hits(backend):
    backend.replies.append((200, {"result": snapshot()}))
    first = backend.fetch(version="v1")
    second = backend.fetch(version="v1")
    assert first.compile() == second.compile()
    assert len(backend.calls) == 1


@pytest.mark.parametrize("edit_cached_hit", [False, True])
@pytest.mark.parametrize("stale", [False, True])
def test_snapshot_isolated_from_unsaved_edits(backend, edit_cached_hit, stale):
    backend.replies.append((200, {"result": snapshot()}))
    first = backend.fetch(version="v1")
    if edit_cached_hit:
        first = backend.fetch(version="v1")
    first.template.messages[0]["content"] = "Unpublished edit"
    first.template.metadata["nested"] = {"draft": True}
    if stale:
        for item in backend.cache._store.values():
            item.expiry = 0
        backend.replies.append((503, {"message": "Temporarily unavailable"}))
    again = backend.fetch(version="v1")
    assert again.compile() == [{"role": "user", "content": "Published prompt"}]
    assert again.template.metadata == {}
    assert again.template is not first.template
    assert len(backend.calls) == (2 if stale else 1)


def test_snapshot_version_stays_published_after_new_draft(backend):
    backend.replies.extend([
        (200, {"result": snapshot()}),
        (200, {"results": [{"template_version": "v1", "is_draft": False}]}),
        (201, {"result": [{"template_version": "v2"}]}),
    ])
    first = backend.fetch(version="v1")
    assert first.create_new_version() is first
    assert first.template.version == "v2"
    original = backend.fetch(version="v1")
    assert original.template.version == "v1"
    assert len(backend.calls) == 3
