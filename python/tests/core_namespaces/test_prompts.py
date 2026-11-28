import copy
import json

import httpx
import pytest

from fi.errors import BadRequestError, NotFoundError, UnexpectedRedirectError
from fi.prompts import PromptsClient

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("method,args,kwargs,verb,path,body,query", [
    ("list", (), {"limit": 2, "search": "hello & world"}, "GET", "prompt-templates/", None, {"limit": "2", "search": "hello & world"}),
    ("create", ({"name": "hello", "prompt_config": [{"messages": []}]},), {}, "POST", "prompt-templates/create-draft/", {"name": "hello", "prompt_config": [{"messages": []}]}, {}),
    ("get", ("p1",), {}, "GET", "prompt-templates/p1/", None, {}),
    ("update", ("p1", {"description": None}), {}, "PATCH", "prompt-templates/p1/", {"description": None}, {}),
    ("delete", ("p1",), {}, "DELETE", "prompt-templates/p1/", None, {}),
    ("get_by_name", ("hello & world",), {"version": "v2"}, "GET", "prompt-labels/get-by-name/", None, {"name": "hello & world", "version": "v2"}),
    ("get_by_name", ("hello & world",), {"label": "release & review"}, "GET", "prompt-labels/get-by-name/", None, {"name": "hello & world", "label": "release & review"}),
    ("get_by_label", ("hello", "production"), {}, "GET", "prompt-labels/get-by-name/", None, {"name": "hello", "label": "production"}),
    ("versions.list", ("p1",), {"page": 2, "limit": 5}, "GET", "prompt-templates/p1/versions/", None, {"page": "2", "limit": "5"}),
    ("versions.create", ("p1", {"new_prompts": [{"prompt_config": []}]}), {}, "POST", "prompt-templates/p1/add-new-draft/", {"new_prompts": [{"prompt_config": []}]}, {}),
    ("versions.commit", ("p1", "v2"), {"message": "release", "set_default": True}, "POST", "prompt-templates/p1/commit/", {"version_name": "v2", "message": "release", "set_default": True, "is_draft": False}, {}),
    ("versions.set_default", ("hello", "v2"), {}, "POST", "prompt-labels/set-default/", {"template_name": "hello", "version": "v2"}, {}),
    ("labels.list", (), {"page": 2}, "GET", "prompt-labels/", None, {"page": "2"}),
    ("labels.create", ({"name": "review", "type": "custom"},), {}, "POST", "prompt-labels/", {"name": "review", "type": "custom"}, {}),
    ("labels.get", ("l1",), {}, "GET", "prompt-labels/l1/", None, {}),
    ("labels.update", ("l1", {"name": "reviewed"}), {}, "PATCH", "prompt-labels/l1/", {"name": "reviewed"}, {}),
    ("labels.delete", ("l1",), {}, "DELETE", "prompt-labels/l1/", None, {}),
    ("labels.assign", ("p1", "l1"), {"version": "v2"}, "POST", "prompt-labels/p1/l1/assign-label-by-id/", {"version": "v2"}, {}),
    ("labels.remove", ("v-id", "l1"), {}, "POST", "prompt-labels/remove/", {"version_id": "v-id", "label_id": "l1"}, {}),
    ("labels.for_template", ("p1",), {}, "GET", "prompt-labels/template-labels/", None, {"template_id": "p1"}),
])
async def test_prompt_operations(resources, method, args, kwargs, verb, path, body, query):
    target = resources.prompts
    for part in method.split("."):
        target = getattr(target, part)
    assert await resources.call(target, *args, **kwargs) == {"ok": True}
    request, = resources.requests
    assert request.method == verb
    assert request.url.path == "/model-hub/" + path
    assert dict(request.url.params) == query
    assert (json.loads(request.content) if request.content else None) == body


@pytest.mark.parametrize("body", [{"name": "hello"}, {"name": "hello", "prompt_config": []}, {"name": "hello", "prompt_config": {"messages": []}}])
async def test_create_requires_the_first_version_config(resources, body):
    with pytest.raises(ValueError, match="prompt_config"):
        await resources.call(resources.prompts.create, body)
    assert resources.requests == []


