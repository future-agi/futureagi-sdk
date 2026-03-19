"""Tests for fi.queues – AnnotationQueue SDK client.

Tests mock the HTTP layer (HttpClient.request) to verify:
- Correct URL construction and route formatting
- Correct HTTP method selection
- Correct request body / params assembly
- Response handler parsing (JSON → Pydantic models)
- Input validation (empty lists, missing args)
- Error status code differentiation
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from fi.api.types import HttpMethod
from fi.queues.client import (
    AnnotationQueue,
    _CsvResponseHandler,
    _DictResponseHandler,
    _QueueResponseHandler,
    _QueueListResponseHandler,
    _ItemListResponseHandler,
    _ScoreListResponseHandler,
    _ScoreResponseHandler,
    _validate_id,
)
from fi.queues.types import (
    AddItemsResponse,
    ExportToDatasetResponse,
    ImportAnnotationsResponse,
    QueueAgreement,
    QueueAnalytics,
    QueueDetail,
    QueueItem,
    QueueProgress,
    Score,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_response(data, status_code=200):
    """Build a mock requests.Response."""
    from requests import Response
    resp = MagicMock(spec=Response)
    resp.ok = 200 <= status_code < 300
    resp.status_code = status_code
    resp.json.return_value = data
    resp.text = json.dumps(data) if not isinstance(data, str) else data
    return resp


def _wrapped(result):
    """Wrap result in the backend's standard envelope."""
    return {"status": "success", "result": result}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Create an AnnotationQueue client with mocked auth."""
    with patch.dict("os.environ", {"FI_API_KEY": "test-key", "FI_SECRET_KEY": "test-secret"}):
        c = AnnotationQueue()
    return c


@pytest.fixture
def mock_request(client):
    """Patch the client's request method to capture calls."""
    with patch.object(client, "request") as m:
        yield m


# ===========================================================================
# ID Validation Tests
# ===========================================================================

class TestIdValidation:

    def test_valid_uuid(self):
        _validate_id("abc-123-def", "queue_id")

    def test_valid_alphanumeric(self):
        _validate_id("abc_123", "queue_id")

    def test_rejects_empty(self):
        with pytest.raises(ValueError, match="Invalid queue_id"):
            _validate_id("", "queue_id")

    def test_rejects_path_traversal(self):
        with pytest.raises(ValueError, match="Invalid queue_id"):
            _validate_id("../../admin", "queue_id")

    def test_rejects_slash(self):
        with pytest.raises(ValueError, match="Invalid item_id"):
            _validate_id("abc/def", "item_id")


# ===========================================================================
# Response Handler Tests
# ===========================================================================

