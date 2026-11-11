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


@pytest.mark.parametrize("by_name", [False, True])
@pytest.mark.parametrize("identity", ["origin", "api_key", "secret_key", "workspace"])
def test_cache_identity_delete_preserves_other_identity(backend, monkeypatch, by_name, identity):
    changed = {
        "origin": {"fi_base_url": "https://another.example.test"},
        "api_key": {"fi_api_key": "synthetic-other-key"},
        "secret_key": {"fi_secret_key": "synthetic-other-secret"},
        "workspace": {},
    }[identity]
    if identity == "workspace":
        monkeypatch.setenv("FI_EXTRA_HEADERS", "X-Workspace-Id=synthetic-workspace-b")
    backend.replies.append((200, {"result": snapshot("Account B")}))
    backend.fetch(version="v1", **changed)
    if identity == "workspace":
        monkeypatch.setenv("FI_EXTRA_HEADERS", "X-Workspace-Id=synthetic-workspace-a")
    if by_name:
        backend.replies.append((200, {"result": snapshot("Account A")}))
    backend.replies.append((204, None))
    if by_name:
        assert Prompt.delete_template_by_name(NAME, **AUTH) is True
    else:
        client = Prompt(template=PromptTemplate(id=TEMPLATE_ID, name=NAME), **AUTH)
        backend.clients.append(client)
        assert client.delete() is True
    calls_before_lookup = len(backend.calls)
    if identity == "workspace":
        monkeypatch.setenv("FI_EXTRA_HEADERS", "X-Workspace-Id=synthetic-workspace-b")
    backend.replies.append((503, {"message": "Temporarily unavailable"}))
    found = backend.fetch(version="v1", **changed)
    assert found.compile() == [{"role": "user", "content": "Account B"}]
    assert len(backend.calls) == calls_before_lookup


@pytest.mark.parametrize("by_name", [False, True])
@pytest.mark.parametrize("stale", [False, True])
def test_cache_identity_delete_evicts_own_selectors(backend, by_name, stale):
    selectors = [{"version": "v1"}, {"label": "production"}, {}]
    for selector in selectors:
        backend.replies.append((200, {"result": snapshot()}))
        backend.fetch(**selector)
    if stale:
        for item in backend.cache._store.values():
            item.expiry = 0
    if by_name:
        backend.replies.append((200, {"result": snapshot()}))
    backend.replies.append((204, None))
    assert (Prompt.delete_template_by_name(NAME, **AUTH) if by_name
            else backend.clients[0].delete()) is True
    for selector in selectors:
        backend.replies.append((503, {"message": "Temporarily unavailable"}))
        with pytest.raises(HTTPError):
            backend.fetch(**selector)


@pytest.mark.parametrize("identity", ["origin", "workspace"])
@pytest.mark.parametrize("stale", [False, True])
def test_cache_identity_resolves_live_environment(backend, monkeypatch, identity, stale):
    setting, first, second, kwargs = (
        ("FI_BASE_URL", BASE_URL, "https://another.example.test", {"fi_base_url": None})
        if identity == "origin" else
        ("FI_EXTRA_HEADERS", "X-Workspace-Id=synthetic-workspace-a",
         "X-Workspace-Id=synthetic-workspace-b", {})
    )
    monkeypatch.setenv(setting, first)
    if stale:
        backend.cache._ttl_sec = -1
    backend.replies.append((200, {"result": snapshot("Account A")}))
    backend.fetch(version="v1", **kwargs)
    monkeypatch.setenv(setting, second)
    if stale:
        backend.replies.append((503, {"message": "Temporarily unavailable"}))
        with pytest.raises(HTTPError):
            backend.fetch(version="v1", **kwargs)
    else:
        backend.replies.append((200, {"result": snapshot("Account B")}))
        assert backend.fetch(version="v1", **kwargs).compile() == [
            {"role": "user", "content": "Account B"},
        ]
    assert len(backend.calls) == 2


@pytest.mark.parametrize("stale", [False, True])
def test_cache_identity_never_uses_unscoped_entries(backend, stale):
    template = PromptTemplate(id=TEMPLATE_ID, name=NAME, messages=[
        MessageBase(role="user", content="Identity-free data"),
    ])
    backend.cache.set(backend.cache.make_key(NAME, version="v1"), template,
                      ttl_sec=-1 if stale else 300)
    backend.replies.append((503, {"message": "Temporarily unavailable"}))
    with pytest.raises(HTTPError):
        backend.fetch(version="v1")
    assert len(backend.calls) == 1


