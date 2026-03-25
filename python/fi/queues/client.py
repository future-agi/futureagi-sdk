import re
from typing import Any, Dict, List, Optional, Union

from requests import Response

from fi.api.auth import APIKeyAuth, ResponseHandler
from fi.api.types import HttpMethod, RequestConfig
from fi.annotations.types import AnnotationLabel
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
from fi.utils.errors import (
    InvalidAuthError,
    RateLimitError,
    SDKException,
    ServerError,
    ServiceUnavailableError,
)
from fi.utils.logging import logger
from fi.utils.routes import Routes


# ---------------------------------------------------------------------------
# ID validation
# ---------------------------------------------------------------------------

_SAFE_ID_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")


def _validate_id(value: str, name: str = "id") -> None:
    """Validate that an ID is safe for URL interpolation."""
    if not value or not _SAFE_ID_RE.match(value):
        raise ValueError(
            f"Invalid {name}: {value!r}. "
            "Must be non-empty and contain only alphanumeric characters, hyphens, or underscores."
        )


# ---------------------------------------------------------------------------
# Response handlers
# ---------------------------------------------------------------------------

class _QueueResponseHandler(ResponseHandler[Dict[str, Any], QueueDetail]):
    """Handles single-queue responses."""

    @classmethod
    def _parse_success(cls, response: Response) -> QueueDetail:
        data = response.json()
        if isinstance(data, dict) and "result" in data:
            data = data["result"]
        return QueueDetail(**data)

    @classmethod
    def _handle_error(cls, response: Response) -> None:
        _raise_for_status(response)


class _QueueListResponseHandler(ResponseHandler[Dict[str, Any], List[QueueDetail]]):
    """Handles list-queues responses."""

    @classmethod
    def _parse_success(cls, response: Response) -> List[QueueDetail]:
        data = response.json()
        if isinstance(data, dict) and "result" in data:
            data = data["result"]
        items = data if isinstance(data, list) else data.get("results", data.get("table", []))
        return [QueueDetail(**q) for q in items]

    @classmethod
    def _handle_error(cls, response: Response) -> None:
        _raise_for_status(response)


class _DictResponseHandler(ResponseHandler[Dict[str, Any], Dict[str, Any]]):
    """Generic handler that returns unwrapped result dict."""

    @classmethod
    def _parse_success(cls, response: Response) -> Dict[str, Any]:
        data = response.json()
        if isinstance(data, dict) and "result" in data:
            return data["result"]
        return data

    @classmethod
    def _handle_error(cls, response: Response) -> None:
        _raise_for_status(response)


class _ItemListResponseHandler(ResponseHandler[Dict[str, Any], List[QueueItem]]):

    @classmethod
    def _parse_success(cls, response: Response) -> List[QueueItem]:
        data = response.json()
        if isinstance(data, dict) and "result" in data:
            data = data["result"]
        items = data if isinstance(data, list) else data.get("results", [])
        return [QueueItem(**i) for i in items]

    @classmethod
    def _handle_error(cls, response: Response) -> None:
        _raise_for_status(response)


class _ScoreListResponseHandler(ResponseHandler[Dict[str, Any], List[Score]]):

    @classmethod
    def _parse_success(cls, response: Response) -> List[Score]:
        data = response.json()
        if isinstance(data, dict) and "result" in data:
            data = data["result"]
        items = data if isinstance(data, list) else data.get("results", [])
        return [Score(**s) for s in items]

    @classmethod
    def _handle_error(cls, response: Response) -> None:
        _raise_for_status(response)


class _ScoreResponseHandler(ResponseHandler[Dict[str, Any], Score]):

    @classmethod
    def _parse_success(cls, response: Response) -> Score:
        data = response.json()
        if isinstance(data, dict) and "result" in data:
            data = data["result"]
        return Score(**data)

    @classmethod
    def _handle_error(cls, response: Response) -> None:
        _raise_for_status(response)


class _CsvResponseHandler(ResponseHandler[Dict[str, Any], str]):
    """Handler for CSV export — returns raw text and raises on errors."""

    @classmethod
    def _parse_success(cls, response: Response) -> str:
        return response.text

    @classmethod
    def _handle_error(cls, response: Response) -> None:
        _raise_for_status(response)


class _LabelResponseHandler(ResponseHandler[Dict[str, Any], AnnotationLabel]):
    """Handles single annotation-label responses."""

    @classmethod
    def _parse_success(cls, response: Response) -> AnnotationLabel:
        data = response.json()
        if isinstance(data, dict) and "data" in data:
            data = data["data"]
        elif isinstance(data, dict) and "result" in data:
            data = data["result"]
        return AnnotationLabel(**data)

    @classmethod
    def _handle_error(cls, response: Response) -> None:
        _raise_for_status(response)