@pytest.mark.parametrize("selector", [
    {},
    {"version": None, "label": None},
    {"version": ""},
    {"label": ""},
    {"version": " \t"},
    {"label": " \t"},
    {"version": "v1", "label": "prod"},
    {"version": "v1", "label": ""},
    {"version": "", "label": "prod"},
    {"version": 1},
    {"label": False},
])
async def test_lookup_requires_exactly_one_nonempty_selector_before_request(resources, selector):
    with pytest.raises(BadRequestError, match="exactly one of version or label") as error:
        await resources.call(resources.prompts.get_by_name, "hello", **selector)
    assert error.value.code == "invalid_prompt_selector"
    assert resources.requests == []


async def test_empty_label_shortcut_rejected_before_request(resources):
    with pytest.raises(BadRequestError, match="exactly one of version or label"):
        await resources.call(resources.prompts.get_by_label, "hello", "")
    assert resources.requests == []


async def test_generated_path_encoding(resources):
    await resources.call(resources.prompts.labels.get, "a/b ?#")
    assert resources.requests[0].url.raw_path == b"/model-hub/prompt-labels/a%2Fb%20%3F%23/"


@pytest.mark.parametrize("response,error", [
    (httpx.Response(404, json={"detail": "missing"}, headers={"x-request-id": "request-one"}), NotFoundError),
    (httpx.Response(200, json={"status": False, "result": "bad label"}), BadRequestError),
    (httpx.Response(302, headers={"location": "http://127.0.0.2/private"}), UnexpectedRedirectError),
])
async def test_prompt_errors(resources, response, error):
    resources.replies.append(httpx.Response(response.status_code, headers=response.headers, content=response.content))
    with pytest.raises(error):
        await resources.call(resources.prompts.get, "p1")
    assert len(resources.requests) == 1


async def test_retrieved_version_compiles_without_another_request(resources):
    template = {"id": "p1", "name": "hello", "version": "v2", "prompt_config": [{"messages": [{"role": "user", "content": "Hello {{name}}"}]}]}
    resources.replies.append(httpx.Response(200, json={"status": True, "result": template}))
    fetched = await resources.call(resources.prompts.get_by_label, "hello", "production")
    assert fetched["version"] == "v2"
    assert resources.prompts.compile(fetched, {"name": "reader"}) == [{"role": "user", "content": "Hello reader"}]
    assert len(resources.requests) == 1


async def test_prompt_page_keeps_metadata(resources):
    page = {"count": 5, "next": "?page=2", "previous": None, "results": [{"id": "p1"}]}
    resources.replies.append(httpx.Response(200, json=page))
    assert await resources.call(resources.prompts.list, page=1) == page


async def test_compile_is_local_preserves_multimodal_and_does_not_mutate(resources):
    template = {"prompt_config": [{"messages": [
        {"role": "user", "content": [{"type": "text", "text": "Hello {{ who }} / {{missing}}"}, {"type": "image_url", "image_url": {"url": "data:example"}}]},
        {"type": "placeholder", "name": "history"},
        {"type": "placeholder", "name": "unresolved"},
    ]}]}
    variables = {"who": "reader", "history": [{"role": "assistant", "content": "Welcome {{who}}", "tool_calls": [{"id": "call-one"}]}]}
    before = copy.deepcopy((template, variables))
    result = resources.prompts.compile(template, variables)
    assert result[0]["content"][0]["text"] == "Hello reader / {{missing}}"
    assert result[0]["content"][1] == {"type": "image_url", "image_url": {"url": "data:example"}}
    assert result[1] == {"role": "assistant", "content": "Welcome reader", "tool_calls": [{"id": "call-one"}]}
    assert result[2] == {"type": "placeholder", "name": "unresolved"}
    result[1]["tool_calls"][0]["id"] = "changed"
    assert (template, variables) == before
    assert resources.requests == []


@pytest.mark.parametrize("template,variables", [
    ({}, {}),
    ({"messages": [{}]}, {}),
    ({"messages": [{"type": "placeholder", "name": "h"}]}, {"h": "not a list"}),
    ({"messages": [{"type": "placeholder", "name": "h"}]}, {"h": [{"role": "user"}]}),
])
async def test_compile_rejects_invalid_messages(template, variables):
    with pytest.raises(ValueError):
        PromptsClient.compile(template, variables)
