import json

import httpx
import pytest

from fi.errors import BadRequestError

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("method,args,kwargs,verb,path,body,query", [
    ("list", (), {"source_type": "trace", "source_id": "t1", "label_id": "l1"}, "GET", "scores/", None, {"source_type": "trace", "source_id": "t1", "label_id": "l1"}),
    ("create", ({"source_type": "trace", "source_id": "t1", "label_id": "l1", "value": {"score": 0}},), {}, "POST", "scores/", {"source_type": "trace", "source_id": "t1", "label_id": "l1", "value": {"score": 0}}, {}),
    ("bulk_create", ({"scores": []},), {}, "POST", "scores/bulk/", {"scores": []}, {}),
    ("get", ("s1",), {}, "GET", "scores/s1/", None, {}),
    ("update", ("s1", {"notes": None}), {}, "PATCH", "scores/s1/", {"notes": None}, {}),
    ("delete", ("s1",), {}, "DELETE", "scores/s1/", None, {}),
    ("for_source", ("trace", "t1"), {"project_id": "p1"}, "GET", "scores/for-source/", None, {"source_type": "trace", "source_id": "t1", "project_id": "p1"}),
    ("labels.list", (), {"type": "star", "include_archived": True}, "GET", "annotations-labels/", None, {"type": "star", "include_archived": "true"}),
    ("labels.create", ({"name": "quality", "type": "star"},), {}, "POST", "annotations-labels/", {"name": "quality", "type": "star"}, {}),
    ("labels.get", ("l1",), {}, "GET", "annotations-labels/l1/", None, {}),
    ("labels.update", ("l1", {"description": None}), {}, "PATCH", "annotations-labels/l1/", {"description": None}, {}),
    ("labels.delete", ("l1",), {}, "DELETE", "annotations-labels/l1/", None, {}),
    ("labels.restore", ("l1",), {}, "POST", "annotations-labels/l1/restore/", {}, {}),
])
async def test_score_operations(resources, method, args, kwargs, verb, path, body, query):
    target = resources.scores
    for part in method.split("."):
        target = getattr(target, part)
    expected = {"ok": True}
    if method == "for_source":
        expected = {"status": True, "result": expected}
    assert await resources.call(target, *args, **kwargs) == expected
    request, = resources.requests
    assert (request.method, request.url.path) == (verb, "/model-hub/" + path)
    assert dict(request.url.params) == query
    assert (json.loads(request.content) if request.content else None) == body


@pytest.mark.parametrize("notes", [None, [], [{"source_id": "span1", "notes": "Needs review"}]])
async def test_for_source_preserves_scores_and_span_notes(resources, notes):
    payload = {"status": True, "result": [{"id": "s1", "value": {"score": 0}}]}
    if notes is not None:
        payload["span_notes"] = notes
    resources.replies.append(httpx.Response(200, json=payload))
    result = await resources.call(resources.root.scores.for_source, "observation_span", "span1")
    assert result == payload


async def test_invalid_source_fails_before_request(resources):
    with pytest.raises(ValueError):
        await resources.call(resources.scores.for_source, "invalid", "t1")
    assert resources.requests == []


async def test_score_validation_error(resources):
    resources.replies.append(httpx.Response(400, json={"code": "invalid_score", "detail": "bad score"}))
    with pytest.raises(BadRequestError) as exc:
        await resources.call(resources.scores.create, {"value": {}})
    assert exc.value.code == "invalid_score"