class TestResponseHandlers:

    def test_queue_response_handler_parses_wrapped(self):
        resp = _mock_response(_wrapped({"id": "q1", "name": "Test Queue", "status": "draft"}))
        result = _QueueResponseHandler.parse(resp)
        assert isinstance(result, QueueDetail)
        assert result.id == "q1"
        assert result.name == "Test Queue"

    def test_queue_response_handler_parses_flat(self):
        resp = _mock_response({"id": "q2", "name": "Flat"})
        result = _QueueResponseHandler.parse(resp)
        assert isinstance(result, QueueDetail)
        assert result.id == "q2"

    def test_queue_response_handler_raises_on_invalid_data(self):
        resp = _mock_response(_wrapped({"not_a_queue": True}))
        with pytest.raises(Exception):
            _QueueResponseHandler.parse(resp)

    def test_queue_list_handler_parses_results(self):
        resp = _mock_response(_wrapped({"results": [
            {"id": "q1", "name": "A"},
            {"id": "q2", "name": "B"},
        ]}))
        result = _QueueListResponseHandler.parse(resp)
        assert len(result) == 2
        assert all(isinstance(q, QueueDetail) for q in result)

    def test_queue_list_handler_parses_flat_list(self):
        resp = _mock_response(_wrapped([{"id": "q1", "name": "A"}]))
        result = _QueueListResponseHandler.parse(resp)
        assert len(result) == 1

    def test_item_list_handler(self):
        resp = _mock_response(_wrapped({"results": [
            {"id": "i1", "sourceType": "trace", "sourceId": "t1", "status": "pending"},
        ]}))
        result = _ItemListResponseHandler.parse(resp)
        assert len(result) == 1
        assert isinstance(result[0], QueueItem)
        assert result[0].source_type == "trace"

    def test_score_list_handler(self):
        resp = _mock_response(_wrapped([
            {"id": "s1", "labelName": "Sentiment", "value": "positive", "scoreSource": "human"},
        ]))
        result = _ScoreListResponseHandler.parse(resp)
        assert len(result) == 1
        assert isinstance(result[0], Score)
        assert result[0].label_name == "Sentiment"
        assert result[0].score_source == "human"

    def test_score_response_handler(self):
        resp = _mock_response(_wrapped({
            "id": "s1", "labelName": "Quality", "value": 4.5, "scoreSource": "api",
        }))
        result = _ScoreResponseHandler.parse(resp)
        assert isinstance(result, Score)
        assert result.value == 4.5

    def test_dict_response_handler(self):
        resp = _mock_response(_wrapped({"added": 3, "duplicates": 1}))
        result = _DictResponseHandler.parse(resp)
        assert result == {"added": 3, "duplicates": 1}

    def test_csv_response_handler(self):
        resp = _mock_response("id,label,value\ni1,Sentiment,positive\n")
        resp.text = "id,label,value\ni1,Sentiment,positive\n"
        result = _CsvResponseHandler.parse(resp)
        assert isinstance(result, str)
        assert "Sentiment" in result

    def test_error_handler_raises_on_401(self):
        resp = _mock_response({"message": "Unauthorized"}, status_code=401)
        from fi.utils.errors import InvalidAuthError
        with pytest.raises(InvalidAuthError):
            _DictResponseHandler.parse(resp)

    def test_error_handler_raises_on_403(self):
        resp = _mock_response({"message": "Forbidden"}, status_code=403)
        from fi.utils.errors import InvalidAuthError
        with pytest.raises(InvalidAuthError):
            _DictResponseHandler.parse(resp)

    def test_error_handler_raises_on_400(self):
        resp = _mock_response({"message": "Bad request"}, status_code=400)
        from fi.utils.errors import SDKException
        with pytest.raises(SDKException, match="Bad request"):
            _DictResponseHandler.parse(resp)

    def test_error_handler_raises_on_429(self):
        resp = _mock_response({"message": "Too many requests"}, status_code=429)
        from fi.utils.errors import RateLimitError
        with pytest.raises(RateLimitError):
            _DictResponseHandler.parse(resp)

    def test_error_handler_raises_on_503(self):
        resp = _mock_response({"message": "Service unavailable"}, status_code=503)
        from fi.utils.errors import ServiceUnavailableError
        with pytest.raises(ServiceUnavailableError):
            _DictResponseHandler.parse(resp)

    def test_error_handler_raises_on_500(self):
        resp = _mock_response({"message": "Internal error"}, status_code=500)
        from fi.utils.errors import ServerError
        with pytest.raises(ServerError):
            _DictResponseHandler.parse(resp)

    def test_error_handler_fallback_message(self):
        """PY-13: _raise_for_status should not produce None messages."""
        resp = _mock_response({}, status_code=418)
        resp.json.side_effect = ValueError("not json")
        from fi.utils.errors import SDKException
        with pytest.raises(SDKException, match="HTTP 418"):
            _DictResponseHandler.parse(resp)


# ===========================================================================
# Queue CRUD Tests
# ===========================================================================

