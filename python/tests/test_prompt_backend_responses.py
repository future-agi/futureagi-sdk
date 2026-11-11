"""Offline regressions for backend prompt responses, routing, and deletion."""

import copy
import json
from collections import deque
from concurrent.futures import Future
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import UUID

import pytest
from requests import HTTPError, Request, Response
from requests_futures.sessions import FuturesSession

from fi.prompt.cache import PromptCache
from fi.prompt.client import Prompt, PromptResponseHandler
from fi.prompt.types import MessageBase, PromptTemplate
from fi.utils.errors import SDKException, TemplateAlreadyExists, TemplateNotFound
from fi.utils.routes import Routes


BASE_URL = "https://prompt.example.test"
AUTH = dict(fi_api_key="synthetic-key", fi_secret_key="synthetic-secret", fi_base_url=BASE_URL)
TEMPLATE_ID = "00000000-0000-0000-0000-000000000001"
NAME = "response-regression"
TEMPLATE = {"id": TEMPLATE_ID, "name": NAME, "version": "v2"}


@pytest.fixture(autouse=True)
def transport(monkeypatch):
    """Exercise the real request/response handlers without opening any sockets."""
    calls, replies = [], deque()
    cache = PromptCache(max_workers=0)
    monkeypatch.setattr("fi.prompt.client.prompt_cache", cache)
    monkeypatch.delenv("FI_EXTRA_HEADERS", raising=False)

    def request(session, **kwargs):
        calls.append(kwargs)
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

    monkeypatch.setattr(FuturesSession, "request", request)
    yield SimpleNamespace(calls=calls, replies=replies, cache=cache)


@pytest.fixture
def client():
    template = PromptTemplate(**TEMPLATE, messages=[MessageBase(role="user", content="Original prompt")])
    prompt = Prompt(template=template, **AUTH)
    yield prompt
    prompt.close()


def test_constructor_name_lookup_uses_name_only_route(transport):
    transport.replies.append((200, {"result": TEMPLATE}))
    client = Prompt(template=PromptTemplate(name=NAME), **AUTH)
    try:
        assert str(client.template.id) == TEMPLATE_ID
        assert transport.calls[0]["url"] == BASE_URL + "/" + Routes.get_template_by_name.value
        assert transport.calls[0]["params"] == {"name": NAME}
    finally:
        client.close()


def test_delete_by_name_resolves_name_only_route(transport):
    transport.replies.extend([(200, {"result": TEMPLATE}), (204, None)])
    assert Prompt.delete_template_by_name(NAME, **AUTH) is True
    assert [(c["method"], c["url"]) for c in transport.calls] == [
        ("GET", BASE_URL + "/" + Routes.get_template_by_name.value),
        ("DELETE", BASE_URL + "/" + Routes.delete_template.value.format(template_id=TEMPLATE_ID)),
    ]
    assert transport.calls[0]["params"] == {"name": NAME}


@pytest.mark.parametrize("selector", [{"label": "staging"}, {"version": "v2"}])
def test_explicit_selector_keeps_label_route(transport, selector):
    transport.replies.append((200, {"result": TEMPLATE}))
    prompt = Prompt.get_template_by_name(NAME, **selector, **AUTH)
    try:
        assert prompt.template.version == "v2"
        assert transport.calls[0]["url"] == BASE_URL + "/" + Routes.prompt_label_get_by_name.value
        assert transport.calls[0]["params"] == {"name": NAME, **selector}
    finally:
        prompt.close()


def test_unlabelled_lookup_keeps_production_then_default_fallback(transport):
    transport.replies.extend([(404, {}), (200, {"result": TEMPLATE})])
    prompt = Prompt.get_template_by_name(NAME, **AUTH)
    try:
        assert transport.calls[0]["url"] == BASE_URL + "/" + Routes.prompt_label_get_by_name.value
        assert transport.calls[0]["params"] == {"name": NAME, "label": "production"}
        assert transport.calls[1]["url"] == BASE_URL + "/" + Routes.get_template_by_name.value
        assert transport.calls[1]["params"] == {"name": NAME}
    finally:
        prompt.close()


