"""Published 0.6.13 calls, through real serializers and mocked transports only.

Paging audit (FA 0e70e242, source paths relative to the FA repository):
method / published inputs -> accepted wire inputs / action / evidence
AnnotationQueue.list_queues: page=1,page_size=20 -> page,limit / rename size /
  model_hub/views/annotation_queues.py:3034-3049,3141-3146 (also accepts page_size)
AnnotationQueue.list_items: page=1,page_size=50 -> page,limit / rename size /
  model_hub/views/annotation_queues.py:4765,4908-4911;
  model_hub/serializers/annotation_queues.py:964-973
Both use tfc/utils/pagination.py:4-6 (ExtendedPageNumberPagination); inherited
  rest_framework/pagination.py:224-228 defaults to page 1, so NO base conversion.
Annotation.list_projects: page_number=0,page_size=20 -> same / unchanged /
  tracer/views/project.py:630-642
Dataset.get_column_id, download/_download_dataset: internal page_size=1/100,
  current_page_index=0 -> same / unchanged / model_hub/views/develop_dataset.py:2600-2601,2765-2766
EvalTemplateManager.list_templates: page=0,page_size=25 (POST body) -> same /
  unchanged / model_hub/views/separate_evals.py:2546-2549
EvalTemplateManager.get_ground_truth_data: page=1,page_size=50 -> same /
  unchanged / model_hub/views/separate_evals.py:5661-5667
EvalTemplateManager.get_template_usage: page=0,page_size=25 -> same / unchanged /
  model_hub/views/separate_evals.py:5962-5963,6272
EvalTemplateManager.list_template_feedback: page=0,page_size=25 -> same / unchanged /
  model_hub/views/separate_evals.py:6619-6620,6643
KnowledgeBase.list_kbs and Prompt.list_templates/list_template_versions: no published
  paging inputs and no paging keys emitted (fi/kb/client.py, fi/prompt/client.py).
  Server: model_hub/views/develop_dataset.py:16727-16771 (unpaginated KB list);
  model_hub/views/prompt_template.py:648,696-698,4316-4322,4354 (prompt lists use
  default pagination; the legacy SDK provides no page argument to translate).
No global page_size rewrite: dataset/project/eval endpoints require that spelling.
"""
import importlib
import inspect
import json
import warnings
from urllib.parse import urlsplit

import httpx
import pytest
import requests
from requests.adapters import BaseAdapter
from requests_futures.sessions import FuturesSession

from fi import FutureAGIClient
from fi.annotations import Annotation
from fi.evals.manager import EvalTemplateManager
from fi.queues import AnnotationQueue

BASE = "http://compat.test"
LABEL = "11111111-1111-4111-8111-111111111111"
SCOPE = "22222222-2222-4222-8222-222222222222"
QUEUE = "33333333-3333-4333-8333-333333333333"
PATHS = ("fi", "fi.queues", "fi.queues.client")


class Capture(BaseAdapter):
    def __init__(self, responses):
        self.responses = iter(responses)
        self.sent = []

    def send(self, request, **kwargs):
        self.sent.append(request)
        response = requests.Response()
        response.status_code = 200
        response._content = json.dumps(next(self.responses)).encode()
        response.request = request
        response.url = request.url
        return response

    def close(self):
        pass


@pytest.fixture
def legacy():
    sessions = []

    def make(cls=AnnotationQueue, responses=()):
        transport = Capture(responses)
        session = FuturesSession(max_workers=1)
        session.mount(BASE, transport)
        sessions.append(session)
        client = cls(fi_api_key="test", fi_secret_key="test", fi_base_url=BASE, session=session)
        return client, transport.sent

    yield make
    for session in sessions:
        session.close()
        session.executor.shutdown(wait=True)


@pytest.mark.parametrize("module,name,current", [
    ("fi.api.auth", "DatasetNotFoundError", "fi.utils.errors"),
    ("fi.client", "HttpMethod", "fi.api.types"),
    ("fi.client", "RequestConfig", "fi.api.types"),
    ("fi.client", "Routes", "fi.utils.routes"),
])
def test_published_reexports_are_identical(module, name, current):
    assert getattr(importlib.import_module(module), name, None) is getattr(importlib.import_module(current), name)