class TestQueueCRUD:

    def test_create(self, client, mock_request):
        mock_request.return_value = QueueDetail(id="q1", name="Test")
        result = client.create(
            name="Test",
            description="A test queue",
            instructions="Rate quality",
            assignment_strategy="round_robin",
            annotations_required=2,
        )
        mock_request.assert_called_once()
        config = mock_request.call_args[0][0]
        assert config.method == HttpMethod.POST
        assert "annotation-queues/" in config.url
        assert config.json["name"] == "Test"
        assert config.json["description"] == "A test queue"
        assert config.json["assignment_strategy"] == "round_robin"
        assert config.json["annotations_required"] == 2
        assert result.id == "q1"

    def test_create_minimal(self, client, mock_request):
        mock_request.return_value = QueueDetail(id="q2", name="Min")
        client.create(name="Min")
        config = mock_request.call_args[0][0]
        assert config.json == {"name": "Min"}

    def test_list_queues(self, client, mock_request):
        mock_request.return_value = [QueueDetail(id="q1", name="A")]
        result = client.list_queues(status="active", search="test")
        config = mock_request.call_args[0][0]
        assert config.method == HttpMethod.GET
        assert config.params["status"] == "active"
        assert config.params["search"] == "test"
        assert len(result) == 1

    def test_get(self, client, mock_request):
        mock_request.return_value = QueueDetail(id="q1", name="A")
        result = client.get("q1")
        config = mock_request.call_args[0][0]
        assert config.method == HttpMethod.GET
        assert "q1" in config.url

    def test_get_rejects_path_traversal(self, client):
        with pytest.raises(ValueError, match="Invalid queue_id"):
            client.get("../../admin")

    def test_update(self, client, mock_request):
        mock_request.return_value = QueueDetail(id="q1", name="Updated")
        client.update("q1", name="Updated", instructions="New instructions")
        config = mock_request.call_args[0][0]
        assert config.method == HttpMethod.PATCH
        assert config.json["name"] == "Updated"
        assert config.json["instructions"] == "New instructions"

    def test_update_omits_none_fields(self, client, mock_request):
        mock_request.return_value = QueueDetail(id="q1", name="Same")
        client.update("q1", name="Same")
        config = mock_request.call_args[0][0]
        assert config.json == {"name": "Same"}

    def test_delete(self, client, mock_request):
        mock_request.return_value = {"deleted": True}
        client.delete("q1")
        config = mock_request.call_args[0][0]
        assert config.method == HttpMethod.DELETE
        assert "q1" in config.url


# ===========================================================================
# Queue Lifecycle Tests
# ===========================================================================

class TestQueueLifecycle:

    def test_activate(self, client, mock_request):
        mock_request.return_value = QueueDetail(id="q1", name="A", status="active")
        result = client.activate("q1")
        config = mock_request.call_args[0][0]
        assert config.method == HttpMethod.POST
        assert "update-status" in config.url
        assert config.json == {"status": "active"}

    def test_complete_queue(self, client, mock_request):
        mock_request.return_value = QueueDetail(id="q1", name="A", status="completed")
        result = client.complete_queue("q1")
        config = mock_request.call_args[0][0]
        assert config.json == {"status": "completed"}


# ===========================================================================
# Label Tests
# ===========================================================================

class TestLabels:

    def test_add_label(self, client, mock_request):
        mock_request.return_value = {"label": {"id": "lbl1"}, "created": True}
        client.add_label("q1", "lbl1")
        config = mock_request.call_args[0][0]
        assert config.method == HttpMethod.POST
        assert "add-label" in config.url
        assert config.json == {"label_id": "lbl1"}

    def test_remove_label(self, client, mock_request):
        mock_request.return_value = {"removed": True}
        client.remove_label("q1", "lbl1")
        config = mock_request.call_args[0][0]
        assert "remove-label" in config.url
        assert config.json == {"label_id": "lbl1"}


# ===========================================================================
# Items Tests
# ===========================================================================