@pytest.mark.parametrize("operation", ["generate", "improve"])
@pytest.mark.parametrize("empty_messages", [False, True])
@pytest.mark.parametrize("payload,job_id", [
    ({"result": {"generation_id": "job-1"}}, "job-1"),
    ({"generation_id": "job-2"}, "job-2"),
    ({"status": "queued"}, None),
    ({"result": None}, None),
    ([], None),
])
def test_queued_jobs_preserve_messages_and_return_self(client, transport, operation, empty_messages, payload, job_id):
    if empty_messages:
        client.template.messages = []
    before = copy.deepcopy(client.template.messages)
    transport.replies.append((202, payload))
    assert getattr(client, operation)("Be concise") is client
    assert client.last_generation_id == job_id
    assert client.template.messages == before
    call, = transport.calls
    route = Routes.generate_prompt if operation == "generate" else Routes.improve_prompt
    assert call["url"] == BASE_URL + "/" + route.value
    assert call["method"] == "POST"
    assert call["json"] == (
        {"statement": "Be concise"} if operation == "generate" else
        {"existing_prompt": "" if empty_messages else "Original prompt", "improvement_requirements": "Be concise"}
    )


@pytest.mark.parametrize("operation", ["generate", "improve"])
def test_job_id_is_cleared_by_later_acknowledgement_without_id(client, transport, operation):
    transport.replies.extend([(202, {"result": {"generation_id": "first-job"}}), (202, {"result": {}})])
    getattr(client, operation)("first")
    assert client.last_generation_id == "first-job"
    getattr(client, operation)("second")
    assert client.last_generation_id is None


def test_generation_id_initially_unset(client):
    assert client.last_generation_id is None


@pytest.mark.parametrize("operation", ["generate", "improve"])
def test_synchronous_results_still_update_the_prompt(client, transport, operation):
    transport.replies.append((200, {"result": {"prompt": "Revised prompt"}}))
    assert getattr(client, operation)("Be concise") is client
    assert client.template.messages[-1].content == "Revised prompt"


@pytest.mark.parametrize("operation", ["generate", "improve"])
def test_job_requires_template(client, transport, operation):
    client.template = None
    with pytest.raises(ValueError, match="No template configured"):
        getattr(client, operation)("Be concise")
    assert transport.calls == []


@pytest.mark.parametrize("operation", ["generate", "improve"])
def test_rejected_job_does_not_mutate_existing_state(client, transport, operation):
    client._last_generation_id = "prior-job"
    before = copy.deepcopy(client.template)
    transport.replies.append((404, {}))
    with pytest.raises(TemplateNotFound):
        getattr(client, operation)("Be concise")
    assert client.template == before
    assert client._last_generation_id == "prior-job"
    assert len(transport.calls) == 1


@pytest.mark.parametrize("by_name", [False, True])
@pytest.mark.parametrize("ttl", [300, -1], ids=["fresh", "stale"])
def test_successful_delete_evicts_all_cached_selectors(client, transport, by_name, ttl):
    keys = [NAME, transport.cache.make_key(NAME, version="v2"), transport.cache.make_key(NAME, label="production")]
    for key in keys:
        transport.cache.set(key, client.template, ttl_sec=ttl)
    transport.cache.set("another-template", client.template)
    if by_name:
        transport.replies.append((200, {"result": TEMPLATE}))
    transport.replies.append((204, None))
    assert (Prompt.delete_template_by_name(NAME, **AUTH) if by_name else client.delete()) is True
    for key in keys:
        assert transport.cache.get_stale(key) is None
    assert transport.cache.get("another-template") is not None
    if not by_name:
        assert client.template is None
    transport.replies.append((404, {}))
    with pytest.raises(TemplateNotFound):
        Prompt.get_template_by_name(NAME, label="production", **AUTH)
    assert transport.calls[-1]["params"] == {"name": NAME, "label": "production"}


@pytest.mark.parametrize("by_name", [False, True])
def test_delete_failure_preserves_template_and_cache(client, transport, monkeypatch, by_name):
    before = client.template
    transport.cache.set(NAME, before)
    if by_name:
        mock = Mock(side_effect=[before, SDKException("Delete failed")])
        monkeypatch.setattr("fi.prompt.client.APIKeyAuth.request", mock)
    else:
        monkeypatch.setattr(client, "request", Mock(side_effect=SDKException("Delete failed")))
    with pytest.raises(SDKException, match="Delete failed"):
        Prompt.delete_template_by_name(NAME, **AUTH) if by_name else client.delete()
    assert client.template is before
    assert transport.cache.get(NAME) is before


