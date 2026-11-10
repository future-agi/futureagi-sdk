"""Offline request validation against captured server schemas."""

import inspect
import json
from pathlib import Path
from unittest.mock import Mock
from urllib.parse import parse_qs, urlencode
from uuid import UUID

import pytest
from fi.api.types import HttpMethod
from fi.datasets.dataset import Dataset
from fi.datasets.types import DatasetConfig, HuggingfaceDatasetConfig
from fi.queues.client import AnnotationQueue
from jsonschema import Draft4Validator, FormatChecker

SCHEMAS = json.loads(
    (Path(__file__).parent / "fixtures/dataset_queue_request_schemas.json").read_text()
)
BASE_URL = "https://contract.invalid"
QUEUE = "11111111-1111-4111-8111-111111111111"
ITEMS = ["22222222-2222-4222-8222-222222222222"]
USER = "33333333-3333-4333-8333-333333333333"
LABEL = "44444444-4444-4444-8444-444444444444"


def validate_body(name, body, *, strict=False):
    schema = SCHEMAS["definitions"][name]
    # These request serializers reject unknown fields even when Swagger omits
    # additionalProperties. Keep every declared schema constraint as captured.
    if strict:
        assert not set(body) - set(schema["properties"])
    Draft4Validator(
        {**schema, "definitions": SCHEMAS["definitions"]},
        format_checker=FormatChecker(),
    ).validate(body)


@pytest.fixture
def queue():
    client = object.__new__(AnnotationQueue)
    client._base_url = BASE_URL
    client.request = Mock(return_value={"assigned": 1})
    client._get_queue_id_from_name = Mock(return_value=QUEUE)
    return client


@pytest.mark.parametrize("user_options", [{"user_id": USER}, {"user_id": None}, {}])
@pytest.mark.parametrize("by_name", [False, True])
def test_assignment_replaces_or_clears_users(queue, user_options, by_name):
    identity = {"queue_name": "Example queue"} if by_name else {"queue_id": QUEUE}
    result = queue.assign_items(item_ids=ITEMS, timeout=17, **identity, **user_options)
    queue.request.assert_called_once()
    config = queue.request.call_args.args[0]
    validate_body("AssignItems", config.json, strict=True)
    users = [USER] if user_options.get("user_id") is not None else []
    assert config.json == {"item_ids": ITEMS, "user_ids": users, "action": "set"}
    assert config.method == HttpMethod.POST
    assert config.url == f"{BASE_URL}/model-hub/annotation-queues/{QUEUE}/items/assign/"
    assert config.timeout == 17
    assert result == {"assigned": 1}
    if by_name:
        queue._get_queue_id_from_name.assert_called_once_with("Example queue")
    else:
        queue._get_queue_id_from_name.assert_not_called()


def test_assignment_keeps_positional_items_and_does_not_mutate_them(queue):
    items = [*ITEMS, "55555555-5555-4555-8555-555555555555"]
    before = items.copy()
    queue.assign_items(QUEUE, items, user_id=USER)
    config = queue.request.call_args.args[0]
    validate_body("AssignItems", config.json, strict=True)
    assert config.json == {"item_ids": before, "user_ids": [USER], "action": "set"}
    assert items == before


@pytest.mark.parametrize("items", [None, []])
def test_assignment_requires_items_before_transport(queue, items):
    with pytest.raises(ValueError, match="non-empty"):
        queue.assign_items(QUEUE, items, user_id=USER)
    queue.request.assert_not_called()


