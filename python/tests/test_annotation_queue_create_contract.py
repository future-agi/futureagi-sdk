"""Contract: both queue create() methods against the backend's AnnotationQueueSerializer.

The server facts come from the checked-in snapshot
tests/fixtures/server-contracts/annotation-queue-create.json (backend commit and file blobs
inside). Refresh it with scripts/snapshot-annotation-queue-contract.py (see its "refresh").
"""

import ast
import importlib.util
import inspect
import json
import warnings
from pathlib import Path
from unittest.mock import patch

import attrs
import httpx
import pytest
from fi import FutureAGIAPIError, FutureAGIClient
from fi._queue_create import (
    DEFAULT_QUEUE_SCOPE_IDS,
    IGNORED_ON_CREATE,
    REQUIRED_ON_CREATE,
)
from fi.futureagi_client import AnnotationQueuesClient
from fi.generated.openapi_client.models.annotation_queue import (
    AnnotationQueue as GeneratedQueue,
)
from fi.generated.openapi_client.models.queue_default_queue import QueueDefaultQueue
from fi.generated.openapi_client.models.queue_default_result import QueueDefaultResult
from fi.generated.openapi_client.models.queue_default_result_action import (
    QueueDefaultResultAction,
)
from fi.generated.openapi_client.models.queue_label_result import QueueLabelResult
from fi.queues.client import AnnotationQueue
from fi.queues.types import DefaultQueue, QueueDetail

ROOT = Path(__file__).parents[2]
SNAPSHOT = json.loads(
    (ROOT / "tests/fixtures/server-contracts/annotation-queue-create.json").read_text()
)
WRITABLE = set(SNAPSHOT["create"]["writable"])
REQUIRED = set(SNAPSHOT["create"]["required"])
# create() parameters that are not request fields.
TRANSPORT_PARAMETERS = {"self", "timeout"}
LABEL = "11111111-1111-4111-8111-111111111111"
USER = "22222222-2222-4222-8222-222222222222"