@pytest.mark.parametrize("by_name", [False, True])
def test_cache_failure_does_not_fail_successful_delete(client, transport, monkeypatch, by_name):
    monkeypatch.setattr(transport.cache, "invalidate_template", Mock(side_effect=RuntimeError("Cache unavailable")))
    if by_name:
        transport.replies.append((200, {"result": TEMPLATE}))
    transport.replies.append((204, None))
    assert (Prompt.delete_template_by_name(NAME, **AUTH) if by_name else client.delete()) is True
    transport.cache.invalidate_template.assert_called_once_with(NAME)
    if not by_name:
        assert client.template is None


@pytest.mark.parametrize("code_key", ["code", "error_code"])
def test_duplicate_error_recognizes_backend_and_legacy_code(client, transport, code_key):
    client.template.id = None
    transport.replies.append((400, {code_key: "TEMPLATE_ALREADY_EXIST", "name": NAME}))
    with pytest.raises(TemplateAlreadyExists, match=NAME):
        client.create()
    assert len(transport.calls) == 1


def test_other_error_code_keeps_backend_message(client, transport):
    client.template.id = None
    transport.replies.append((400, {"code": "OTHER_ERROR", "message": "Invalid template"}))
    with pytest.raises(SDKException, match="Invalid template"):
        client.create()


@pytest.mark.parametrize("model_key", ["model", "model_name"])
@pytest.mark.parametrize("as_list", [False, True])
@pytest.mark.parametrize("via_handler", [False, True])
def test_snake_case_template_fields_and_model_aliases(model_key, as_list, via_handler):
    config = {"configuration": {model_key: "test-model", "temperature": 0, "top_p": 0,
                                "frequency_penalty": 0, "presence_penalty": 0},
              "messages": [{"role": "user", "content": "Hello"}]}
    payload = {**TEMPLATE, "is_default": False, "error_message": "Synthetic failure",
               "prompt_config": [config] if as_list else config}
    if via_handler:
        response = Response()
        response.status_code = 200
        response._content = json.dumps({"result": payload}).encode()
        response.request = Request("GET", BASE_URL + "/template/").prepare()
        response.url = response.request.url
        template = PromptResponseHandler.parse(response)
    else:
        template = Prompt._dict_to_prompt_template(payload)
    assert template.version == "v2"
    assert template.is_default is False
    assert template.error_message == "Synthetic failure"
    assert template.model_configuration.model_name == "test-model"
    assert template.model_configuration.temperature == 0
    assert template.model_configuration.top_p == 0


@pytest.mark.parametrize("draft", [False, True])
def test_version_history_reads_snake_case(client, transport, draft):
    history = {"results": [{"template_version": "v2", "is_draft": draft, "version_id": "version-2"}]}
    transport.replies.extend([(200, history), (200, history)])
    assert client._current_version_is_draft() is draft
    assert client._get_version_id_by_name("v2") == "version-2"


def test_create_and_new_draft_keep_backend_version(client, transport):
    client.template.id = None
    transport.replies.extend([(201, {"result": {**TEMPLATE, "template_version": "v3"}}),
                              (201, {"result": [{"template_version": "v4"}]})])
    assert client.create() is client
    assert client.template.version == "v3"
    client._create_new_draft()
    assert client.template.version == "v4"


@pytest.mark.parametrize("operation", ["generate", "improve"])
def test_generation_bad_request_keeps_sdk_exception(client, transport, operation):
    before = copy.deepcopy(client.template)
    client._last_generation_id = "prior-job"
    transport.replies.append((400, {"code": "INVALID_REQUIREMENTS", "message": "Invalid requirements"}))
    with pytest.raises(SDKException, match="Invalid requirements"):
        getattr(client, operation)("invalid")
    assert len(transport.calls) == 1
    assert client.template == before
    assert client._last_generation_id == "prior-job"


@pytest.mark.parametrize("by_name", [False, True])
@pytest.mark.parametrize("status", [403, 404, 500])
def test_rejected_http_delete_keeps_cache(client, transport, by_name, status):
    original = client.template
    key = transport.cache.make_key(NAME, label="production")
    transport.cache.set(key, original)
    if by_name:
        transport.replies.append((200, {"result": TEMPLATE}))
    transport.replies.append((status, {"message": "Deletion rejected"}))
    # This compatibility check isolates cache preservation. Older clients did
    # not raise for failed DELETE responses; corrected clients may raise.
    try:
        Prompt.delete_template_by_name(NAME, **AUTH) if by_name else client.delete()
    except HTTPError:
        pass
    assert transport.cache.get_stale(key) is original