def test_assignment_signature_keeps_existing_parameters():
    params = inspect.signature(AnnotationQueue.assign_items).parameters
    assert list(params) == ["self", "queue_id", "item_ids", "queue_name", "user_id", "timeout"]
    assert all(p.default is None for name, p in params.items() if name != "self")
    assert params["queue_id"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert params["item_ids"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert params["user_id"].kind is inspect.Parameter.KEYWORD_ONLY


@pytest.mark.parametrize("by_name", [False, True])
@pytest.mark.parametrize("options", [{}, {"page": 3, "page_size": 7, "status": "pending", "assigned_to": USER}])
def test_item_paging_matches_query_contract(queue, by_name, options):
    identity = {"queue_name": "Example queue"} if by_name else {"queue_id": QUEUE}
    queue.list_items(**identity, **options, timeout=19)
    config = queue.request.call_args.args[0]
    parameters = {p["name"]: p for p in SCHEMAS["item_list_query"] if p["in"] == "query"}
    assert not set(config.params) - set(parameters)
    assert config.params["page"] == options.get("page", 1)
    assert config.params["limit"] == options.get("page_size", 50)
    wire = parse_qs(urlencode(config.params, doseq=True))
    for name, values in wire.items():
        schema = {k: v for k, v in parameters[name].items() if k not in {"name", "in", "required"}}
        value = values if schema["type"] == "array" else values[0]
        if schema["type"] == "integer":
            value = int(value)
        Draft4Validator(schema).validate(value)
    if "status" in options:
        assert wire["status"] == ["pending"]
        assert wire["assigned_to"] == [USER]
    assert config.method == HttpMethod.GET
    assert config.url == f"{BASE_URL}/model-hub/annotation-queues/{QUEUE}/items/"
    assert config.timeout == 19


@pytest.mark.parametrize("auto_assign", [None, False, True])
@pytest.mark.parametrize("label", [LABEL, UUID(LABEL)])
def test_queue_creation_preserves_labels_and_auto_assignment(queue, auto_assign, label):
    queue.create("Example queue", label_ids=[label], auto_assign=auto_assign)
    body = queue.request.call_args.args[0].json
    validate_body("AnnotationQueue", body)
    expected = {"name": "Example queue", "label_ids": [LABEL]}
    if auto_assign is not None:
        expected["auto_assign"] = auto_assign
    assert body == expected


def test_queue_creation_refuses_empty_labels_before_transport(queue):
    with pytest.raises(ValueError, match="at least one"):
        queue.create("Example queue", label_ids=[])
    queue.request.assert_not_called()


@pytest.mark.parametrize(
    "options",
    [{}, {"subset": "sample", "split": "validation", "num_rows": 5}, {"subset": None}],
)
def test_huggingface_creation_uses_supported_name(options):
    dataset = object.__new__(Dataset)
    dataset._base_url = BASE_URL
    expected = DatasetConfig(name="Imported examples", model_type="GenerativeLLM")
    dataset.request_with_retry = Mock(return_value=expected)
    source = HuggingfaceDatasetConfig(name="example/data", **options)
    result = dataset._create_from_huggingface(expected, source)
    dataset.request_with_retry.assert_called_once()
    config = dataset.request_with_retry.call_args.kwargs["config"]
    validate_body("HuggingFaceDatasetCreateRequest", config.data, strict=True)
    assert config.data["name"] == expected.name
    assert config.data["model_type"] == "GenerativeLLM"
    assert config.data["huggingface_dataset_name"] == "example/data"
    assert config.data["huggingface_dataset_split"] == source.split
    if source.subset is not None:
        assert config.data["huggingface_dataset_config"] == source.subset
    else:
        assert "huggingface_dataset_config" not in config.data
    if source.num_rows is not None:
        assert config.data["num_rows"] == source.num_rows
    else:
        assert "num_rows" not in config.data
    assert config.method == HttpMethod.POST
    assert config.url == f"{BASE_URL}/model-hub/develops/create-dataset-from-huggingface/"
    assert result is expected


def test_schema_snapshot_rejects_obsolete_request_names():
    with pytest.raises(AssertionError):
        validate_body("AssignItems", {"item_ids": ITEMS, "user_id": USER}, strict=True)
    with pytest.raises(AssertionError):
        validate_body(
            "HuggingFaceDatasetCreateRequest",
            {"new_dataset_name": "Example", "huggingface_dataset_name": "example/data", "huggingface_dataset_split": "train"},
            strict=True,
        )
    assert "page_size" not in {p["name"] for p in SCHEMAS["item_list_query"]}