class _LabelListResponseHandler(ResponseHandler[Dict[str, Any], List[AnnotationLabel]]):
    """Handles list annotation-label responses."""

    @classmethod
    def _parse_success(cls, response: Response) -> List[AnnotationLabel]:
        data = response.json()
        if isinstance(data, dict) and "result" in data:
            data = data["result"]
        items = data if isinstance(data, list) else data.get("results", [])
        return [AnnotationLabel(**label) for label in items]

    @classmethod
    def _handle_error(cls, response: Response) -> None:
        _raise_for_status(response)


def _raise_for_status(response: Response) -> None:
    status = response.status_code
    if status == 401 or status == 403:
        raise InvalidAuthError()
    if status == 429:
        raise RateLimitError()
    if status == 503:
        raise ServiceUnavailableError()
    if status >= 500:
        raise ServerError()
    try:
        detail = response.json()
        msg = detail.get("message", detail.get("detail", response.text))
    except Exception:
        msg = None
    raise SDKException(msg or f"HTTP {status}")


# ---------------------------------------------------------------------------
# Main client
# ---------------------------------------------------------------------------

class AnnotationQueue(APIKeyAuth):
    """SDK client for managing annotation queues, items, scores, and analytics.

    Example::

        from fi.queues import AnnotationQueue

        client = AnnotationQueue(fi_api_key="...", fi_secret_key="...")

        # Create a queue
        queue = client.create(name="Review Queue", instructions="Rate quality 1-5")

        # Add items
        client.add_items(queue.id, items=[
            {"source_type": "trace", "source_id": "abc123"},
        ])

        # Import annotations programmatically
        client.import_annotations(queue.id, item_id, annotations=[
            {"label_id": "lbl_1", "value": "positive"},
        ])

        # Check progress
        progress = client.get_progress(queue.id)
    """

    def __init__(
        self,
        fi_api_key: Optional[str] = None,
        fi_secret_key: Optional[str] = None,
        fi_base_url: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(fi_api_key, fi_secret_key, fi_base_url, **kwargs)

    # ------------------------------------------------------------------
    # Name → ID resolvers
    # ------------------------------------------------------------------

    def _get_queue_id_from_name(self, queue_name: str) -> str:
        queues = self.list_queues(search=queue_name)
        matches = [q for q in queues if q.name.lower() == queue_name.lower()]
        if not matches:
            raise SDKException(f"Queue with name '{queue_name}' not found.")
        if len(matches) > 1:
            raise SDKException(
                f"Multiple queues found with name '{queue_name}': "
                f"{[q.id for q in matches]}. Use queue_id instead."
            )
        return matches[0].id

    def _get_label_id_from_name(self, label_name: str) -> str:
        labels = self.list_labels()
        matches = [l for l in labels if l.name.lower() == label_name.lower()]
        if not matches:
            raise SDKException(f"Label with name '{label_name}' not found.")
        if len(matches) > 1:
            raise SDKException(
                f"Multiple labels found with name '{label_name}': "
                f"{[f'{l.id} ({l.type})' for l in matches]}. Use label_id instead."
            )
        return matches[0].id

    # ------------------------------------------------------------------
    # Queue CRUD
    # ------------------------------------------------------------------

    def create(
        self,
        name: str,
        *,
        description: Optional[str] = None,
        instructions: Optional[str] = None,
        assignment_strategy: Optional[str] = None,
        annotations_required: Optional[int] = None,
        reservation_timeout_minutes: Optional[int] = None,
        requires_review: Optional[bool] = None,
        project: Optional[str] = None,
        dataset: Optional[str] = None,
        agent_definition: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> QueueDetail:
        """Create a new annotation queue."""
        body: Dict[str, Any] = {"name": name}
        if description is not None:
            body["description"] = description
        if instructions is not None:
            body["instructions"] = instructions
        if assignment_strategy is not None:
            body["assignment_strategy"] = assignment_strategy
        if annotations_required is not None:
            body["annotations_required"] = annotations_required
        if reservation_timeout_minutes is not None:
            body["reservation_timeout_minutes"] = reservation_timeout_minutes
        if requires_review is not None:
            body["requires_review"] = requires_review
        if project is not None:
            body["project"] = project
        if dataset is not None:
            body["dataset"] = dataset
        if agent_definition is not None:
            body["agent_definition"] = agent_definition

        logger.info("Creating annotation queue '%s'", name)
        config = RequestConfig(
            method=HttpMethod.POST,
            url=f"{self._base_url}/{Routes.annotation_queues.value}",
            json=body,
            timeout=timeout,
        )
        return self.request(config, _QueueResponseHandler)

    def list_queues(
        self,
        *,
        status: Optional[str] = None,
        search: Optional[str] = None,
        include_counts: bool = True,
        page: int = 1,
        page_size: int = 20,
        timeout: Optional[int] = None,
    ) -> List[QueueDetail]:
        """List annotation queues."""
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if status:
            params["status"] = status
        if search:
            params["search"] = search
        if include_counts:
            params["include_counts"] = "true"

        config = RequestConfig(
            method=HttpMethod.GET,
            url=f"{self._base_url}/{Routes.annotation_queues.value}",
            params=params,
            timeout=timeout,
        )
        return self.request(config, _QueueListResponseHandler)

    def get(self, queue_id: Optional[str] = None, *, queue_name: Optional[str] = None, timeout: Optional[int] = None) -> QueueDetail:
        """Get a single annotation queue by ID or name."""
        if not queue_id and not queue_name:
            raise ValueError("Provide either queue_id or queue_name")
        resolved_id = queue_id or self._get_queue_id_from_name(queue_name)
        _validate_id(resolved_id, "queue_id")
        url = f"{self._base_url}/{Routes.annotation_queue_detail.value}".format(queue_id=resolved_id)
        config = RequestConfig(method=HttpMethod.GET, url=url, timeout=timeout)
        return self.request(config, _QueueResponseHandler)

    def update(
        self,
        queue_id: Optional[str] = None,
        *,
        queue_name: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        instructions: Optional[str] = None,
        assignment_strategy: Optional[str] = None,
        annotations_required: Optional[int] = None,
        reservation_timeout_minutes: Optional[int] = None,
        requires_review: Optional[bool] = None,
        timeout: Optional[int] = None,
    ) -> QueueDetail:
        """Update an annotation queue by ID or name."""
        if not queue_id and not queue_name:
            raise ValueError("Provide either queue_id or queue_name")
        queue_id = queue_id or self._get_queue_id_from_name(queue_name)
        _validate_id(queue_id, "queue_id")
        body: Dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if instructions is not None:
            body["instructions"] = instructions
        if assignment_strategy is not None:
            body["assignment_strategy"] = assignment_strategy
        if annotations_required is not None:
            body["annotations_required"] = annotations_required
        if reservation_timeout_minutes is not None:
            body["reservation_timeout_minutes"] = reservation_timeout_minutes
        if requires_review is not None:
            body["requires_review"] = requires_review

        url = f"{self._base_url}/{Routes.annotation_queue_detail.value}".format(queue_id=queue_id)
        config = RequestConfig(method=HttpMethod.PATCH, url=url, json=body, timeout=timeout)
        return self.request(config, _QueueResponseHandler)

    def delete(self, queue_id: Optional[str] = None, *, queue_name: Optional[str] = None, timeout: Optional[int] = None) -> Dict[str, Any]:
        """Delete (soft-delete) an annotation queue by ID or name."""
        if not queue_id and not queue_name:
            raise ValueError("Provide either queue_id or queue_name")
        resolved_id = queue_id or self._get_queue_id_from_name(queue_name)
        _validate_id(resolved_id, "queue_id")
        url = f"{self._base_url}/{Routes.annotation_queue_detail.value}".format(queue_id=resolved_id)
        config = RequestConfig(method=HttpMethod.DELETE, url=url, timeout=timeout)
        return self.request(config, _DictResponseHandler)

    # ------------------------------------------------------------------
    # Queue lifecycle
    # ------------------------------------------------------------------

    def activate(self, queue_id: Optional[str] = None, *, queue_name: Optional[str] = None, timeout: Optional[int] = None) -> QueueDetail:
        """Activate a queue (transition from draft to active)."""
        return self._update_status(queue_id=queue_id, queue_name=queue_name, status="active", timeout=timeout)

    def complete_queue(self, queue_id: Optional[str] = None, *, queue_name: Optional[str] = None, timeout: Optional[int] = None) -> QueueDetail:
        """Mark a queue as completed."""
        return self._update_status(queue_id=queue_id, queue_name=queue_name, status="completed", timeout=timeout)

    def _update_status(self, *, queue_id: Optional[str] = None, queue_name: Optional[str] = None, status: str, timeout: Optional[int] = None) -> QueueDetail:
        if not queue_id and not queue_name:
            raise ValueError("Provide either queue_id or queue_name")
        resolved_id = queue_id or self._get_queue_id_from_name(queue_name)
        _validate_id(resolved_id, "queue_id")
        url = f"{self._base_url}/{Routes.annotation_queue_status.value}".format(queue_id=resolved_id)
        config = RequestConfig(method=HttpMethod.POST, url=url, json={"status": status}, timeout=timeout)
        return self.request(config, _QueueResponseHandler)

    # ------------------------------------------------------------------
    # Labels (CRUD)
    # ------------------------------------------------------------------

    def create_label(
        self,
        name: str,
        type: str,
        *,
        settings: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        project: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> AnnotationLabel:
        """Create an annotation label.

        Args:
            name: Label name (must be unique per org/type/project).
            type: Label type — ``"categorical"``, ``"text"``, ``"numeric"``,
                ``"star"``, or ``"thumbs_up_down"``.
            settings: Type-specific settings dict. Required structure varies
                by type:

                - **categorical**: ``{"rule_prompt": str, "multi_choice": bool,
                  "options": [{"label": str}, ...], "auto_annotate": bool,
                  "strategy": str | None}``
                - **text**: ``{"placeholder": str, "max_length": int,
                  "min_length": int}``
                - **numeric**: ``{"min": number, "max": number,
                  "step_size": number, "display_type": "slider" | "button"}``
                - **star**: ``{"no_of_stars": int}``
                - **thumbs_up_down**: ``{}`` (empty or omitted)

            description: Optional description.
            project: Optional project ID to scope the label to.
            timeout: Request timeout in seconds.

        Returns:
            AnnotationLabel instance.
        """
        payload: Dict[str, Any] = {"name": name, "type": type}
        if settings is not None:
            payload["settings"] = settings
        if description is not None:
            payload["description"] = description
        if project is not None:
            payload["project"] = project

        url = f"{self._base_url}/{Routes.annotations_labels.value}"
        config = RequestConfig(method=HttpMethod.POST, url=url, json=payload, timeout=timeout)
        return self.request(config, _LabelResponseHandler)

    def list_labels(
        self,
        *,
        project_id: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> List[AnnotationLabel]:
        """List annotation labels available to the organization.

        Args:
            project_id: Optional project ID to filter labels by.
            timeout: Request timeout in seconds.

        Returns:
            List of AnnotationLabel instances.
        """
        params: Dict[str, Any] = {}
        if project_id is not None:
            params["project_id"] = project_id

        url = f"{self._base_url}/{Routes.annotations_labels.value}"
        config = RequestConfig(method=HttpMethod.GET, url=url, params=params, timeout=timeout)
        return self.request(config, _LabelListResponseHandler)

    def get_label(self, label_id: Optional[str] = None, *, label_name: Optional[str] = None, timeout: Optional[int] = None) -> AnnotationLabel:
        """Get a single annotation label by ID or name.

        Args:
            label_id: UUID of the annotation label (or use label_name).
            label_name: Label name (alternative to label_id).
            timeout: Request timeout in seconds.

        Returns:
            AnnotationLabel instance.
        """
        if not label_id and not label_name:
            raise ValueError("Provide either label_id or label_name")
        resolved_id = label_id or self._get_label_id_from_name(label_name)
        _validate_id(resolved_id, "label_id")
        url = f"{self._base_url}/{Routes.annotations_labels_detail.value}".format(label_id=resolved_id)
        config = RequestConfig(method=HttpMethod.GET, url=url, timeout=timeout)
        return self.request(config, _LabelResponseHandler)

    def delete_label(self, label_id: Optional[str] = None, *, label_name: Optional[str] = None, timeout: Optional[int] = None) -> Dict[str, Any]:
        """Delete an annotation label by ID or name.

        Args:
            label_id: UUID of the annotation label (or use label_name).
            label_name: Label name (alternative to label_id).
            timeout: Request timeout in seconds.

        Returns:
            Dict with deletion confirmation.
        """
        if not label_id and not label_name:
            raise ValueError("Provide either label_id or label_name")
        resolved_id = label_id or self._get_label_id_from_name(label_name)
        _validate_id(resolved_id, "label_id")
        url = f"{self._base_url}/{Routes.annotations_labels_detail.value}".format(label_id=resolved_id)
        config = RequestConfig(method=HttpMethod.DELETE, url=url, timeout=timeout)
        return self.request(config, _DictResponseHandler)

    # ------------------------------------------------------------------
    # Labels (queue attachment)
    # ------------------------------------------------------------------

    def add_label(
        self,
        queue_id: Optional[str] = None,
        label_id: Optional[str] = None,
        *,
        queue_name: Optional[str] = None,
        label_name: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Attach an existing label to the queue. Accepts IDs or names."""
        if not queue_id and not queue_name:
            raise ValueError("Provide either queue_id or queue_name")
        if not label_id and not label_name:
            raise ValueError("Provide either label_id or label_name")
        resolved_queue_id = queue_id or self._get_queue_id_from_name(queue_name)
        resolved_label_id = label_id or self._get_label_id_from_name(label_name)
        _validate_id(resolved_queue_id, "queue_id")
        url = f"{self._base_url}/{Routes.annotation_queue_add_label.value}".format(queue_id=resolved_queue_id)
        config = RequestConfig(method=HttpMethod.POST, url=url, json={"label_id": resolved_label_id}, timeout=timeout)
        return self.request(config, _DictResponseHandler)

    def remove_label(
        self,
        queue_id: Optional[str] = None,
        label_id: Optional[str] = None,
        *,
        queue_name: Optional[str] = None,
        label_name: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Remove a label from the queue. Accepts IDs or names."""
        if not queue_id and not queue_name:
            raise ValueError("Provide either queue_id or queue_name")
        if not label_id and not label_name:
            raise ValueError("Provide either label_id or label_name")
        resolved_queue_id = queue_id or self._get_queue_id_from_name(queue_name)
        resolved_label_id = label_id or self._get_label_id_from_name(label_name)
        _validate_id(resolved_queue_id, "queue_id")
        url = f"{self._base_url}/{Routes.annotation_queue_remove_label.value}".format(queue_id=resolved_queue_id)
        config = RequestConfig(method=HttpMethod.POST, url=url, json={"label_id": resolved_label_id}, timeout=timeout)
        return self.request(config, _DictResponseHandler)

    # ------------------------------------------------------------------
    # Items
    # ------------------------------------------------------------------

    def add_items(
        self,
        queue_id: Optional[str] = None,
        items: Optional[List[Dict[str, str]]] = None,
        *,
        queue_name: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> AddItemsResponse:
        """Add items to the queue.

        Args:
            queue_id: Queue UUID.
            items: List of dicts with ``source_type`` and ``source_id``.
                   Valid source_types: trace, observation_span, trace_session,
                   call_execution, prototype_run, dataset_row.
            queue_name: Queue name (alternative to queue_id).
            timeout: Request timeout in seconds.

        Returns:
            AddItemsResponse with ``added`` and ``duplicates`` counts.
        """
        if not items:
            raise ValueError("items must be a non-empty list")
        if not queue_id and not queue_name:
            raise ValueError("Provide either queue_id or queue_name")

        resolved_id = queue_id or self._get_queue_id_from_name(queue_name)
        _validate_id(resolved_id, "queue_id")
        url = f"{self._base_url}/{Routes.queue_items_add.value}".format(queue_id=resolved_id)
        config = RequestConfig(method=HttpMethod.POST, url=url, json={"items": items}, timeout=timeout)
        result = self.request(config, _DictResponseHandler)
        return AddItemsResponse(**result)

    def list_items(
        self,
        queue_id: Optional[str] = None,
        *,
        queue_name: Optional[str] = None,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
        timeout: Optional[int] = None,
    ) -> List[QueueItem]:
        """List items in a queue with optional filters."""
        if not queue_id and not queue_name:
            raise ValueError("Provide either queue_id or queue_name")
        resolved_id = queue_id or self._get_queue_id_from_name(queue_name)
        _validate_id(resolved_id, "queue_id")
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if status:
            params["status"] = status
        if assigned_to:
            params["assigned_to"] = assigned_to

        url = f"{self._base_url}/{Routes.queue_items.value}".format(queue_id=resolved_id)
        config = RequestConfig(method=HttpMethod.GET, url=url, params=params, timeout=timeout)
        return self.request(config, _ItemListResponseHandler)

    def remove_items(
        self,
        queue_id: Optional[str] = None,
        item_ids: Optional[List[str]] = None,
        *,
        queue_name: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Bulk-remove items from the queue."""
        if not item_ids:
            raise ValueError("item_ids must be a non-empty list")
        if not queue_id and not queue_name:
            raise ValueError("Provide either queue_id or queue_name")

        resolved_id = queue_id or self._get_queue_id_from_name(queue_name)
        _validate_id(resolved_id, "queue_id")
        url = f"{self._base_url}/{Routes.queue_items_bulk_remove.value}".format(queue_id=resolved_id)
        config = RequestConfig(method=HttpMethod.POST, url=url, json={"item_ids": item_ids}, timeout=timeout)
        return self.request(config, _DictResponseHandler)

    def assign_items(
        self,
        queue_id: Optional[str] = None,
        item_ids: Optional[List[str]] = None,
        *,
        queue_name: Optional[str] = None,
        user_id: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Assign items to an annotator. Pass ``user_id=None`` to unassign."""
        if not item_ids:
            raise ValueError("item_ids must be a non-empty list")
        if not queue_id and not queue_name:
            raise ValueError("Provide either queue_id or queue_name")
        resolved_id = queue_id or self._get_queue_id_from_name(queue_name)
        _validate_id(resolved_id, "queue_id")
        url = f"{self._base_url}/{Routes.queue_items_assign.value}".format(queue_id=resolved_id)
        body: Dict[str, Any] = {"item_ids": item_ids, "user_id": user_id}
        config = RequestConfig(method=HttpMethod.POST, url=url, json=body, timeout=timeout)
        return self.request(config, _DictResponseHandler)

    # ------------------------------------------------------------------
    # Annotation submission (programmatic import)
    # ------------------------------------------------------------------

    def import_annotations(
        self,
        queue_id: Optional[str] = None,
        item_id: Optional[str] = None,
        annotations: Optional[List[Dict[str, Any]]] = None,
        *,
        queue_name: Optional[str] = None,
        annotator_id: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> ImportAnnotationsResponse:
        """Import annotations for a queue item programmatically.

        Args:
            queue_id: Queue UUID (or use queue_name).
            item_id: Queue item UUID.
            annotations: List of dicts with ``label_id`` and ``value``.
                         Optionally include ``score_source`` (default: "imported").
            queue_name: Queue name (alternative to queue_id).
            annotator_id: Optional user ID to attribute the annotation to.
            timeout: Request timeout in seconds.
        """
        if not annotations:
            raise ValueError("annotations must be a non-empty list")
        if not item_id:
            raise ValueError("item_id is required")
        if not queue_id and not queue_name:
            raise ValueError("Provide either queue_id or queue_name")

        resolved_id = queue_id or self._get_queue_id_from_name(queue_name)
        _validate_id(resolved_id, "queue_id")
        _validate_id(item_id, "item_id")
        url = f"{self._base_url}/{Routes.queue_item_annotations_import.value}".format(
            queue_id=resolved_id, item_id=item_id,
        )
        body: Dict[str, Any] = {"annotations": annotations}
        if annotator_id is not None:
            body["annotator_id"] = annotator_id

        config = RequestConfig(method=HttpMethod.POST, url=url, json=body, timeout=timeout)
        result = self.request(config, _DictResponseHandler)
        return ImportAnnotationsResponse(**result)

    def submit_annotations(
        self,
        queue_id: Optional[str] = None,
        item_id: Optional[str] = None,
        annotations: Optional[List[Dict[str, Any]]] = None,
        *,
        queue_name: Optional[str] = None,
        notes: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Submit annotations for a queue item (as the authenticated user).

        Args:
            queue_id: Queue UUID (or use queue_name).
            item_id: Queue item UUID.
            annotations: List of dicts with ``label_id`` and ``value``.
            queue_name: Queue name (alternative to queue_id).
            notes: Optional free-text notes.
        """
        if not annotations:
            raise ValueError("annotations must be a non-empty list")
        if not item_id:
            raise ValueError("item_id is required")
        if not queue_id and not queue_name:
            raise ValueError("Provide either queue_id or queue_name")

        resolved_id = queue_id or self._get_queue_id_from_name(queue_name)
        _validate_id(resolved_id, "queue_id")
        _validate_id(item_id, "item_id")
        url = f"{self._base_url}/{Routes.queue_item_annotations_submit.value}".format(
            queue_id=resolved_id, item_id=item_id,
        )
        body: Dict[str, Any] = {"annotations": annotations}
        if notes is not None:
            body["notes"] = notes

        config = RequestConfig(method=HttpMethod.POST, url=url, json=body, timeout=timeout)
        return self.request(config, _DictResponseHandler)

    def get_annotations(
        self,
        queue_id: Optional[str] = None,
        item_id: Optional[str] = None,
        *,
        queue_name: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> List[Score]:
        """Get all annotations for a queue item."""
        if not item_id:
            raise ValueError("item_id is required")
        if not queue_id and not queue_name:
            raise ValueError("Provide either queue_id or queue_name")
        resolved_id = queue_id or self._get_queue_id_from_name(queue_name)
        _validate_id(resolved_id, "queue_id")
        _validate_id(item_id, "item_id")
        url = f"{self._base_url}/{Routes.queue_item_annotations_list.value}".format(
            queue_id=resolved_id, item_id=item_id,
        )
        config = RequestConfig(method=HttpMethod.GET, url=url, timeout=timeout)
        return self.request(config, _ScoreListResponseHandler)

    def complete_item(
        self,
        queue_id: Optional[str] = None,
        item_id: Optional[str] = None,
        *,
        queue_name: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Mark a queue item as completed and get the next item."""
        if not item_id:
            raise ValueError("item_id is required")
        if not queue_id and not queue_name:
            raise ValueError("Provide either queue_id or queue_name")
        resolved_id = queue_id or self._get_queue_id_from_name(queue_name)
        _validate_id(resolved_id, "queue_id")
        _validate_id(item_id, "item_id")
        url = f"{self._base_url}/{Routes.queue_item_complete.value}".format(
            queue_id=resolved_id, item_id=item_id,
        )
        config = RequestConfig(method=HttpMethod.POST, url=url, timeout=timeout)
        return self.request(config, _DictResponseHandler)

    def skip_item(
        self,
        queue_id: Optional[str] = None,
        item_id: Optional[str] = None,
        *,
        queue_name: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Skip a queue item and get the next item."""
        if not item_id:
            raise ValueError("item_id is required")
        if not queue_id and not queue_name:
            raise ValueError("Provide either queue_id or queue_name")
        resolved_id = queue_id or self._get_queue_id_from_name(queue_name)
        _validate_id(resolved_id, "queue_id")
        _validate_id(item_id, "item_id")
        url = f"{self._base_url}/{Routes.queue_item_skip.value}".format(
            queue_id=resolved_id, item_id=item_id,
        )
        config = RequestConfig(method=HttpMethod.POST, url=url, timeout=timeout)
        return self.request(config, _DictResponseHandler)

    # ------------------------------------------------------------------
    # Scores (unified annotation model)
    # ------------------------------------------------------------------

    def create_score(
        self,
        source_type: str,
        source_id: str,
        label_id: Optional[str] = None,
        value: Any = None,
        *,
        label_name: Optional[str] = None,
        score_source: str = "api",
        notes: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Score:
        """Create a single score (upsert semantics).

        Args:
            source_type: trace, observation_span, trace_session, call_execution,
                         prototype_run, or dataset_row.
            source_id: UUID of the source entity.
            label_id: UUID of the annotation label (or use label_name).
            value: Annotation value (str, float, bool, or list depending on label type).
            label_name: Label name (alternative to label_id).
            score_source: Origin — "human", "api", or "auto" (default: "api").
            notes: Optional free-text notes.
        """
        if not label_id and not label_name:
            raise ValueError("Provide either label_id or label_name")
        resolved_label_id = label_id or self._get_label_id_from_name(label_name)
        body: Dict[str, Any] = {
            "source_type": source_type,
            "source_id": source_id,
            "label_id": resolved_label_id,
            "value": value,
            "score_source": score_source,
        }
        if notes is not None:
            body["notes"] = notes

        config = RequestConfig(
            method=HttpMethod.POST,
            url=f"{self._base_url}/{Routes.scores.value}",
            json=body,
            timeout=timeout,
        )
        return self.request(config, _ScoreResponseHandler)

    def create_scores(
        self,
        source_type: str,
        source_id: str,
        scores: List[Dict[str, Any]],
        *,
        notes: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create multiple scores on a single source in one request.

        Args:
            source_type: Source entity type.
            source_id: Source entity UUID.
            scores: List of dicts, each with ``label_id``, ``value``, and
                    optionally ``score_source``.
            notes: Optional shared notes.
        """
        if not scores:
            raise ValueError("scores must be a non-empty list")

        body: Dict[str, Any] = {
            "source_type": source_type,
            "source_id": source_id,
            "scores": scores,
        }
        if notes is not None:
            body["notes"] = notes

        config = RequestConfig(
            method=HttpMethod.POST,
            url=f"{self._base_url}/{Routes.scores_bulk.value}",
            json=body,
            timeout=timeout,
        )
        return self.request(config, _DictResponseHandler)

    def get_scores(
        self,
        source_type: str,
        source_id: str,
        *,
        timeout: Optional[int] = None,
    ) -> List[Score]:
        """Get all scores for a given source entity."""
        config = RequestConfig(
            method=HttpMethod.GET,
            url=f"{self._base_url}/{Routes.scores_for_source.value}",
            params={"source_type": source_type, "source_id": source_id},
            timeout=timeout,
        )
        return self.request(config, _ScoreListResponseHandler)

    # ------------------------------------------------------------------
    # Progress & Analytics
    # ------------------------------------------------------------------

    def get_progress(self, queue_id: Optional[str] = None, *, queue_name: Optional[str] = None, timeout: Optional[int] = None) -> QueueProgress:
        """Get queue progress (total, pending, completed, etc.)."""
        if not queue_id and not queue_name:
            raise ValueError("Provide either queue_id or queue_name")
        resolved_id = queue_id or self._get_queue_id_from_name(queue_name)
        _validate_id(resolved_id, "queue_id")
        url = f"{self._base_url}/{Routes.annotation_queue_progress.value}".format(queue_id=resolved_id)
        config = RequestConfig(method=HttpMethod.GET, url=url, timeout=timeout)
        result = self.request(config, _DictResponseHandler)
        return QueueProgress(**result)

    def get_analytics(self, queue_id: Optional[str] = None, *, queue_name: Optional[str] = None, timeout: Optional[int] = None) -> QueueAnalytics:
        """Get queue analytics (throughput, annotator performance, label distribution)."""
        if not queue_id and not queue_name:
            raise ValueError("Provide either queue_id or queue_name")
        resolved_id = queue_id or self._get_queue_id_from_name(queue_name)
        _validate_id(resolved_id, "queue_id")
        url = f"{self._base_url}/{Routes.annotation_queue_analytics.value}".format(queue_id=resolved_id)
        config = RequestConfig(method=HttpMethod.GET, url=url, timeout=timeout)
        result = self.request(config, _DictResponseHandler)
        return QueueAnalytics(**result)

    def get_agreement(self, queue_id: Optional[str] = None, *, queue_name: Optional[str] = None, timeout: Optional[int] = None) -> QueueAgreement:
        """Get inter-annotator agreement metrics for a queue."""
        if not queue_id and not queue_name:
            raise ValueError("Provide either queue_id or queue_name")
        resolved_id = queue_id or self._get_queue_id_from_name(queue_name)
        _validate_id(resolved_id, "queue_id")
        url = f"{self._base_url}/{Routes.annotation_queue_agreement.value}".format(queue_id=resolved_id)
        config = RequestConfig(method=HttpMethod.GET, url=url, timeout=timeout)
        result = self.request(config, _DictResponseHandler)
        return QueueAgreement(**result)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export(
        self,
        queue_id: Optional[str] = None,
        *,
        queue_name: Optional[str] = None,
        export_format: str = "json",
        status: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Any:
        """Export queue annotations.

        Args:
            queue_id: Queue UUID (or use queue_name).
            queue_name: Queue name (alternative to queue_id).
            export_format: ``"json"`` or ``"csv"``.
            status: Optional item status filter (e.g. ``"completed"``).

        Returns:
            For JSON format: list of dicts. For CSV: raw text content.
        """
        if not queue_id and not queue_name:
            raise ValueError("Provide either queue_id or queue_name")
        resolved_id = queue_id or self._get_queue_id_from_name(queue_name)
        _validate_id(resolved_id, "queue_id")
        params: Dict[str, Any] = {"export_format": export_format}
        if status:
            params["status"] = status

        url = f"{self._base_url}/{Routes.annotation_queue_export.value}".format(queue_id=resolved_id)
        config = RequestConfig(method=HttpMethod.GET, url=url, params=params, timeout=timeout)

        if export_format == "csv":
            return self.request(config, _CsvResponseHandler)

        return self.request(config, _DictResponseHandler)

    def export_to_dataset(
        self,
        queue_id: Optional[str] = None,
        *,
        queue_name: Optional[str] = None,
        dataset_name: Optional[str] = None,
        dataset_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> ExportToDatasetResponse:
        """Export annotated queue items to a dataset.

        Args:
            queue_id: Queue UUID (or use queue_name).
            queue_name: Queue name (alternative to queue_id).
            dataset_name: Name for a new dataset (mutually exclusive with dataset_id).
            dataset_id: Existing dataset UUID to append to.
            status_filter: Item status to export (default: "completed").
        """
        if dataset_name is None and dataset_id is None:
            raise ValueError("Provide either dataset_name or dataset_id")
        if dataset_name is not None and dataset_id is not None:
            raise ValueError("Provide either dataset_name or dataset_id, not both")
        if not queue_id and not queue_name:
            raise ValueError("Provide either queue_id or queue_name")

        resolved_id = queue_id or self._get_queue_id_from_name(queue_name)
        _validate_id(resolved_id, "queue_id")
        body: Dict[str, Any] = {}
        if dataset_name is not None:
            body["dataset_name"] = dataset_name
        if dataset_id is not None:
            body["dataset_id"] = dataset_id
        if status_filter is not None:
            body["status_filter"] = status_filter

        url = f"{self._base_url}/{Routes.annotation_queue_export_to_dataset.value}".format(queue_id=resolved_id)
        config = RequestConfig(method=HttpMethod.POST, url=url, json=body, timeout=timeout)
        result = self.request(config, _DictResponseHandler)
        return ExportToDatasetResponse(**result)