@pytest.mark.parametrize("path", ["fi", "fi.queues"])
def test_default_label_error_has_public_import(path):
    from fi._queue_create import DefaultQueueLabelError

    public = importlib.import_module(path)
    assert getattr(public, "DefaultQueueLabelError", None) is DefaultQueueLabelError
    assert "DefaultQueueLabelError" in public.__all__
    assert issubclass(public.DefaultQueueLabelError, ValueError)


@pytest.mark.parametrize("path", PATHS)
def test_omitted_label_default_has_readable_signature(path):
    from fi._queue_create import OMITTED_LABEL_IDS

    create = getattr(importlib.import_module(path), "AnnotationQueue").create
    signature = inspect.signature(create)
    assert signature.parameters["label_ids"].default is OMITTED_LABEL_IDS
    assert repr(OMITTED_LABEL_IDS) == "OMITTED_LABEL_IDS"
    assert "= OMITTED_LABEL_IDS" in str(signature)


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("method,kwargs,query", [
    ("list_queues", {}, "page=1&limit=20&include_counts=true"),
    ("list_queues", {"page": 2, "page_size": 7}, "page=2&limit=7&include_counts=true"),
    ("list_items", {}, "page=1&limit=50"),
    ("list_items", {"page": 2, "page_size": 7, "status": "pending"}, "page=2&limit=7&status=pending"),
])
def test_legacy_queue_wire_query(legacy, path, method, kwargs, query):
    cls = getattr(importlib.import_module(path), "AnnotationQueue")
    assert cls is AnnotationQueue
    client, sent = legacy(cls, [{"results": []}])
    getattr(client, method)(*([QUEUE] if method == "list_items" else []), **kwargs)
    assert urlsplit(sent[0].url).query == query


def test_projects_keep_zero_based_paging(legacy):
    client, sent = legacy(Annotation, [{"result": []}])
    client.list_projects(page_number=2, page_size=7)
    assert urlsplit(sent[0].url).query == "page_number=2&page_size=7"


@pytest.mark.parametrize("method,args,kwargs,response,query", [
    ("get_ground_truth_data", [SCOPE], {"page": 2, "page_size": 7},
     {"id": SCOPE}, "page=2&page_size=7"),
    ("get_template_usage", [SCOPE], {"page": 2, "page_size": 7},
     {"template_id": SCOPE}, "page=2&page_size=7&period=30d"),
    ("list_template_feedback", [SCOPE], {"page": 2, "page_size": 7},
     {"template_id": SCOPE}, "page=2&page_size=7"),
    ("list_templates", [], {"page": 2, "page_size": 7}, {}, ""),
])
def test_eval_paging_keeps_endpoint_specific_names(legacy, method, args, kwargs, response, query):
    client, sent = legacy(EvalTemplateManager, [{"status": True, "result": response}])
    getattr(client, method)(*args, **kwargs)
    assert urlsplit(sent[0].url).query == query
    if method == "list_templates":
        assert json.loads(sent[0].body) == {
            "page": 2, "page_size": 7, "owner_filter": "all", "sort_by": "updated_at", "sort_order": "desc",
        }


@pytest.mark.parametrize("method", ["get_column_id", "download"])
def test_dataset_paging_stays_zero_based(legacy, tmp_path, method):
    from fi.datasets import Dataset
    from fi.datasets.types import DatasetConfig
    from fi.utils.types import ModelTypes

    reply = {"result": {"column_config": [], "table": [], "metadata": {"total_pages": 2}}}
    client, sent = legacy(Dataset, [reply, reply])
    client.dataset_config = DatasetConfig(id=SCOPE, name="Legacy", model_type=ModelTypes.GENERATIVE_LLM)
    if method == "get_column_id":
        assert client.get_column_id("missing") is None
        expected = ["page_size=1&current_page_index=0"]
    else:
        client.download(str(tmp_path / "dataset.csv"))
        expected = ["page_size=100&current_page_index=0", "page_size=100&current_page_index=1"]
    assert [urlsplit(r.url).query for r in sent] == expected


