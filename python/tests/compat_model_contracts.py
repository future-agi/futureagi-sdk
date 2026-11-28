"""Combine legacy input pins with the published 0.7.0 field/output contract.

The 0.6.13 archive remains immutable. These explicit overrides come from the
0.7.0 annotations/types.py and queues/types.py declarations, not live models.
Legacy input and property behavior is also exercised by test_model_compat.py.
"""
import json
from pathlib import Path


BULK_FIELDS = {
    "annotationsCreated": "annotations_created",
    "annotationsUpdated": "annotations_updated",
    "notesCreated": "notes_created",
    "succeededCount": "succeeded_count",
    "errorsCount": "errors_count",
    "warningsCount": "warnings_count",
}
QUEUE_FIELDS = {
    "QueueDetail": "assignment_strategy annotations_required reservation_timeout_minutes requires_review created_at updated_at item_count completed_count",
    "QueueItem": "source_type source_id assigned_to created_at",
    "QueueProgress": "in_progress progress_pct annotator_stats",
    "QueueAnalytics": "annotator_performance label_distribution status_breakdown",
    "QueueAgreement": "overall_agreement per_label annotator_pairs",
    "Score": "label_id label_name score_source annotator_id annotator_name source_type source_id created_at",
    "ExportToDatasetResponse": "dataset_id dataset_name rows_created",
}


def load_model_contracts():
    fixture = json.loads((Path(__file__).parent / "data/compat_futureagi_0_6_13.json").read_text())
    for name, fields in QUEUE_FIELDS.items():
        spec = fixture["classes"][f"fi.queues.types.{name}"]
        for field in fields.split():
            spec["fields"][field]["output_name_by_alias"] = field
    bulk = fixture["classes"]["fi.annotations.types.BulkAnnotationResponse"]
    bulk["fields"] = {
        BULK_FIELDS.get(name, name): {**details, "output_name_by_alias": BULK_FIELDS.get(name, name)}
        for name, details in bulk["fields"].items()
    }
    # Pydantic's generated keyword-only signature follows its actual field names.
    # Construction from the old input aliases is tested at runtime separately.
    for parameter in fixture["signatures"][bulk["constructor"]]:
        parameter["name"] = BULK_FIELDS.get(parameter["name"], parameter["name"])
    fixture["model_contract_version"] = "0.7.0"
    return fixture
