"""A1c default-label behavior through the retained E1/A1/A2 facade.

Only local MockTransport responses: these controls do not establish server
acceptance or installed-package readiness. Original component tests are unchanged.
"""
import copy
import json
import warnings

import httpx
import pytest

from fi import FutureAGIClient
from fi.queues import DefaultQueueLabelError

BASE = "http://composition.test"
SCOPE = "22222222-2222-4222-8222-222222222222"
LABEL = "11111111-1111-4111-8111-111111111111"
QUEUE = "33333333-3333-4333-8333-333333333333"
USER = "44444444-4444-4444-8444-444444444444"
CREATE_PATH = "/model-hub/annotation-queues/"
DEFAULT_PATH = CREATE_PATH + "get-or-create-default/"


def default_response(action, labels=True):
    return {"status": True, "result": {
        "queue": {"id": QUEUE, "name": "Default", "status": "active", "is_default": True},
        "labels": [{"id": LABEL, "name": "Helpful", "type": "thumbs_up_down",
                    "settings": {}, "allow_notes": False, "required": False, "order": 0}]
                  if labels else [],
        "created": action == "created", "action": action,
    }}


@pytest.fixture
def facade():
    clients = []

    def make(responses):
        replies = iter(responses)
        sent = []

        def handle(request):
            sent.append((request.method, request.url.path, dict(request.url.params),
                         json.loads(request.content) if request.content else None))
            status, body = next(replies)
            return httpx.Response(status, json=body)

        root = FutureAGIClient(api_key="test", secret_key="test", base_url=BASE)
        transport = httpx.Client(base_url=BASE, transport=httpx.MockTransport(handle))
        root.generated_client.set_httpx_client(transport)
        clients.append(transport)
        return root, sent

    yield make
    for client in clients:
        client.close()


@pytest.mark.parametrize("scope", ["project", "dataset", "agent_definition"])
@pytest.mark.parametrize("action", ["created", "restored", "fetched"])
def test_composed_default_lookup_preserves_body_and_one_warning(facade, scope, action):
    response = default_response(action)
    created = {"id": QUEUE, "name": "Named", "auto_assign": False}
    root, sent = facade([(200, response), (201, created)])
    body = {"name": "Named", scope: SCOPE, "auto_assign": False,
            "annotator_ids": [USER], "annotator_roles": {USER: ["reviewer"]}}
    original = copy.deepcopy(body)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = root.annotation_queues.create(body)
    assert result == created
    assert body == original
    assert len(caught) == 1
    assert caught[0].category is DeprecationWarning
    assert "label_ids will be required" in str(caught[0].message)
    assert "not scoped" in str(caught[0].message)
    assert sent == [
        ("POST", DEFAULT_PATH, {}, {scope + "_id": SCOPE}),
        ("POST", CREATE_PATH, {}, {"name": "Named", "label_ids": [LABEL],
         "auto_assign": False, "annotator_ids": [USER], "annotator_roles": {USER: ["reviewer"]}}),
    ]


@pytest.mark.parametrize("action", ["created", "restored", "fetched"])
def test_composed_direct_default_keeps_envelope(facade, action):
    response = default_response(action)
    root, sent = facade([(200, response)])
    assert root.annotation_queues.get_or_create_default(project_id=SCOPE) == response
    assert sent == [("POST", DEFAULT_PATH, {}, {"project_id": SCOPE})]


@pytest.mark.parametrize("action", ["created", "restored", "fetched"])
def test_composed_empty_default_keeps_lookup_side_effect_but_never_creates(facade, action):
    root, sent = facade([(200, default_response(action, labels=False))])
    with pytest.warns(DeprecationWarning, match="label_ids will be required") as caught:
        with pytest.raises(DefaultQueueLabelError, match="no labels"):
            root.annotation_queues.create({"name": "Named", "project": SCOPE})
    assert len(caught) == 1
    assert sent == [("POST", DEFAULT_PATH, {}, {"project_id": SCOPE})]


