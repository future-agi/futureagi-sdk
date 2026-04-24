from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class QueueDetail(BaseModel):
    """Annotation queue as returned by the API."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: str
    name: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    status: Optional[str] = None
    assignment_strategy: Optional[str] = None
    annotations_required: Optional[int] = None
    reservation_timeout_minutes: Optional[int] = None
    requires_review: Optional[bool] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    item_count: Optional[int] = None
    completed_count: Optional[int] = None


class QueueItem(BaseModel):
    """A single item in an annotation queue."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: str
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    status: Optional[str] = None
    order: Optional[int] = None
    assigned_to: Optional[str] = None
    created_at: Optional[str] = None


class QueueProgress(BaseModel):
    """Queue progress statistics."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    total: int = 0
    pending: int = 0
    in_progress: int = 0
    completed: int = 0
    skipped: int = 0
    progress_pct: Optional[float] = None
    annotator_stats: Optional[List[Dict[str, Any]]] = None


class QueueAnalytics(BaseModel):
    """Queue analytics data."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    throughput: Optional[Dict[str, Any]] = None
    annotator_performance: Optional[List[Dict[str, Any]]] = None
    label_distribution: Optional[Dict[str, Any]] = None
    status_breakdown: Optional[Dict[str, int]] = None
    total: Optional[int] = None


class QueueAgreement(BaseModel):
    """Inter-annotator agreement metrics."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    overall_agreement: Optional[float] = None
    per_label: Optional[List[Dict[str, Any]]] = None
    annotator_pairs: Optional[List[Dict[str, Any]]] = None


class Score(BaseModel):
    """A unified annotation score."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[str] = None
    label_id: Optional[str] = None
    label_name: Optional[str] = None
    value: Optional[Any] = None
    score_source: Optional[str] = None
    notes: Optional[str] = None
    annotator_id: Optional[str] = None
    annotator_name: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    created_at: Optional[str] = None


class AddItemsResponse(BaseModel):
    """Response from adding items to a queue."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    added: int = 0
    duplicates: int = 0
    errors: Optional[List[Dict[str, Any]]] = None


class ExportToDatasetResponse(BaseModel):
    """Response from exporting queue to dataset."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    dataset_id: Optional[str] = None
    dataset_name: Optional[str] = None
    rows_created: Optional[int] = None


class ImportAnnotationsResponse(BaseModel):
    """Response from importing annotations."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    imported: int = 0