class TestItems:

    def test_add_items(self, client, mock_request):
        mock_request.return_value = {"added": 3, "duplicates": 0}
        result = client.add_items("q1", items=[
            {"source_type": "trace", "source_id": "t1"},
            {"source_type": "trace", "source_id": "t2"},
            {"source_type": "dataset_row", "source_id": "r1"},
        ])
        config = mock_request.call_args[0][0]
        assert config.method == HttpMethod.POST
        assert "add-items" in config.url
        assert len(config.json["items"]) == 3
        assert isinstance(result, AddItemsResponse)
        assert result.added == 3

    def test_add_items_empty_raises(self, client):
        with pytest.raises(ValueError, match="non-empty"):
            client.add_items("q1", items=[])

    def test_list_items(self, client, mock_request):
        mock_request.return_value = [QueueItem(id="i1", status="pending")]
        result = client.list_items("q1", status="pending", page=2, page_size=10)
        config = mock_request.call_args[0][0]
        assert config.method == HttpMethod.GET
        assert config.params["status"] == "pending"
        assert config.params["page"] == 2
        assert config.params["page_size"] == 10

    def test_remove_items(self, client, mock_request):
        mock_request.return_value = {"removed": 2}
        client.remove_items("q1", item_ids=["i1", "i2"])
        config = mock_request.call_args[0][0]
        assert config.method == HttpMethod.POST
        assert "bulk-remove" in config.url
        assert config.json == {"item_ids": ["i1", "i2"]}

    def test_remove_items_empty_raises(self, client):
        with pytest.raises(ValueError, match="non-empty"):
            client.remove_items("q1", item_ids=[])

    def test_assign_items(self, client, mock_request):
        mock_request.return_value = {"assigned": 2}
        client.assign_items("q1", item_ids=["i1", "i2"], user_id="u1")
        config = mock_request.call_args[0][0]
        assert config.method == HttpMethod.POST
        assert "assign" in config.url
        assert config.json["user_id"] == "u1"

    def test_unassign_items(self, client, mock_request):
        mock_request.return_value = {"assigned": 1}
        client.assign_items("q1", item_ids=["i1"], user_id=None)
        config = mock_request.call_args[0][0]
        assert config.json["user_id"] is None


# ===========================================================================
# Annotation Submission Tests
# ===========================================================================

class TestAnnotations:

    def test_import_annotations(self, client, mock_request):
        mock_request.return_value = {"imported": 2}
        result = client.import_annotations("q1", "item1", annotations=[
            {"label_id": "lbl1", "value": "positive"},
            {"label_id": "lbl2", "value": 4.5},
        ])
        config = mock_request.call_args[0][0]
        assert config.method == HttpMethod.POST
        assert "import" in config.url
        assert "q1" in config.url
        assert "item1" in config.url
        assert len(config.json["annotations"]) == 2
        assert isinstance(result, ImportAnnotationsResponse)
        assert result.imported == 2

    def test_import_annotations_with_annotator(self, client, mock_request):
        mock_request.return_value = {"imported": 1}
        client.import_annotations("q1", "item1",
            annotations=[{"label_id": "lbl1", "value": "good"}],
            annotator_id="user123",
        )
        config = mock_request.call_args[0][0]
        assert config.json["annotator_id"] == "user123"

    def test_import_annotations_empty_raises(self, client):
        with pytest.raises(ValueError, match="non-empty"):
            client.import_annotations("q1", "item1", annotations=[])

    def test_submit_annotations(self, client, mock_request):
        mock_request.return_value = {"submitted": 1}
        client.submit_annotations("q1", "item1",
            annotations=[{"label_id": "lbl1", "value": "good"}],
            notes="Looks fine",
        )
        config = mock_request.call_args[0][0]
        assert config.method == HttpMethod.POST
        assert "submit" in config.url
        assert config.json["notes"] == "Looks fine"

    def test_submit_annotations_empty_raises(self, client):
        with pytest.raises(ValueError, match="non-empty"):
            client.submit_annotations("q1", "item1", annotations=[])

    def test_get_annotations(self, client, mock_request):
        mock_request.return_value = [Score(id="s1", label_name="Q", value="good")]
        result = client.get_annotations("q1", "item1")
        config = mock_request.call_args[0][0]
        assert config.method == HttpMethod.GET
        assert "annotations" in config.url
        assert len(result) == 1

    def test_complete_item(self, client, mock_request):
        mock_request.return_value = {"completed_item_id": "item1", "next_item": None}
        result = client.complete_item("q1", "item1")
        config = mock_request.call_args[0][0]
        assert config.method == HttpMethod.POST
        assert "complete" in config.url

    def test_skip_item(self, client, mock_request):
        mock_request.return_value = {"skipped_item_id": "item1", "next_item": None}
        result = client.skip_item("q1", "item1")
        config = mock_request.call_args[0][0]
        assert "skip" in config.url