@pytest.mark.parametrize("body,warning", [
    ({"name": "Named", "label_ids": None, "project": SCOPE}, False),
    ({"name": "Named", "label_ids": [], "project": SCOPE}, False),
    ({"label_ids": [LABEL], "project": SCOPE}, False),
    ({"project": SCOPE}, False),
    ({"name": "Named"}, True),
    ({"name": "Named", "project": None}, True),
    ({"name": "Named", "project": ""}, True),
    ({"name": "Named", "project": SCOPE, "dataset": SCOPE}, True),
])
def test_composed_invalid_create_never_requests(facade, body, warning):
    root, sent = facade([])
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with pytest.raises((TypeError, ValueError)):
            root.annotation_queues.create(body)
    assert sent == []
    assert len(caught) == int(warning)
    if warning:
        assert caught[0].category is DeprecationWarning


@pytest.mark.parametrize("key", ["project_id", "dataset_id", "agent_definition_id"])
@pytest.mark.parametrize("explicit", [False, True])
def test_composed_scope_ids_refused_before_lookup_or_warning(facade, key, explicit):
    root, sent = facade([])
    body = {"name": "Named", "project": SCOPE, key: SCOPE}
    if explicit:
        body["label_ids"] = [LABEL]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with pytest.raises(ValueError, match="get_or_create_default"):
            root.annotation_queues.create(body)
    assert sent == []
    assert not caught


def test_composed_explicit_labels_skip_lookup_and_strip_null_scope_ids(facade):
    created = {"id": QUEUE, "name": "Named"}
    root, sent = facade([(201, created)])
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert root.annotation_queues.create({
            "name": "Named", "label_ids": [LABEL], "project_id": None,
            "dataset_id": None, "agent_definition_id": None,
        }) == created
    assert not caught
    assert sent == [("POST", CREATE_PATH, {}, {"name": "Named", "label_ids": [LABEL]})]


def test_composed_explicit_scope_warns_without_lookup(facade):
    root, sent = facade([(201, {"id": QUEUE, "name": "Named"})])
    with pytest.warns(DeprecationWarning, match="read-only") as caught:
        root.annotation_queues.create({"name": "Named", "label_ids": [LABEL], "project": SCOPE})
    assert len(caught) == 1
    assert sent == [("POST", CREATE_PATH, {}, {"name": "Named", "label_ids": [LABEL]})]


def test_composed_retains_pagination_archive_and_withdrawal(facade):
    page = {"count": 0, "next": None, "previous": None, "results": [],
            "total_pages": 0, "current_page": 2}
    archive = {"status": True, "result": {"deleted": False, "archived": True, "queue_id": QUEUE}}
    root, sent = facade([(200, page), (200, archive)])
    assert root.annotation_queues.list(page=2, page_size=7, limit=5) == page
    assert root.annotation_queues.archive(QUEUE) == archive
    assert sent[0] == ("GET", CREATE_PATH, {"page": "2", "page_size": "7", "limit": "5", "archived": "false"}, None)
    assert not hasattr(root, "simulations")
    assert hasattr(root, "environments")


def test_composed_list_explicit_archived_false_preserves_pagination(facade):
    page = {"count": 0, "next": None, "previous": None, "results": [],
            "total_pages": 0, "current_page": 2}
    root, sent = facade([(200, page)])
    assert root.annotation_queues.list(page=2, page_size=7, limit=5, archived=False) == page
    assert sent == [
        ("GET", CREATE_PATH, {"page": "2", "page_size": "7", "limit": "5", "archived": "false"}, None),
    ]


def test_composed_list_explicit_archived_true_preserves_pagination(facade):
    page = {"count": 0, "next": None, "previous": None, "results": [],
            "total_pages": 0, "current_page": 2}
    root, sent = facade([(200, page)])
    assert root.annotation_queues.list(page=2, page_size=7, limit=5, archived=True) == page
    assert sent == [
        ("GET", CREATE_PATH, {"page": "2", "page_size": "7", "limit": "5", "archived": "true"}, None),
    ]