def _load_snapshot_script():
    path = ROOT / "scripts/snapshot-annotation-queue-contract.py"
    spec = importlib.util.spec_from_file_location(
        "snapshot_annotation_queue_contract", path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _facade(handler):
    client = FutureAGIClient(
        api_key="api-key", secret_key="secret-key", base_url="http://api.test"
    )
    client.generated_client.set_httpx_client(
        httpx.Client(base_url="http://api.test", transport=httpx.MockTransport(handler))
    )
    return client


def _capturing_facade():
    sent = []

    def handler(request):
        sent.append(json.loads(request.content))
        return httpx.Response(
            201, json={"id": "33333333-3333-4333-8333-333333333333", "name": "Q"}
        )

    return _facade(handler), sent


def test_snapshot_pins_backend_content_and_is_consistent():
    source = SNAPSHOT["source"]
    assert len(source["sha256"]) == 64 and int(source["sha256"], 16) >= 0
    assert source["sha256"] == _load_snapshot_script()._METADATA["source_identity"](source["files"])
    assert "commit" not in source and "ref" not in source
    paths = {f["path"] for f in source["files"]}
    assert "futureagi/model_hub/serializers/annotation_queues.py" in paths
    assert "futureagi/model_hub/views/annotation_queues.py" in paths
    assert all(len(f["sha256"]) == 64 and int(f["sha256"], 16) >= 0 for f in source["files"])
    assert "scripts/snapshot-annotation-queue-contract.py" in SNAPSHOT["refresh"]
    # The derived "create" section follows from the parsed fields (no hand edits).
    derived = _load_snapshot_script().derive(
        SNAPSHOT["serializer"], SNAPSHOT["model_fields"]
    )
    assert derived == SNAPSHOT["create"]


def test_the_view_never_applies_the_ignored_fields_on_create():
    view = SNAPSHOT["view"]
    # The view validates with the serializer the snapshot describes ...
    assert view["serializer_class"] == SNAPSHOT["serializer"]["class"]
    # ... and saves nothing else that could scope the queue.
    assert not set(IGNORED_ON_CREATE) & set(view["perform_create_saves"])


def test_get_or_create_default_takes_exactly_one_scope_id_per_ignored_field():
    default = SNAPSHOT["get_or_create_default"]
    assert default["methods"] == ["POST"]
    assert default["path"] == "/model-hub/annotation-queues/get-or-create-default/"
    request = default["request_serializer"]
    scope_ids = {f"{field}_id" for field in IGNORED_ON_CREATE}
    assert set(request["declared_fields"]) == scope_ids
    assert set(request["exactly_one_of"]) == scope_ids
    assert not any(f.get("required") for f in request["declared_fields"].values())


def test_queue_client_create_signature_matches_the_server():
    params = inspect.signature(AnnotationQueue.create).parameters
    fields = set(params) - TRANSPORT_PARAMETERS - set(IGNORED_ON_CREATE)
    assert fields == WRITABLE
    required = {
        name
        for name, p in params.items()
        if name not in TRANSPORT_PARAMETERS and p.default is inspect.Parameter.empty
    }
    assert required == REQUIRED - {"label_ids"}


@pytest.mark.parametrize("missing", sorted(REQUIRED))
def test_queue_client_create_refuses_none_for_each_required_field(missing):
    # A required parameter can still be given None; the server requires a value, so the client
    # refuses it before any request, as TypeScript's AnnotationQueue.create does.
    with patch.dict("os.environ", {"FI_API_KEY": "k", "FI_SECRET_KEY": "s"}):
        client = AnnotationQueue()
    values = {"name": "Q", "label_ids": [LABEL]}
    assert REQUIRED <= set(values)
    values[missing] = None
    with patch.object(client, "request") as request:
        with pytest.raises(ValueError) as raised:
            client.create(**values)
    assert str(raised.value) == (
        f"AnnotationQueue.create(): {missing} is required; the server refuses a queue "
        "without it"
    )
    request.assert_not_called()


def test_ignored_fields_are_read_only_on_the_server():
    read_only = set(SNAPSHOT["serializer"]["read_only_fields"])
    for field in IGNORED_ON_CREATE:
        assert field in read_only
        assert field not in WRITABLE
    params = inspect.signature(AnnotationQueue.create).parameters
    assert all(params[f].default is None for f in IGNORED_ON_CREATE)


def test_queue_client_create_puts_every_server_field_on_the_wire():
    with patch.dict("os.environ", {"FI_API_KEY": "k", "FI_SECRET_KEY": "s"}):
        client = AnnotationQueue()
    values = {
        "label_ids": [LABEL],
        "description": "d",
        "instructions": "i",
        "assignment_strategy": "manual",
        "annotations_required": 1,
        "reservation_timeout_minutes": 60,
        "requires_review": False,
        "auto_assign": False,
        "annotator_ids": [USER],
        "annotator_roles": {USER: ["annotator"]},
    }
    with patch.object(
        client, "request", return_value=QueueDetail(id="q1", name="Q")
    ) as request:
        client.create("Q", **values)
    assert set(request.call_args[0][0].json) == WRITABLE


def test_generated_body_model_carries_every_server_field():
    assert WRITABLE <= {field.name for field in attrs.fields(GeneratedQueue)}


def test_facade_create_puts_every_server_field_on_the_wire():
    client, sent = _capturing_facade()
    body = {
        "name": "Q",
        "label_ids": [LABEL],
        "description": "d",
        "instructions": "i",
        "assignment_strategy": "manual",
        "annotations_required": 1,
        "reservation_timeout_minutes": 60,
        "requires_review": False,
        "auto_assign": False,
        "annotator_ids": [USER],
        "annotator_roles": {USER: ["annotator"]},
    }
    assert set(body) == WRITABLE
    client.annotation_queues.create(body)
    assert set(sent[0]) == WRITABLE
    # The server's format (a role or a list of roles per user), not the generated object type.
    assert sent[0]["annotator_roles"] == {USER: ["annotator"]}


def test_facade_required_keys_are_the_servers():
    assert set(REQUIRED_ON_CREATE) == REQUIRED
    assert set(REQUIRED_ON_CREATE) <= WRITABLE


@pytest.mark.parametrize("missing", sorted(REQUIRED))
@pytest.mark.parametrize("absent", [False, True], ids=["key-absent", "value-none"])
def test_facade_create_refuses_a_body_without_each_required_field(missing, absent):
    # Driven by the snapshot: a field the server starts to require fails here until the
    # facade checks it too.
    client, sent = _capturing_facade()
    body = {"name": "Q", "label_ids": [LABEL], "description": "d"}
    assert REQUIRED <= set(body)
    if absent:
        del body[missing]
    else:
        body[missing] = None
    with pytest.raises(ValueError, match=f"needs {missing}"):
        client.annotation_queues.create(body)
    assert sent == []


@pytest.mark.parametrize(
    "body, error, match",
    [
        ({"name": "Q"}, ValueError, "needs label_ids"),
        ({"label_ids": [LABEL]}, ValueError, "needs name"),
        (
            {"name": "Q", "label_ids": []},
            ValueError,
            "at least one annotation label id",
        ),
        ({"name": "Q", "label_ids": LABEL}, TypeError, "list of id strings"),
        (GeneratedQueue(name="Q"), ValueError, "needs label_ids"),
    ],
)
def test_facade_create_refuses_a_body_without_labels_before_any_request(
    body, error, match
):
    client, sent = _capturing_facade()
    with pytest.raises(error, match=match):
        client.annotation_queues.create(body)
    assert sent == []


def test_facade_create_drops_ignored_fields_with_a_deprecation_warning():
    client, sent = _capturing_facade()
    with pytest.warns(DeprecationWarning, match="ignored by the server") as caught:
        client.annotation_queues.create(
            {
                "name": "Q",
                "label_ids": [LABEL],
                "project": USER,
                "agent_definition": USER,
            }
        )
    assert len(caught) == 1
    assert caught[0].filename == __file__
    message = str(caught[0].message)
    assert "remain accepted for compatibility" in message
    # The hint is a call on this client, not a raw endpoint.
    assert "annotation_queues.get_or_create_default(project_id=...)" in message
    assert "/model-hub/" not in message
    assert sent == [{"name": "Q", "label_ids": [LABEL]}]


def test_facade_create_accepts_the_generated_model_and_drops_its_scope_fields():
    client, sent = _capturing_facade()
    with pytest.warns(DeprecationWarning):
        client.annotation_queues.create(
            GeneratedQueue(name="Q", label_ids=[LABEL], dataset=USER)
        )
    assert sent == [{"name": "Q", "label_ids": [LABEL]}]


DEFAULT_QUEUE = SNAPSHOT["get_or_create_default"]
DEFAULT_QUEUE_FIELDS = set(DEFAULT_QUEUE["request_serializer"]["declared_fields"])


@pytest.mark.parametrize(
    "method",
    [AnnotationQueue.get_or_create_default, AnnotationQueuesClient.get_or_create_default],
    ids=["AnnotationQueue", "annotation_queues"],
)
def test_get_or_create_default_signature_matches_the_server(method):
    params = inspect.signature(method).parameters
    fields = set(params) - TRANSPORT_PARAMETERS
    assert fields == DEFAULT_QUEUE_FIELDS
    # Every scope id is optional in the signature; the call checks that exactly one is given.
    assert all(params[f].kind is inspect.Parameter.KEYWORD_ONLY for f in fields)
    assert all(params[f].default is None for f in fields)
    assert set(DEFAULT_QUEUE_SCOPE_IDS.values()) == DEFAULT_QUEUE_FIELDS
    assert set(DEFAULT_QUEUE_SCOPE_IDS) == set(IGNORED_ON_CREATE)


# A get-or-create-default answer in the shape the view returns: the queue, and each label with
# the 8 fields of the generated QueueLabelResult (id, name, type, settings, description,
# allow_notes, required, order).
DEFAULT_QUEUE_ANSWER = {
    "queue": {
        "id": "33333333-3333-4333-8333-333333333333",
        "name": "Default - P",
        "description": "",
        "instructions": "",
        "status": "active",
        "is_default": True,
    },
    "labels": [
        {
            "id": LABEL,
            "name": "Helpful",
            "type": "categorical",
            "settings": {"options": [{"label": "Yes"}, {"label": "No"}], "multi_choice": False},
            "description": "Was the answer helpful?",
            "allow_notes": True,
            "required": True,
            "order": 0,
        }
    ],
    "created": True,
    "action": "created",
}


def _attrs_names(model):
    return {f.name for f in attrs.fields(model)} - {"additional_properties"}


def test_default_queue_matches_the_generated_result():
    # fi.queues.DefaultQueue (what AnnotationQueue.get_or_create_default returns) is written by
    # hand; the generated QueueDefaultResult follows the server's response serializer. A field
    # added to, or dropped from, either fails here.
    assert set(DefaultQueue.model_fields) == _attrs_names(QueueDefaultResult)
    assert _attrs_names(QueueDefaultQueue) <= set(QueueDetail.model_fields)
    assert {action.value for action in QueueDefaultResultAction} == {
        "created",
        "restored",
        "fetched",
    }
    # The view's answer, read by the generated model, parses into DefaultQueue unchanged.
    generated = QueueDefaultResult.from_dict(DEFAULT_QUEUE_ANSWER).to_dict()
    assert generated == DEFAULT_QUEUE_ANSWER
    parsed = DefaultQueue(**generated)
    assert parsed.queue.model_dump(exclude_none=True) == DEFAULT_QUEUE_ANSWER["queue"]
    assert parsed.labels == DEFAULT_QUEUE_ANSWER["labels"]
    assert (parsed.created, parsed.action) == (True, "created")
    # Each label has the generated QueueLabelResult's fields, the ones DefaultQueue.labels lists.
    (label,) = DEFAULT_QUEUE_ANSWER["labels"]
    assert set(QueueLabelResult.from_dict(label).to_dict()) == set(label)
    assert len(label) == len(_attrs_names(QueueLabelResult)) == 8


@pytest.mark.parametrize("field", sorted(DEFAULT_QUEUE_FIELDS))
def test_facade_get_or_create_default_puts_one_id_on_the_wire(field):
    sent = []

    def handler(request):
        sent.append((request.method, request.url.path, json.loads(request.content)))
        return httpx.Response(200, json={"status": True, "result": DEFAULT_QUEUE_ANSWER})

    result = _facade(handler).annotation_queues.get_or_create_default(**{field: USER})
    assert sent == [(DEFAULT_QUEUE["methods"][0], DEFAULT_QUEUE["path"], {field: USER})]
    # A plain dict, like every other annotation_queues method; the label went through the
    # generated QueueLabelResult and back unchanged.
    assert type(result) is dict
    assert result == {"status": True, "result": DEFAULT_QUEUE_ANSWER}
    assert result["result"]["labels"][0]["type"] == "categorical"


@pytest.mark.parametrize(
    "scope, error",
    [
        ({}, ValueError),
        ({"project_id": USER, "dataset_id": USER}, ValueError),
        ({"agent_definition_id": ""}, TypeError),
        ({"project_id": "not-a-uuid"}, ValueError),
    ],
)
def test_facade_get_or_create_default_needs_exactly_one_id(scope, error):
    client, sent = _capturing_facade()
    with pytest.raises(error, match=r"^annotation_queues\.get_or_create_default\(\): "):
        client.annotation_queues.get_or_create_default(**scope)
    assert sent == []


@pytest.mark.parametrize("field", sorted(DEFAULT_QUEUE_FIELDS))
def test_facade_get_or_create_default_names_the_call_for_an_id_that_is_not_a_uuid(field):
    # The server's fields are UUIDFields, and the generated request model parses the id with
    # uuid.UUID; without the check the caller got a bare "badly formed hexadecimal UUID string".
    assert DEFAULT_QUEUE["request_serializer"]["declared_fields"][field]["field"] == "UUIDField"
    client, sent = _capturing_facade()
    with pytest.raises(ValueError) as raised:
        client.annotation_queues.get_or_create_default(**{field: "not-a-uuid"})
    assert str(raised.value) == (
        f"annotation_queues.get_or_create_default(): {field} must be a UUID, not 'not-a-uuid'"
    )
    assert sent == []


@pytest.mark.parametrize("argument", ["label_ids", "annotator_ids"])
def test_facade_create_names_the_call_for_an_id_that_is_not_a_uuid(argument):
    declared = SNAPSHOT["serializer"]["declared_fields"][argument]
    assert (declared["field"], declared["child"]) == ("ListField", "UUIDField")
    client, sent = _capturing_facade()
    body = {"name": "Q", "label_ids": [LABEL], argument: ["lbl-1"]}
    with pytest.raises(ValueError) as raised:
        client.annotation_queues.create(body)
    assert str(raised.value) == (
        f"annotation_queues.create(): {argument} must hold UUIDs, not 'lbl-1'"
    )
    assert sent == []


def test_facade_get_or_create_default_raises_the_api_error():
    def handler(request):
        return httpx.Response(404, json={"status": False, "result": "Project not found."})

    with pytest.raises(FutureAGIAPIError) as raised:
        _facade(handler).annotation_queues.get_or_create_default(project_id=USER)
    assert raised.value.status_code == 404


def test_the_create_serializer_accepts_the_scope_ids_without_an_error():
    # A plain ModelSerializer drops unknown keys without an error, and the scope ids are not
    # among its fields: sent on a create, they raise nothing and are never saved. Hence the SDK
    # refuses them.
    assert not any(b.startswith("Strict") for b in SNAPSHOT["serializer"]["bases"])
    assert not DEFAULT_QUEUE_FIELDS & set(SNAPSHOT["serializer"]["meta_fields"])


def test_the_create_path_uses_the_scope_ids_only_for_the_name_check():
    # The serializer reads project_id / dataset_id / agent_definition_id only in validate_name,
    # to scope its duplicate-name check; the view's create() and perform_create() use none of
    # them, and perform_create saves none. So the server never applies them to the queue, which
    # is what the create() refusal says. A backend that starts to use one elsewhere on the
    # create path is drift (--check exits 1) and fails here once the snapshot is refreshed.
    assert SNAPSHOT["serializer"]["scope_ids_read"] == {
        "validate_name": sorted(DEFAULT_QUEUE_FIELDS)
    }
    assert SNAPSHOT["view"]["scope_ids_read"] == {}
    assert not DEFAULT_QUEUE_FIELDS & set(SNAPSHOT["view"]["perform_create_saves"])


def test_snapshot_script_finds_the_scope_ids_a_method_uses():
    script = _load_snapshot_script()
    source = '''
class S:
    def validate_name(self, value):
        return self.context["request"].data.get("project_id")
    def create(self, validated_data):
        return Queue(dataset_id=validated_data.pop("x"))
    def update(self, instance, data):
        instance.agent_definition_id = data
    def other(self):
        return "label_ids"
'''
    cls = ast.parse(source).body[0]
    assert script.scope_ids_read(cls, DEFAULT_QUEUE_FIELDS) == {
        "validate_name": ["project_id"],
        "create": ["dataset_id"],
        "update": ["agent_definition_id"],
    }
    assert script.scope_ids_read(cls, DEFAULT_QUEUE_FIELDS, ("create",)) == {
        "create": ["dataset_id"]
    }


def test_snapshot_check_warns_when_a_pinned_file_changed(monkeypatch, capsys, tmp_path):
    # --check compares the parsed facts; a pinned file whose blob changed while the facts did
    # not is a WARNING (exit 0, or 2 with --strict), so a change the parser does not model is
    # never passed in silence.
    script = _load_snapshot_script()
    out = tmp_path / "snapshot.json"
    out.write_text(json.dumps(SNAPSHOT))
    fresh = json.loads(json.dumps(SNAPSHOT))
    fresh["source"]["sha256"] = "f" * 64
    path = "futureagi/model_hub/serializers/annotation_queues.py"
    (pinned,) = [f for f in fresh["source"]["files"] if f["path"] == path]
    old_blob, pinned["sha256"] = pinned["sha256"], "e" * 64
    monkeypatch.setattr(script, "build", lambda backend, ref: fresh)
    argv = ["--backend", "/backend", "--out", str(out), "--check"]

    assert script.main(argv) == 0
    printed = capsys.readouterr().out
    assert f"WARNING: {path} changed (sha256 {old_blob[:12]} -> {'e' * 12})" in printed
    assert "Read the retained source diff" in printed
    assert "1 pinned file(s) changed" in printed
    assert script.main([*argv, "--strict"]) == 2
    capsys.readouterr()

    # Unchanged blobs: no warning, exit 0 even with --strict.
    pinned["sha256"] = old_blob
    assert script.main([*argv, "--strict"]) == 0
    assert "WARNING" not in capsys.readouterr().out

    # A changed fact is drift, as before.
    fresh["serializer"]["scope_ids_read"]["create"] = ["project_id"]
    assert script.main(argv) == 1
    assert "DRIFT in serializer" in capsys.readouterr().out


@pytest.mark.parametrize("field", sorted(DEFAULT_QUEUE_FIELDS))
@pytest.mark.parametrize("as_model", [False, True], ids=["mapping", "generated-model"])
def test_facade_create_refuses_a_scope_id_before_any_request(field, as_model):
    client, sent = _capturing_facade()
    if as_model:
        body = GeneratedQueue(name="Q", label_ids=[LABEL])
        body.additional_properties[field] = USER
    else:
        body = {"name": "Q", "label_ids": [LABEL], field: USER}
    with pytest.raises(ValueError) as raised:
        client.annotation_queues.create(body)
    message = str(raised.value)
    assert message.startswith(f"annotation_queues.create(): {field} cannot be set")
    # Worded as the snapshot shows: never applied, only used for the name check.
    assert "the server never applies it to the queue" in message
    assert "duplicate-name check" in message
    assert f"annotation_queues.get_or_create_default({field}='{USER}')" in message
    assert sent == []


def test_facade_create_refuses_several_scope_ids_and_ignores_none():
    client, sent = _capturing_facade()
    with pytest.raises(ValueError, match="project_id and dataset_id cannot be set"):
        client.annotation_queues.create(
            {"name": "Q", "label_ids": [LABEL], "project_id": USER, "dataset_id": USER}
        )
    assert sent == []
    client.annotation_queues.create(
        {"name": "Q", "label_ids": [LABEL], "agent_definition_id": None}
    )
    assert sent == [{"name": "Q", "label_ids": [LABEL]}]


def test_facade_create_without_scope_fields_does_not_warn():
    client, sent = _capturing_facade()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        client.annotation_queues.create(
            {"name": "Q", "label_ids": [LABEL], "project": None}
        )
    assert sent == [{"name": "Q", "label_ids": [LABEL]}]