# ===========================================================================
# Scores Tests
# ===========================================================================

class TestScores:

    def test_create_score(self, client, mock_request):
        mock_request.return_value = Score(id="s1", value="positive", score_source="api")
        result = client.create_score(
            source_type="trace",
            source_id="t1",
            label_id="lbl1",
            value="positive",
            notes="API generated",
        )
        config = mock_request.call_args[0][0]
        assert config.method == HttpMethod.POST
        assert "scores/" in config.url
        assert config.json["source_type"] == "trace"
        assert config.json["source_id"] == "t1"
        assert config.json["label_id"] == "lbl1"
        assert config.json["value"] == "positive"
        assert config.json["score_source"] == "api"
        assert config.json["notes"] == "API generated"
        assert isinstance(result, Score)

    def test_create_score_default_source(self, client, mock_request):
        mock_request.return_value = Score(id="s1", value=True)
        client.create_score("trace", "t1", "lbl1", True)
        config = mock_request.call_args[0][0]
        assert config.json["score_source"] == "api"

    def test_create_scores_bulk(self, client, mock_request):
        mock_request.return_value = {"scores": [{"id": "s1"}, {"id": "s2"}]}
        result = client.create_scores(
            source_type="observation_span",
            source_id="os1",
            scores=[
                {"label_id": "lbl1", "value": "good"},
                {"label_id": "lbl2", "value": 4.0},
            ],
            notes="Batch import",
        )
        config = mock_request.call_args[0][0]
        assert config.method == HttpMethod.POST
        assert "scores/bulk/" in config.url
        assert len(config.json["scores"]) == 2
        assert config.json["notes"] == "Batch import"

    def test_create_scores_empty_raises(self, client):
        with pytest.raises(ValueError, match="non-empty"):
            client.create_scores("trace", "t1", scores=[])

    def test_get_scores(self, client, mock_request):
        mock_request.return_value = [
            Score(id="s1", label_name="Sentiment", value="positive"),
            Score(id="s2", label_name="Quality", value=4.5),
        ]
        result = client.get_scores("trace", "t1")
        config = mock_request.call_args[0][0]
        assert config.method == HttpMethod.GET
        assert "for-source" in config.url
        assert config.params["source_type"] == "trace"
        assert config.params["source_id"] == "t1"
        assert len(result) == 2


# ===========================================================================
# Progress & Analytics Tests
# ===========================================================================

class TestAnalytics:

    def test_get_progress(self, client, mock_request):
        mock_request.return_value = {
            "total": 100, "pending": 30, "inProgress": 20,
            "completed": 45, "skipped": 5, "progressPct": 45.0,
        }
        result = client.get_progress("q1")
        config = mock_request.call_args[0][0]
        assert config.method == HttpMethod.GET
        assert "progress" in config.url
        assert isinstance(result, QueueProgress)
        assert result.total == 100
        assert result.completed == 45
        assert result.in_progress == 20
        assert result.progress_pct == 45.0

    def test_get_analytics(self, client, mock_request):
        mock_request.return_value = {
            "throughput": [{"date": "2025-01-01", "count": 10}],
            "annotatorPerformance": [{"annotatorName": "Alice", "completed": 50}],
            "labelDistribution": {"positive": 30, "negative": 20},
            "statusBreakdown": {"completed": 45, "pending": 30},
            "total": 100,
        }
        result = client.get_analytics("q1")
        assert isinstance(result, QueueAnalytics)
        assert result.total == 100
        assert len(result.throughput) == 1
        assert result.label_distribution["positive"] == 30

    def test_get_agreement(self, client, mock_request):
        mock_request.return_value = {
            "overallAgreement": 85.5,
            "perLabel": [{"labelName": "Sentiment", "agreementPct": 90.0, "cohensKappa": 0.82}],
            "annotatorPairs": [],
        }
        result = client.get_agreement("q1")
        assert isinstance(result, QueueAgreement)
        assert result.overall_agreement == 85.5
        assert len(result.per_label) == 1