def test_cache_identity_normalizes_headers_and_hides_values(backend, monkeypatch):
    monkeypatch.setenv("FI_EXTRA_HEADERS", "X-Workspace-Id=synthetic-workspace;X-Region=synthetic-region")
    backend.replies.append((200, {"result": snapshot()}))
    first = backend.fetch(version="v1")
    monkeypatch.setenv("FI_EXTRA_HEADERS", "x-region=synthetic-region;x-workspace-id=synthetic-workspace")
    second = backend.fetch(version="v1", fi_base_url=BASE_URL + "/")
    assert first.compile() == second.compile()
    assert len(backend.calls) == 1
    keys = repr(list(backend.cache._store))
    assert all(value not in keys for value in [
        AUTH["fi_api_key"], AUTH["fi_secret_key"], "synthetic-workspace", "synthetic-region",
    ])


@pytest.mark.parametrize("edit_cached_hit", [False, True])
@pytest.mark.parametrize("stale", [False, True])
def test_snapshot_isolated_from_unsaved_edits(backend, edit_cached_hit, stale):
    backend.replies.append((200, {"result": snapshot()}))
    first = backend.fetch(version="v1")
    if edit_cached_hit:
        first = backend.fetch(version="v1")
    first.template.messages[0].content = "Unpublished edit"
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


@pytest.mark.parametrize("operation", ["create", "create_new_version", "save_current_draft"])
def test_write_configuration_preserves_supported_settings(backend, operation):
    config = ModelConfig(
        model_name="test-model", temperature=0, max_tokens=42, top_p=0.5,
        frequency_penalty=0.25, presence_penalty=-0.5,
        response_format={"type": "json_object"}, tool_choice="required",
        tools=[{"type": "function", "function": {
            "name": "lookup", "parameters": {"type": "object", "properties": {}}
        }}],
    )
    template = PromptTemplate(
        id=TEMPLATE_ID, name=NAME, version="v1", model_configuration=config,
        messages=[MessageBase(role="user", content="Hello")],
    )
    client = Prompt(template=template, **AUTH)
    backend.clients.append(client)
    if operation == "create":
        client.template.id = None
        backend.replies.append((201, {"result": {"id": TEMPLATE_ID, "name": NAME,
                                                "template_version": "v1"}}))
    elif operation == "create_new_version":
        backend.replies.extend([
            (200, {"results": [{"template_version": "v1", "is_draft": False}]}),
            (201, {"result": [{"template_version": "v2"}]}),
        ])
    else:
        backend.replies.extend([
            (200, {"results": [{"template_version": "v1", "is_draft": True}]}),
            (200, {"status": True}),
        ])
    getattr(client, operation)()
    write = backend.calls[-1]["json"]
    entry = write["new_prompts"][0] if operation == "create_new_version" else write
    wire_config = entry["prompt_config"][0]["configuration"]
    expected = config.model_dump()
    expected["model"] = expected.pop("model_name")
    assert wire_config == expected

    backend.replies.append((200, {"result": {
        "id": TEMPLATE_ID, "name": NAME, "version": client.template.version,
        "prompt_config": entry["prompt_config"],
    }}))
    fetched = backend.fetch(version=client.template.version)
    assert fetched.template.model_configuration == config


DEFAULT_WIRE_SETTINGS = {
    "model": "test-model", "temperature": 0.7, "max_tokens": 1000, "top_p": 1.0,
    "frequency_penalty": 0, "presence_penalty": 0,
}
LOOKUP_TOOL = {"type": "function", "function": {
    "name": "lookup", "parameters": {"type": "object", "properties": {
        "order_id": {"type": ["string", "null"], "default": None},
    }},
}}


@pytest.mark.parametrize("operation", ["create", "create_new_version", "save_current_draft"])
@pytest.mark.parametrize("settings", [
    {},
    {"tools": [LOOKUP_TOOL]},
    {"tool_choice": "auto"},
    {"response_format": {"type": "json_object"}},
], ids=["none-set", "tools-only", "tool-choice-only", "response-format-only"])
def test_write_configuration_omits_unset_settings(backend, operation, settings):
    config = ModelConfig(model_name="test-model", **copy.deepcopy(settings))
    template = PromptTemplate(
        id=TEMPLATE_ID, name=NAME, version="v1", model_configuration=config,
        messages=[MessageBase(role="user", content="Hello")],
    )
    client = Prompt(template=template, **AUTH)
    backend.clients.append(client)
    if operation == "create":
        client.template.id = None
        backend.replies.append((201, {"result": {"id": TEMPLATE_ID, "name": NAME,
                                                "template_version": "v1"}}))
    elif operation == "create_new_version":
        backend.replies.extend([
            (200, {"results": [{"template_version": "v1", "is_draft": False}]}),
            (201, {"result": [{"template_version": "v2"}]}),
        ])
    else:
        backend.replies.extend([
            (200, {"results": [{"template_version": "v1", "is_draft": True}]}),
            (200, {"status": True}),
        ])
    getattr(client, operation)()
    write = backend.calls[-1]["json"]
    entry = write["new_prompts"][0] if operation == "create_new_version" else write
    wire_config = entry["prompt_config"][0]["configuration"]
    # Set settings are sent as given (nested values included); unset ones are left out, not sent as null.
    assert wire_config == {**DEFAULT_WIRE_SETTINGS, **settings}
    unset = {"response_format", "tool_choice", "tools"} - set(settings)
    assert not (unset & set(wire_config))
    assert None not in wire_config.values()

    backend.replies.append((200, {"result": {
        "id": TEMPLATE_ID, "name": NAME, "version": client.template.version,
        "prompt_config": entry["prompt_config"],
    }}))
    fetched = backend.fetch(version=client.template.version)
    assert fetched.template.model_configuration == config


