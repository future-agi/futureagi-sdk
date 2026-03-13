from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class QueueDetail(BaseModel):
    """Annotation queue as returned by the API."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: str
    name: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    status: Optional[str] = None
    assignment_strategy: Optional[str] = Field(None, alias="assignmentStrategy")
    annotations_required: Optional[int] = Field(None, alias="annotationsRequired")
    reservation_timeout_minutes: Optional[int] = Field(None, alias="reservationTimeoutMinutes")
    requires_review: Optional[bool] = Field(None, alias="requiresReview")
    created_at: Optional[str] = Field(None, alias="createdAt")
    updated_at: Optional[str] = Field(None, alias="updatedAt")
    item_count: Optional[int] = Field(None, alias="itemCount")
    completed_count: Optional[int] = Field(None, alias="completedCount")


class QueueItem(BaseModel):
    """A single item in an annotation queue."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: str
    source_type: Optional[str] = Field(None, alias="sourceType")
    source_id: Optional[str] = Field(None, alias="sourceId")
    status: Optional[str] = None
    order: Optional[int] = None
    assigned_to: Optional[str] = Field(None, alias="assignedTo")
    created_at: Optional[str] = Field(None, alias="createdAt")


class QueueProgress(BaseModel):
    """Queue progress statistics."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    total: int = 0
    pending: int = 0
    in_progress: int = Field(0, alias="inProgress")
    completed: int = 0
    skipped: int = 0
    progress_pct: Optional[float] = Field(None, alias="progressPct")
    annotator_stats: Optional[List[Dict[str, Any]]] = Field(None, alias="annotatorStats")


class QueueAnalytics(BaseModel):
    """Queue analytics data."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    throughput: Optional[List[Dict[str, Any]]] = None
    annotator_performance: Optional[List[Dict[str, Any]]] = Field(None, alias="annotatorPerformance")
    label_distribution: Optional[Dict[str, Any]] = Field(None, alias="labelDistribution")
    status_breakdown: Optional[Dict[str, int]] = Field(None, alias="statusBreakdown")
    total: Optional[int] = None


class QueueAgreement(BaseModel):
    """Inter-annotator agreement metrics."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    overall_agreement: Optional[float] = Field(None, alias="overallAgreement")
    per_label: Optional[List[Dict[str, Any]]] = Field(None, alias="perLabel")
    annotator_pairs: Optional[List[Dict[str, Any]]] = Field(None, alias="annotatorPairs")


class Score(BaseModel):
    """A unified annotation score."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[str] = None
    label_id: Optional[str] = Field(None, alias="labelId")
    label_name: Optional[str] = Field(None, alias="labelName")
    value: Optional[Any] = None
    score_source: Optional[str] = Field(None, alias="scoreSource")
    notes: Optional[str] = None
    annotator_id: Optional[str] = Field(None, alias="annotatorId")
    annotator_name: Optional[str] = Field(None, alias="annotatorName")
    source_type: Optional[str] = Field(None, alias="sourceType")
    source_id: Optional[str] = Field(None, alias="sourceId")
    created_at: Optional[str] = Field(None, alias="createdAt")


class AddItemsResponse(BaseModel):
    """Response from adding items to a queue."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    added: int = 0
    duplicates: int = 0
    errors: Optional[List[Dict[str, Any]]] = None


class ExportToDatasetResponse(BaseModel):
    """Response from exporting queue to dataset."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    dataset_id: Optional[str] = Field(None, alias="datasetId")
    dataset_name: Optional[str] = Field(None, alias="datasetName")
    rows_created: Optional[int] = Field(None, alias="rowsCreated")


class ImportAnnotationsResponse(BaseModel):
    """Response from importing annotations."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    imported: int = 0