# ===========================================================================
# Export Tests
# ===========================================================================

class TestExport:

    def test_export_json(self, client, mock_request):
        mock_request.return_value = [{"item_id": "i1", "annotations": []}]
        result = client.export("q1", export_format="json", status="completed")
        config = mock_request.call_args[0][0]
        assert config.method == HttpMethod.GET
        assert "export" in config.url
        assert config.params["format"] == "json"
        assert config.params["status"] == "completed"

    def test_export_csv(self, client, mock_request):
        csv_text = "id,label,value\ni1,Sentiment,positive\n"
        mock_request.return_value = csv_text
        result = client.export("q1", export_format="csv")
        assert isinstance(result, str)
        assert result == csv_text

    def test_export_to_dataset_with_name(self, client, mock_request):
        mock_request.return_value = {"datasetId": "d1", "datasetName": "Curated", "rowsCreated": 42}
        result = client.export_to_dataset("q1", dataset_name="Curated")
        config = mock_request.call_args[0][0]
        assert config.method == HttpMethod.POST
        assert "export-to-dataset" in config.url
        assert config.json["dataset_name"] == "Curated"
        assert isinstance(result, ExportToDatasetResponse)
        assert result.rows_created == 42

    def test_export_to_dataset_with_id(self, client, mock_request):
        mock_request.return_value = {"datasetId": "d1", "rowsCreated": 10}
        client.export_to_dataset("q1", dataset_id="d1", status_filter="completed")
        config = mock_request.call_args[0][0]
        assert config.json["dataset_id"] == "d1"
        assert config.json["status_filter"] == "completed"

    def test_export_to_dataset_missing_args_raises(self, client):
        with pytest.raises(ValueError, match="dataset_name or dataset_id"):
            client.export_to_dataset("q1")

    def test_export_to_dataset_both_args_raises(self, client):
        """PY-14: Mutual exclusion — both dataset_name AND dataset_id."""
        with pytest.raises(ValueError, match="not both"):
            client.export_to_dataset("q1", dataset_name="New", dataset_id="d1")


# ===========================================================================
# URL Construction Tests
# ===========================================================================

class TestURLConstruction:
    """Verify that queue_id and item_id are correctly interpolated into URLs."""

    def test_queue_detail_url(self, client, mock_request):
        mock_request.return_value = QueueDetail(id="abc-123", name="A")
        client.get("abc-123")
        url = mock_request.call_args[0][0].url
        assert "annotation-queues/abc-123/" in url

    def test_item_annotations_url(self, client, mock_request):
        mock_request.return_value = [Score(id="s1")]
        client.get_annotations("q-id", "item-id")
        url = mock_request.call_args[0][0].url
        assert "q-id/items/item-id/annotations/" in url

    def test_import_url(self, client, mock_request):
        mock_request.return_value = {"imported": 0}
        client.import_annotations("q-id", "item-id", [{"label_id": "l1", "value": "x"}])
        url = mock_request.call_args[0][0].url
        assert "q-id/items/item-id/annotations/import/" in url

    def test_complete_item_url(self, client, mock_request):
        mock_request.return_value = {}
        client.complete_item("q-id", "item-id")
        url = mock_request.call_args[0][0].url
        assert "q-id/items/item-id/complete/" in url

    def test_progress_url(self, client, mock_request):
        mock_request.return_value = {"total": 0}
        client.get_progress("q-id")
        url = mock_request.call_args[0][0].url
        assert "annotation-queues/q-id/progress/" in url

    def test_scores_for_source_url(self, client, mock_request):
        mock_request.return_value = []
        client.get_scores("trace", "t1")
        url = mock_request.call_args[0][0].url
        assert "scores/for-source/" in url