@pytest.mark.parametrize("as_model", [False, True])
def test_compile_fidelity_preserves_multimodal_content(backend, as_model):
    content = [
        {"type": "text", "text": "Hello {{ name }}; {{missing}}"},
        {"type": "image_url", "image_url": {"url": "https://images.example.test/{{image}}.png"}},
    ]
    message = MessageBase(role="user", content=content) if as_model else {"role": "user", "content": content}
    client = Prompt(template=PromptTemplate(id=TEMPLATE_ID, name=NAME, messages=[message]), **AUTH)
    backend.clients.append(client)
    before = client.template.model_dump()
    compiled = client.compile(name="reader", image="sample")
    assert compiled == [{"role": "user", "content": [
        {"type": "text", "text": "Hello reader; {{missing}}"},
        {"type": "image_url", "image_url": {"url": "https://images.example.test/sample.png"}},
    ]}]
    compiled[0]["content"][1]["image_url"]["url"] = "local edit"
    assert client.template.model_dump() == before


def test_compile_fidelity_preserves_tool_message_metadata(backend):
    messages = [
        {"role": "assistant", "content": None, "tool_calls": [
            {"id": "call-1", "type": "function", "function": {"name": "lookup", "arguments": "{}"}}
        ]},
        {"role": "tool", "content": "Result: {{value}}", "tool_call_id": "call-1", "name": "lookup"},
    ]
    client = Prompt(template=PromptTemplate(id=TEMPLATE_ID, name=NAME, messages=messages), **AUTH)
    backend.clients.append(client)
    compiled = client.compile(value="found")
    expected = copy.deepcopy(messages)
    expected[1]["content"] = "Result: found"
    assert compiled == expected
    compiled[0]["tool_calls"][0]["function"]["name"] = "local edit"
    assert client.compile(value="found") == expected


def test_compile_fidelity_preserves_placeholder_messages_and_inputs(backend):
    client = Prompt(template=PromptTemplate(id=TEMPLATE_ID, name=NAME, messages=[
        {"type": "placeholder", "name": "history"},
    ]), **AUTH)
    backend.clients.append(client)
    history = [{"role": "tool", "content": [{"type": "text", "text": "{{value}}"}],
                "tool_call_id": "call-1"}]
    before = copy.deepcopy(history)
    compiled = client.compile(history=history, value="found")
    assert compiled == [{"role": "tool", "content": [{"type": "text", "text": "found"}],
                         "tool_call_id": "call-1"}]
    compiled[0]["content"][0]["text"] = "local edit"
    assert history == before
    unresolved = client.compile()
    unresolved[0]["name"] = "local edit"
    assert client.compile() == [{"type": "placeholder", "name": "history"}]


def test_compile_fidelity_survives_text_write_and_fetch(backend):
    client = Prompt(template=PromptTemplate(id=TEMPLATE_ID, name=NAME, messages=[
        MessageBase(role="user", content="Hello {{name}}"),
    ]), **AUTH)
    backend.clients.append(client)
    client.template.id = None
    backend.replies.append((201, {"result": {"id": TEMPLATE_ID, "name": NAME, "template_version": "v1"}}))
    client.create()
    stored = backend.calls[-1]["json"]["prompt_config"]
    backend.replies.append((200, {"result": {"id": TEMPLATE_ID, "name": NAME,
                                            "version": "v1", "prompt_config": stored}}))
    fetched = backend.fetch(version="v1")
    assert fetched.compile(name="reader") == [
        {"role": "system", "content": [{"type": "text", "text": ""}]},
        {"role": "user", "content": [{"type": "text", "text": "Hello reader"}]},
    ]


def test_compile_fidelity_keeps_string_messages_and_validates_placeholders(backend):
    from fi.prompt.types import UserMessage

    client = Prompt(template=PromptTemplate(id=TEMPLATE_ID, name=NAME, messages=[
        UserMessage(content="Hello {{ name }}; {{missing}}"),
        {"type": "placeholder", "name": "history"},
    ]), **AUTH)
    backend.clients.append(client)
    assert client.compile(name="reader", history=[]) == [
        {"role": "user", "content": "Hello reader; {{missing}}"},
    ]
    with pytest.raises(ValueError, match="role.*content"):
        client.compile(history=[{"role": "user"}])
