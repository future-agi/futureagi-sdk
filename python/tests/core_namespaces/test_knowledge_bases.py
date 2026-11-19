import json

import httpx
import pytest

from fi.errors import PermissionDeniedError

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("method,args,kwargs,verb,path,body", [
    ("create", ("docs",), {}, "POST", "knowledge-base/", {"name": "docs"}),
    ("list", (), {"search": "docs & notes"}, "GET", "knowledge-base/list/", None),
    ("update", ("kb1", {"name": "new", "kb_id": "not-used"}), {}, "PATCH", "knowledge-base/", {"name": "new", "kb_id": "kb1"}),
    ("delete", ("kb1",), {}, "DELETE", "knowledge-base/", {"kb_ids": ["kb1"]}),
    ("documents.list", ("kb1",), {"page_number": 0, "page_size": 2}, "POST", "knowledge-base/files/", {"kb_id": "kb1", "page_number": 0, "page_size": 2}),
    ("documents.delete", ("kb1", ["guide.txt"]), {}, "DELETE", "knowledge-base/files/", {"kb_id": "kb1", "file_names": ["guide.txt"]}),
])
async def test_knowledge_base_operations(resources, method, args, kwargs, verb, path, body):
    target = resources.knowledge_bases
    for part in method.split("."):
        target = getattr(target, part)
    assert await resources.call(target, *args, **kwargs) == {"ok": True}
    request, = resources.requests
    assert (request.method, request.url.path) == (verb, "/model-hub/" + path)
    assert (json.loads(request.content) if request.content else None) == body
    if method == "list":
        assert request.url.params["search"] == "docs & notes"


async def test_add_text_is_multipart_on_shared_transport(resources):
    await resources.call(resources.knowledge_bases.documents.add_text, "kb1", "guide.txt", "Welcome café")
    request, = resources.requests
    assert request.method == "PATCH"
    assert request.url.path == "/model-hub/knowledge-base/"
    assert request.headers["content-type"].startswith("multipart/form-data; boundary=")
    assert b'name="kb_id"\r\n\r\nkb1' in request.content
    assert b'name="file"; filename="guide.txt"' in request.content
    assert "Welcome café".encode() in request.content
    assert b"Content-Type: text/plain" in request.content


@pytest.mark.parametrize("name", ["../guide.txt", "a\\b.txt", "x\r\ny.txt", "x\x00.txt", "guide.pdf", ""])
async def test_bad_document_names_fail_before_network(resources, name):
    with pytest.raises(ValueError):
        await resources.call(resources.knowledge_bases.documents.add_text, "kb1", name, "hello")
    assert resources.requests == []


async def test_empty_delete_is_not_sent(resources):
    with pytest.raises(ValueError):
        await resources.call(resources.knowledge_bases.documents.delete, "kb1", [])
    assert resources.requests == []


async def test_knowledge_base_permission_error(resources):
    resources.replies.append(httpx.Response(403, json={"detail": "denied"}, headers={"x-request-id": "kb-request"}))
    with pytest.raises(PermissionDeniedError) as exc:
        await resources.call(resources.knowledge_bases.delete, "foreign-kb")
    assert exc.value.request_id == "kb-request"