def default_result(labels):
    return {"status": True, "result": {
        "queue": {"id": QUEUE, "name": "Default", "status": "active", "is_default": True},
        "labels": labels, "created": False, "action": "fetched",
    }}


@pytest.fixture
def facade():
    clients = []

    def make(responses):
        replies = iter(responses)
        sent = []
        def handle(request):
            sent.append(request)
            return httpx.Response(200, json=next(replies))
        client = FutureAGIClient(api_key="test", secret_key="test", base_url=BASE)
        http = httpx.Client(base_url=BASE, transport=httpx.MockTransport(handle))
        client.generated_client.set_httpx_client(http)
        clients.append(http)
        return client.annotation_queues, sent

    yield make
    for client in clients:
        client.close()


@pytest.mark.parametrize("surface", [*PATHS, "facade"])
@pytest.mark.parametrize("scope", ["project", "dataset", "agent_definition"])
def test_published_create_derives_default_labels_once(legacy, facade, surface, scope):
    # 0.6.13 signature: create(name, *, description=None, ..., project=None,
    # dataset=None, agent_definition=None, timeout=None); no label_ids parameter.
    responses = [default_result([{"id": LABEL, "name": "Helpful", "type": "thumbs_up_down", "settings": {}, "allow_notes": False, "required": False, "order": 0}]), {"id": QUEUE, "name": "Legacy"}]
    client, sent = facade(responses) if surface == "facade" else legacy(getattr(importlib.import_module(surface), "AnnotationQueue"), responses)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        if surface == "facade":
            client.create({"name": "Legacy", scope: SCOPE, "description": "kept"})
        else:
            client.create("Legacy", **{scope: SCOPE, "description": "kept", "timeout": 9})
    assert len(caught) == 1
    assert caught[0].category is DeprecationWarning
    assert "label_ids will be required" in str(caught[0].message)
    assert len(sent) == 2
    assert str(sent[0].url) == f"{BASE}/model-hub/annotation-queues/get-or-create-default/"
    bodies = [json.loads(r.content if isinstance(r, httpx.Request) else r.body) for r in sent]
    assert bodies == [{scope + "_id": SCOPE}, {"name": "Legacy", "description": "kept", "label_ids": [LABEL]}]


@pytest.mark.parametrize("surface", ["legacy", "facade"])
@pytest.mark.parametrize("scope,labels,reason", [
    ({}, [], "exactly one"),
    ({"project": SCOPE, "dataset": SCOPE}, [], "exactly one"),
    ({"project": SCOPE}, [], "no labels"),
])
def test_no_invented_default_label(legacy, facade, surface, scope, labels, reason):
    from fi.queues import DefaultQueueLabelError

    client, sent = facade([default_result(labels)]) if surface == "facade" else legacy(responses=[default_result(labels)])
    with pytest.warns(DeprecationWarning, match="label_ids will be required"):
        with pytest.raises(DefaultQueueLabelError, match=reason) as error:
            client.create({"name": "Legacy", **scope}) if surface == "facade" else client.create("Legacy", **scope)
    assert type(error.value).__name__ == "DefaultQueueLabelError"
    assert len(sent) == (1 if len(scope) == 1 else 0)


@pytest.mark.parametrize("surface", ["legacy", "facade"])
def test_explicit_labels_do_not_lookup_or_warn(legacy, facade, surface):
    client, sent = facade([{"id": QUEUE, "name": "Explicit"}]) if surface == "facade" else legacy(responses=[{"id": QUEUE, "name": "Explicit"}])
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        client.create({"name": "Explicit", "label_ids": [LABEL]}) if surface == "facade" else client.create("Explicit", label_ids=[LABEL])
    assert len(sent) == 1
    assert not caught