@pytest.mark.parametrize("by_name", [False, True])
def test_delete_keeps_other_names_with_same_prefix(client, transport, by_name):
    other_names = [NAME + "-other", NAME + "s", NAME + "|notes"]
    keys = [key for name in other_names for key in (
        name, transport.cache.make_key(name, version="v2"),
        transport.cache.make_key(name, label="production"),
    )]
    original = client.template
    for key in keys:
        transport.cache.set(key, original)
    if by_name:
        transport.replies.append((200, {"result": TEMPLATE}))
    transport.replies.append((204, None))
    Prompt.delete_template_by_name(NAME, **AUTH) if by_name else client.delete()
    for key in keys:
        assert transport.cache.get_stale(key) is original


@pytest.mark.parametrize("by_name", [False, True])
def test_deleting_one_name_preserves_cached_lookup_of_another(client, transport, by_name):
    other_name = NAME + "-backup"
    other = client.template.model_copy(update={
        "name": other_name, "id": UUID("00000000-0000-0000-0000-000000000002"),
    })
    transport.cache.set(transport.cache.make_scoped_key(
        other_name, scope=transport.cache.scope_for(client), label="production"
    ), other)
    if by_name:
        transport.replies.append((200, {"result": TEMPLATE}))
    transport.replies.append((204, None))
    Prompt.delete_template_by_name(NAME, **AUTH) if by_name else client.delete()
    calls_before_lookup = len(transport.calls)
    # A temporary backend failure must not break an unrelated fresh cache hit.
    transport.replies.append((503, {"message": "Temporarily unavailable"}))
    found = Prompt.get_template_by_name(other_name, label="production", **AUTH)
    try:
        assert found.template is other
        assert found.template.name == other_name
        assert len(transport.calls) == calls_before_lookup
    finally:
        found.close()


@pytest.mark.parametrize("by_name", [False, True])
@pytest.mark.parametrize("name_suffix", ["|v:backup", "|label:backup"])
def test_delete_preserves_distinct_name_containing_selector_syntax(client, transport, by_name, name_suffix):
    other_name = NAME + name_suffix
    # Exercise normal name validation rather than bypassing it with model_copy.
    other = PromptTemplate(name=other_name, id=UUID("00000000-0000-0000-0000-000000000002"),
                           version="v2", messages=[])
    assert other.name == other_name
    other_key = transport.cache.make_scoped_key(
        other_name, scope=transport.cache.scope_for(client), label="production"
    )
    target_keys = [NAME, transport.cache.make_key(NAME, version="v2"),
                   transport.cache.make_key(NAME, label="production")]
    assert other_key not in target_keys
    for key in target_keys:
        transport.cache.set(key, client.template)
    transport.cache.set(other_key, other)
    if by_name:
        transport.replies.append((200, {"result": TEMPLATE}))
    transport.replies.append((204, None))
    assert (Prompt.delete_template_by_name(NAME, **AUTH) if by_name else client.delete()) is True
    calls_before_lookup = len(transport.calls)
    # An unrelated fresh cache hit remains usable during a backend outage.
    transport.replies.append((503, {"message": "Temporarily unavailable"}))
    found = Prompt.get_template_by_name(other_name, label="production", **AUTH)
    try:
        assert found.template is other
        assert len(transport.calls) == calls_before_lookup
        assert transport.cache.get_stale(other_key) is other
    finally:
        found.close()


@pytest.mark.parametrize("by_name", [False, True])
@pytest.mark.parametrize("status", [302, 403, 404, 500])
def test_unsuccessful_delete_raises_before_changing_state(client, transport, by_name, status):
    original = client.template
    keys = [NAME, transport.cache.make_key(NAME, version="v2"),
            transport.cache.make_key(NAME, label="production")]
    for key in keys:
        transport.cache.set(key, original)
    if by_name:
        transport.replies.append((200, {"result": TEMPLATE}))
    transport.replies.append((status, {"message": "Deletion rejected"}))
    error_type = HTTPError if status >= 400 else SDKException
    with pytest.raises(error_type):
        Prompt.delete_template_by_name(NAME, **AUTH) if by_name else client.delete()
    assert client.template is original
    for key in keys:
        assert transport.cache.get_stale(key) is original
    assert len(transport.calls) == (2 if by_name else 1)


def test_prefix_invalidation_remains_available(transport, client):
    keys = [NAME, NAME + "-backup", transport.cache.make_key(NAME, label="production")]
    for key in keys:
        transport.cache.set(key, client.template)
    transport.cache.set("other-template", client.template)
    transport.cache.invalidate(NAME)
    assert all(transport.cache.get_stale(key) is None for key in keys)
    assert transport.cache.get_stale("other-template") is client.template
