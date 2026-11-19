"""Offline regression pins for the published 0.7.0 model contracts."""
import json

import pytest

from fi import BulkAnnotationResponse
from fi.gateway.types.embedding import EmbeddingResponse
from fi.gateway.types.shared import Usage
from fi.queues import types as queues


BULK = {
    "annotations_created": 1, "annotations_updated": 2, "notes_created": 3,
    "succeeded_count": 4, "errors_count": 0, "warnings_count": 0,
}
QUEUE_PAYLOADS = [
    (queues.QueueDetail, {
        "id": "q", "name": "queue", "assignment_strategy": "manual",
        "annotations_required": 0, "reservation_timeout_minutes": 1,
        "requires_review": False, "created_at": "created", "updated_at": "updated",
        "item_count": 0, "completed_count": 2,
    }),
    (queues.QueueItem, {
        "id": "i", "source_type": "trace", "source_id": "source",
        "assigned_to": "annotator", "created_at": "created",
    }),
    (queues.QueueProgress, {"in_progress": 1, "progress_pct": 0.0, "annotator_stats": []}),
    (queues.QueueAnalytics, {
        "annotator_performance": [], "label_distribution": {}, "status_breakdown": {},
    }),
    (queues.QueueAgreement, {"overall_agreement": 0.0, "per_label": [], "annotator_pairs": []}),
    (queues.Score, {
        "label_id": "label", "label_name": "Label", "score_source": "human",
        "annotator_id": "annotator", "annotator_name": "Annotator",
        "source_type": "trace", "source_id": "source", "created_at": "created",
    }),
    (queues.ExportToDatasetResponse, {
        "dataset_id": "dataset", "dataset_name": "Dataset", "rows_created": 0,
    }),
]


@pytest.mark.parametrize("by_alias", [False, True])
@pytest.mark.parametrize("format", ["dict", "json"])
def test_bulk_published_serialization(format, by_alias):
    payload = {"message": "ok", **BULK}
    model = BulkAnnotationResponse(**payload)
    expected = {**payload, "warnings": None, "errors": None}
    actual = (model.model_dump(by_alias=by_alias) if format == "dict" else
              json.loads(model.model_dump_json(by_alias=by_alias)))
    assert actual == expected


def test_bulk_published_field_metadata_and_schema():
    expected = {"message", *BULK, "warnings", "errors"}
    assert set(BulkAnnotationResponse.model_fields) == expected
    for mode in ("validation", "serialization"):
        for by_alias in (False, True):
            schema = BulkAnnotationResponse.model_json_schema(mode=mode, by_alias=by_alias)
            assert set(schema["properties"]) == expected
            assert set(schema["required"]) == {"message", *BULK}


@pytest.mark.parametrize("cls,payload", QUEUE_PAYLOADS, ids=[c.__name__ for c, _ in QUEUE_PAYLOADS])
@pytest.mark.parametrize("format", ["dict", "json"])
@pytest.mark.parametrize("by_alias", [False, True])
def test_queue_published_serialization(cls, payload, format, by_alias):
    model = cls(**payload)
    actual = (model.model_dump(by_alias=by_alias, exclude_unset=True) if format == "dict" else
              json.loads(model.model_dump_json(by_alias=by_alias, exclude_unset=True)))
    assert actual == payload
    for mode in ("validation", "serialization"):
        assert set(cls.model_json_schema(mode=mode, by_alias=by_alias)["properties"]) == set(cls.model_fields)


def test_embedding_accepts_published_usage_instance():
    usage = Usage(prompt_tokens=1, completion_tokens=0, total_tokens=1)
    response = EmbeddingResponse(data=[], model="fixture", usage=usage)
    assert response.usage is usage
    assert response.model_dump()["usage"] == usage.model_dump()


def test_embedding_dictionary_usage_still_defaults_completion_tokens():
    response = EmbeddingResponse(data=[], model="fixture", usage={"prompt_tokens": 1, "total_tokens": 1})
    assert response.usage.completion_tokens == 0


@pytest.mark.parametrize("method", ["constructor", "model_validate", "model_validate_json"])
def test_embedding_dictionary_usage_retains_embedding_type_and_extras(method):
    from fi.gateway.types.embedding import EmbeddingUsage

    payload = {"data": [], "model": "fixture", "usage": {
        "prompt_tokens": 1, "total_tokens": 1,
        "prompt_tokens_details": {"cached_tokens": 1}, "cost": 0.5,
    }}
    if method == "constructor":
        response = EmbeddingResponse(**payload)
    elif method == "model_validate":
        response = EmbeddingResponse.model_validate(payload)
    else:
        response = EmbeddingResponse.model_validate_json(json.dumps(payload))
    assert isinstance(response.usage, EmbeddingUsage)
    assert isinstance(response.usage, Usage)
    assert response.usage.completion_tokens == 0
    assert response.usage.prompt_tokens_details == {"cached_tokens": 1}
    assert response.usage.model_extra == {"cost": 0.5}
    assert response.model_dump()["usage"]["cost"] == 0.5


def test_embedding_usage_field_keeps_the_published_annotation_and_schema():
    from typing import get_args

    assert set(get_args(EmbeddingResponse.model_fields["usage"].annotation)) == {Usage, type(None)}
    schema = EmbeddingResponse.model_json_schema()
    assert schema["properties"]["usage"]["anyOf"] == [
        {"$ref": "#/$defs/Usage"}, {"type": "null"},
    ]
    assert schema["$defs"]["Usage"] == Usage.model_json_schema()


@pytest.mark.parametrize("method", ["model_validate", "model_validate_json"])
def test_embedding_usage_respects_strict_validation(method):
    from pydantic import ValidationError

    payload = {"data": [], "model": "fixture", "usage": {
        "prompt_tokens": "1", "total_tokens": 1,
    }}
    argument = json.dumps(payload) if method == "model_validate_json" else payload
    with pytest.raises(ValidationError):
        getattr(EmbeddingResponse, method)(argument, strict=True)


def test_embedding_usage_keeps_default_coercion():
    response = EmbeddingResponse(data=[], model="fixture", usage={"prompt_tokens": "1", "total_tokens": 1})
    assert response.usage.prompt_tokens == 1


def test_embedding_usage_preserves_extra_values_and_fields_set():
    marker = object()
    payload = {"prompt_tokens": 1, "total_tokens": 1, "marker": marker, "_fields_set": "server-field"}
    response = EmbeddingResponse(data=[], model="fixture", usage=payload)
    assert response.usage.model_extra == {"marker": marker, "_fields_set": "server-field"}
    assert response.usage.model_extra["marker"] is marker
    assert response.usage.model_fields_set == set(payload)
    assert "completion_tokens" not in response.usage.model_dump(exclude_unset=True)
