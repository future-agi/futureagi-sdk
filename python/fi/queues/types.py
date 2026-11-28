from typing import Any, Dict, List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from fi._compat_fields import LegacyFieldsModel as _LegacyFieldsModel


class QueueDetail(_LegacyFieldsModel):
    """Annotation queue as returned by the API.

    Legacy camelCase inputs warn once per alias per process; unknown fields survive.
    Default and by_alias dumps retain the published 0.7.0 snake_case names.
    """

    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    status: Optional[str] = None
    assignment_strategy: Optional[str] = Field(None, validation_alias=AliasChoices("assignment_strategy", "assignmentStrategy"))
    annotations_required: Optional[int] = Field(None, validation_alias=AliasChoices("annotations_required", "annotationsRequired"))
    reservation_timeout_minutes: Optional[int] = Field(None, validation_alias=AliasChoices("reservation_timeout_minutes", "reservationTimeoutMinutes"))
    requires_review: Optional[bool] = Field(None, validation_alias=AliasChoices("requires_review", "requiresReview"))
    is_default: Optional[bool] = None
    created_at: Optional[str] = Field(None, validation_alias=AliasChoices("created_at", "createdAt"))
    updated_at: Optional[str] = Field(None, validation_alias=AliasChoices("updated_at", "updatedAt"))
    item_count: Optional[int] = Field(None, validation_alias=AliasChoices("item_count", "itemCount"))
    completed_count: Optional[int] = Field(None, validation_alias=AliasChoices("completed_count", "completedCount"))


class DefaultQueue(BaseModel):
    """The default queue of a project, dataset or agent definition (``get_or_create_default``)."""

    model_config = ConfigDict(extra="allow")

    queue: QueueDetail
    #: The queue's labels: id, name, type, settings, description, allow_notes, required, order.
    labels: List[Dict[str, Any]] = Field(default_factory=list)
    #: True only when this call created the queue.
    created: bool = False
    #: ``"created"``, ``"restored"`` (an archived default queue came back) or ``"fetched"``.
    action: Optional[str] = None


class QueueItem(_LegacyFieldsModel):
    """A queue item accepting legacy inputs and retaining 0.7.0 output names."""

    model_config = ConfigDict(extra="allow")

    id: str
    source_type: Optional[str] = Field(None, validation_alias=AliasChoices("source_type", "sourceType"))
    source_id: Optional[str] = Field(None, validation_alias=AliasChoices("source_id", "sourceId"))
    status: Optional[str] = None
    order: Optional[int] = None
    assigned_to: Optional[str] = Field(None, validation_alias=AliasChoices("assigned_to", "assignedTo"))
    created_at: Optional[str] = Field(None, validation_alias=AliasChoices("created_at", "createdAt"))


class QueueProgress(_LegacyFieldsModel):
    """Queue progress accepting legacy inputs and retaining 0.7.0 output names."""

    model_config = ConfigDict(extra="allow")

    total: int = 0
    pending: int = 0
    in_progress: int = Field(0, validation_alias=AliasChoices("in_progress", "inProgress"))
    completed: int = 0
    skipped: int = 0
    progress_pct: Optional[float] = Field(None, validation_alias=AliasChoices("progress_pct", "progressPct"))
    annotator_stats: Optional[List[Dict[str, Any]]] = Field(None, validation_alias=AliasChoices("annotator_stats", "annotatorStats"))


class QueueAnalytics(_LegacyFieldsModel):
    """Queue analytics accepting legacy inputs and retaining 0.7.0 output names."""

    model_config = ConfigDict(extra="allow")

    throughput: Optional[Dict[str, Any]] = None
    annotator_performance: Optional[List[Dict[str, Any]]] = Field(None, validation_alias=AliasChoices("annotator_performance", "annotatorPerformance"))
    label_distribution: Optional[Dict[str, Any]] = Field(None, validation_alias=AliasChoices("label_distribution", "labelDistribution"))
    status_breakdown: Optional[Dict[str, int]] = Field(None, validation_alias=AliasChoices("status_breakdown", "statusBreakdown"))
    total: Optional[int] = None


class QueueAgreement(_LegacyFieldsModel):
    """Agreement metrics accepting legacy inputs and retaining 0.7.0 output names."""

    model_config = ConfigDict(extra="allow")

    overall_agreement: Optional[float] = Field(None, validation_alias=AliasChoices("overall_agreement", "overallAgreement"))
    per_label: Optional[List[Dict[str, Any]]] = Field(None, validation_alias=AliasChoices("per_label", "perLabel"))
    annotator_pairs: Optional[List[Dict[str, Any]]] = Field(None, validation_alias=AliasChoices("annotator_pairs", "annotatorPairs"))


class Score(_LegacyFieldsModel):
    """A score accepting legacy inputs and retaining 0.7.0 output names."""

    model_config = ConfigDict(extra="allow")

    id: Optional[str] = None
    label_id: Optional[str] = Field(None, validation_alias=AliasChoices("label_id", "labelId"))
    label_name: Optional[str] = Field(None, validation_alias=AliasChoices("label_name", "labelName"))
    value: Optional[Any] = None
    score_source: Optional[str] = Field(None, validation_alias=AliasChoices("score_source", "scoreSource"))
    notes: Optional[str] = None
    annotator_id: Optional[str] = Field(None, validation_alias=AliasChoices("annotator_id", "annotatorId"))
    annotator_name: Optional[str] = Field(None, validation_alias=AliasChoices("annotator_name", "annotatorName"))
    source_type: Optional[str] = Field(None, validation_alias=AliasChoices("source_type", "sourceType"))
    source_id: Optional[str] = Field(None, validation_alias=AliasChoices("source_id", "sourceId"))
    created_at: Optional[str] = Field(None, validation_alias=AliasChoices("created_at", "createdAt"))


class AddItemsResponse(BaseModel):
    """Response from adding items to a queue."""

    model_config = ConfigDict(extra="allow")

    added: int = 0
    duplicates: int = 0
    errors: Optional[List[Dict[str, Any]]] = None


class ExportToDatasetResponse(_LegacyFieldsModel):
    """Export result accepting legacy inputs and retaining 0.7.0 output names."""

    model_config = ConfigDict(extra="allow")

    dataset_id: Optional[str] = Field(None, validation_alias=AliasChoices("dataset_id", "datasetId"))
    dataset_name: Optional[str] = Field(None, validation_alias=AliasChoices("dataset_name", "datasetName"))
    rows_created: Optional[int] = Field(None, validation_alias=AliasChoices("rows_created", "rowsCreated"))


class ImportAnnotationsResponse(BaseModel):
    """Response from importing annotations."""

    model_config = ConfigDict(extra="allow")

    imported: int = 0
