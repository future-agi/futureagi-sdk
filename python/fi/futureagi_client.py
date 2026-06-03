import os
from collections.abc import Mapping
from typing import Any, Callable, TypeVar
from urllib.parse import quote
from uuid import UUID

from fi.generated.openapi_client.api.annotation_queue_discussion import (
    create_annotation_queue_item_comment,
    list_annotation_queue_item_discussion,
    reopen_annotation_queue_item_thread,
    resolve_annotation_queue_item_thread,
    toggle_annotation_queue_item_comment_reaction,
)
from fi.generated.openapi_client.api.annotation_queue_items import (
    add_annotation_queue_items,
    assign_annotation_queue_items,
    complete_annotation_queue_item,
    get_annotation_queue_item_detail,
    get_next_annotation_queue_item,
    import_annotation_queue_item_annotations,
    list_annotation_queue_item_annotations,
    list_annotation_queue_items,
    release_annotation_queue_item,
    remove_annotation_queue_items,
    skip_annotation_queue_item,
    submit_annotation_queue_item_annotations,
)
from fi.generated.openapi_client.api.annotation_queue_review import (
    review_annotation_queue_item,
)
from fi.generated.openapi_client.api.annotation_queues import (
    add_annotation_queue_label,
    archive_annotation_queue,
    create_annotation_queue,
    export_annotation_queue,
    export_annotation_queue_to_dataset,
    get_annotation_queue,
    get_annotation_queue_agreement,
    get_annotation_queue_analytics,
    get_annotation_queue_progress,
    list_annotation_queue_export_fields,
    list_annotation_queues,
    remove_annotation_queue_label,
    update_annotation_queue,
    update_annotation_queue_status,
)
from fi.generated.openapi_client.client import Client as GeneratedOpenAPIClient
from fi.generated.openapi_client.models.add_items import AddItems
from fi.generated.openapi_client.models.annotation_queue import (
    AnnotationQueue as GeneratedAnnotationQueue,
)
from fi.generated.openapi_client.models.assign_items import AssignItems
from fi.generated.openapi_client.models.bulk_remove_items import BulkRemoveItems
from fi.generated.openapi_client.models.discussion_comment_request import (
    DiscussionCommentRequest,
)
from fi.generated.openapi_client.models.discussion_reaction_request import (
    DiscussionReactionRequest,
)
from fi.generated.openapi_client.models.discussion_thread_status_request import (
    DiscussionThreadStatusRequest,
)
from fi.generated.openapi_client.models.empty_request import EmptyRequest
from fi.generated.openapi_client.models.import_annotations import ImportAnnotations
from fi.generated.openapi_client.models.list_annotation_queue_items_ordering import (
    ListAnnotationQueueItemsOrdering,
)
from fi.generated.openapi_client.models.queue_export_to_dataset_request import (
    QueueExportToDatasetRequest,
)
from fi.generated.openapi_client.models.queue_item_navigation_request import (
    QueueItemNavigationRequest,
)
from fi.generated.openapi_client.models.queue_label_request import QueueLabelRequest
from fi.generated.openapi_client.models.queue_status_request import QueueStatusRequest
from fi.generated.openapi_client.models.review_item_request import ReviewItemRequest
from fi.generated.openapi_client.models.submit_annotations import SubmitAnnotations
from fi.utils.constants import API_KEY_ENVVAR_NAME, SECRET_KEY_ENVVAR_NAME, get_base_url
from fi.utils.errors import MissingAuthError, SDKException

T = TypeVar("T")


class FutureAGIAPIError(SDKException):
    def __init__(self, status_code: int, payload: Any) -> None:
        self.status_code = status_code
        self.payload = payload
        super().__init__(
            message=f"Future AGI API request failed with status {status_code}: {payload}"
        )

    def get_error_code(self) -> str:
        return "FUTURE_AGI_API_ERROR"


def _as_uuid(value: str | UUID) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))


def _clean(values: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


def _quote(value: str | UUID) -> str:
    return quote(str(value), safe="")


def _coerce_model(model: type[T], value: Mapping[str, Any] | T | None) -> T:
    if isinstance(value, model):
        return value
    if value is None:
        value = {}
    return model.from_dict(value)  # type: ignore[attr-defined]


def _to_plain(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return _to_plain(value.to_dict())
    if isinstance(value, list):
        return [_to_plain(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_to_plain(item) for item in value)
    if isinstance(value, dict):
        return {key: _to_plain(item) for key, item in value.items()}
    return value


def _ordering(
    value: str | ListAnnotationQueueItemsOrdering | None,
) -> ListAnnotationQueueItemsOrdering | None:
    if value is None or isinstance(value, ListAnnotationQueueItemsOrdering):
        return value
    return ListAnnotationQueueItemsOrdering(value)


class FutureAGIClient:
    def __init__(
        self,
        api_key: str | None = None,
        secret_key: str | None = None,
        *,
        fi_api_key: str | None = None,
        fi_secret_key: str | None = None,
        base_url: str | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> None:
        self.api_key = api_key or fi_api_key or os.environ.get(API_KEY_ENVVAR_NAME)
        self.secret_key = (
            secret_key or fi_secret_key or os.environ.get(SECRET_KEY_ENVVAR_NAME)
        )
        if self.api_key is None or self.secret_key is None:
            raise MissingAuthError(self.api_key, self.secret_key)

        self.generated_client = GeneratedOpenAPIClient(
            base_url=(base_url or get_base_url()).rstrip("/"),
            headers={
                "X-Api-Key": self.api_key,
                "X-Secret-Key": self.secret_key,
                **dict(headers or {}),
            },
            timeout=timeout,
            raise_on_unexpected_status=True,
        )
        self.annotation_queues = AnnotationQueuesClient(self.generated_client)
        self.datasets = DatasetsClient(self.generated_client)
        self.evals = EvalsClient(self.generated_client)
        self.experiments = ExperimentsClient(self.generated_client)
        self.simulations = SimulationsClient(self.generated_client)
        self.tracing = TracingClient(self.generated_client)
        self.users = UsersClient(self.generated_client)
        self.alerts = AlertsClient(self.generated_client)

    def close(self) -> None:
        self.generated_client.get_httpx_client().close()

    def __enter__(self) -> "FutureAGIClient":
        self.generated_client.__enter__()
        return self

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        self.generated_client.__exit__(*args, **kwargs)


class BaseGeneratedClient:
    def __init__(self, client: GeneratedOpenAPIClient) -> None:
        self._client = client

    def _request(
        self, sync_detailed: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        response = sync_detailed(*args, client=self._client, **kwargs)
        status_code = int(response.status_code)
        payload = _to_plain(response.parsed)
        if status_code >= 400:
            raise FutureAGIAPIError(status_code, payload)
        return payload

    def _raw_request(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, Any] | None = None,
        body: Any = None,
    ) -> Any:
        request_kwargs: dict[str, Any] = {
            "method": method,
            "url": path,
            "params": _clean(query or {}),
        }
        if body is not None:
            request_kwargs["json"] = body
        response = self._client.get_httpx_client().request(**request_kwargs)
        status_code = int(response.status_code)
        if response.content:
            try:
                payload: Any = response.json()
            except ValueError:
                payload = response.text
        else:
            payload = None
        if status_code >= 400:
            raise FutureAGIAPIError(status_code, payload)
        return payload


class AnnotationQueuesClient(BaseGeneratedClient):
    def __init__(self, client: GeneratedOpenAPIClient) -> None:
        super().__init__(client)
        self.items = AnnotationQueueItemsClient(client)
        self.discussion = AnnotationQueueDiscussionClient(client)
        self.review = AnnotationQueueReviewClient(client)

    def list(self, **query: Any) -> Any:
        return self._request(list_annotation_queues.sync_detailed, **_clean(query))

    def create(self, body: Mapping[str, Any] | GeneratedAnnotationQueue) -> Any:
        return self._request(
            create_annotation_queue.sync_detailed,
            body=_coerce_model(GeneratedAnnotationQueue, body),
        )

    def get(self, queue_id: str | UUID) -> Any:
        return self._request(get_annotation_queue.sync_detailed, _as_uuid(queue_id))

    def update(
        self, queue_id: str | UUID, body: Mapping[str, Any] | GeneratedAnnotationQueue
    ) -> Any:
        return self._request(
            update_annotation_queue.sync_detailed,
            _as_uuid(queue_id),
            body=_coerce_model(GeneratedAnnotationQueue, body),
        )

    def archive(self, queue_id: str | UUID) -> Any:
        return self._request(archive_annotation_queue.sync_detailed, _as_uuid(queue_id))

    def update_status(
        self, queue_id: str | UUID, body: Mapping[str, Any] | QueueStatusRequest
    ) -> Any:
        return self._request(
            update_annotation_queue_status.sync_detailed,
            _as_uuid(queue_id),
            body=_coerce_model(QueueStatusRequest, body),
        )

    def progress(self, queue_id: str | UUID) -> Any:
        return self._request(get_annotation_queue_progress.sync_detailed, str(queue_id))

    def analytics(self, queue_id: str | UUID) -> Any:
        return self._request(
            get_annotation_queue_analytics.sync_detailed, str(queue_id)
        )

    def agreement(self, queue_id: str | UUID) -> Any:
        return self._request(
            get_annotation_queue_agreement.sync_detailed, str(queue_id)
        )

    def export_json(self, queue_id: str | UUID) -> Any:
        return self._request(export_annotation_queue.sync_detailed, str(queue_id))

    def list_export_fields(self, queue_id: str | UUID) -> Any:
        return self._request(
            list_annotation_queue_export_fields.sync_detailed, str(queue_id)
        )

    def export_to_dataset(
        self,
        queue_id: str | UUID,
        body: Mapping[str, Any] | QueueExportToDatasetRequest,
    ) -> Any:
        return self._request(
            export_annotation_queue_to_dataset.sync_detailed,
            str(queue_id),
            body=_coerce_model(QueueExportToDatasetRequest, body),
        )

    def add_label(
        self, queue_id: str | UUID, body: Mapping[str, Any] | QueueLabelRequest
    ) -> Any:
        return self._request(
            add_annotation_queue_label.sync_detailed,
            _as_uuid(queue_id),
            body=_coerce_model(QueueLabelRequest, body),
        )

    def remove_label(
        self, queue_id: str | UUID, body: Mapping[str, Any] | QueueLabelRequest
    ) -> Any:
        return self._request(
            remove_annotation_queue_label.sync_detailed,
            _as_uuid(queue_id),
            body=_coerce_model(QueueLabelRequest, body),
        )


class AnnotationQueueItemsClient(BaseGeneratedClient):
    def list(self, queue_id: str | UUID, **query: Any) -> Any:
        if "ordering" in query:
            query["ordering"] = _ordering(query["ordering"])
        return self._request(
            list_annotation_queue_items.sync_detailed, str(queue_id), **_clean(query)
        )

    def add(self, queue_id: str | UUID, body: Mapping[str, Any] | AddItems) -> Any:
        return self._request(
            add_annotation_queue_items.sync_detailed,
            str(queue_id),
            body=_coerce_model(AddItems, body),
        )

    def assign(
        self, queue_id: str | UUID, body: Mapping[str, Any] | AssignItems
    ) -> Any:
        return self._request(
            assign_annotation_queue_items.sync_detailed,
            str(queue_id),
            body=_coerce_model(AssignItems, body),
        )

    def remove(
        self, queue_id: str | UUID, body: Mapping[str, Any] | BulkRemoveItems
    ) -> Any:
        return self._request(
            remove_annotation_queue_items.sync_detailed,
            str(queue_id),
            body=_coerce_model(BulkRemoveItems, body),
        )

    def next(self, queue_id: str | UUID, **query: Any) -> Any:
        return self._request(
            get_next_annotation_queue_item.sync_detailed, str(queue_id), **_clean(query)
        )

    def get_detail(
        self, queue_id: str | UUID, item_id: str | UUID, **query: Any
    ) -> Any:
        return self._request(
            get_annotation_queue_item_detail.sync_detailed,
            str(queue_id),
            _as_uuid(item_id),
            **_clean(query),
        )

    def release(
        self,
        queue_id: str | UUID,
        item_id: str | UUID,
        body: Mapping[str, Any] | EmptyRequest | None = None,
    ) -> Any:
        return self._request(
            release_annotation_queue_item.sync_detailed,
            str(queue_id),
            _as_uuid(item_id),
            body=_coerce_model(EmptyRequest, body),
        )

    def complete(
        self,
        queue_id: str | UUID,
        item_id: str | UUID,
        body: Mapping[str, Any] | QueueItemNavigationRequest | None = None,
    ) -> Any:
        return self._request(
            complete_annotation_queue_item.sync_detailed,
            str(queue_id),
            _as_uuid(item_id),
            body=_coerce_model(QueueItemNavigationRequest, body),
        )

    def skip(
        self,
        queue_id: str | UUID,
        item_id: str | UUID,
        body: Mapping[str, Any] | QueueItemNavigationRequest | None = None,
    ) -> Any:
        return self._request(
            skip_annotation_queue_item.sync_detailed,
            str(queue_id),
            _as_uuid(item_id),
            body=_coerce_model(QueueItemNavigationRequest, body),
        )

    def list_annotations(self, queue_id: str | UUID, item_id: str | UUID) -> Any:
        return self._request(
            list_annotation_queue_item_annotations.sync_detailed,
            str(queue_id),
            _as_uuid(item_id),
        )

    def submit_annotations(
        self,
        queue_id: str | UUID,
        item_id: str | UUID,
        body: Mapping[str, Any] | SubmitAnnotations,
    ) -> Any:
        return self._request(
            submit_annotation_queue_item_annotations.sync_detailed,
            str(queue_id),
            _as_uuid(item_id),
            body=_coerce_model(SubmitAnnotations, body),
        )

    def import_annotations(
        self,
        queue_id: str | UUID,
        item_id: str | UUID,
        body: Mapping[str, Any] | ImportAnnotations,
    ) -> Any:
        return self._request(
            import_annotation_queue_item_annotations.sync_detailed,
            str(queue_id),
            _as_uuid(item_id),
            body=_coerce_model(ImportAnnotations, body),
        )


class AnnotationQueueDiscussionClient(BaseGeneratedClient):
    def list(self, queue_id: str | UUID, item_id: str | UUID) -> Any:
        return self._request(
            list_annotation_queue_item_discussion.sync_detailed,
            str(queue_id),
            _as_uuid(item_id),
        )

    def comment(
        self,
        queue_id: str | UUID,
        item_id: str | UUID,
        body: Mapping[str, Any] | DiscussionCommentRequest,
    ) -> Any:
        return self._request(
            create_annotation_queue_item_comment.sync_detailed,
            str(queue_id),
            _as_uuid(item_id),
            body=_coerce_model(DiscussionCommentRequest, body),
        )

    def resolve_thread(
        self,
        queue_id: str | UUID,
        item_id: str | UUID,
        thread_id: str,
        body: Mapping[str, Any] | DiscussionThreadStatusRequest | None = None,
    ) -> Any:
        return self._request(
            resolve_annotation_queue_item_thread.sync_detailed,
            str(queue_id),
            _as_uuid(item_id),
            thread_id,
            body=_coerce_model(DiscussionThreadStatusRequest, body),
        )

    def reopen_thread(
        self,
        queue_id: str | UUID,
        item_id: str | UUID,
        thread_id: str,
        body: Mapping[str, Any] | DiscussionThreadStatusRequest | None = None,
    ) -> Any:
        return self._request(
            reopen_annotation_queue_item_thread.sync_detailed,
            str(queue_id),
            _as_uuid(item_id),
            thread_id,
            body=_coerce_model(DiscussionThreadStatusRequest, body),
        )

    def react(
        self,
        queue_id: str | UUID,
        item_id: str | UUID,
        comment_id: str,
        body: Mapping[str, Any] | DiscussionReactionRequest,
    ) -> Any:
        return self._request(
            toggle_annotation_queue_item_comment_reaction.sync_detailed,
            str(queue_id),
            _as_uuid(item_id),
            comment_id,
            body=_coerce_model(DiscussionReactionRequest, body),
        )


class AnnotationQueueReviewClient(BaseGeneratedClient):
    def submit(
        self,
        queue_id: str | UUID,
        item_id: str | UUID,
        body: Mapping[str, Any] | ReviewItemRequest,
    ) -> Any:
        return self._request(
            review_annotation_queue_item.sync_detailed,
            str(queue_id),
            _as_uuid(item_id),
            body=_coerce_model(ReviewItemRequest, body),
        )


class DatasetsClient(BaseGeneratedClient):
    def list(self, **query: Any) -> Any:
        return self._raw_request(
            "GET", "/model-hub/develops/get-datasets/", query=query
        )

    def list_names(self, **query: Any) -> Any:
        return self._raw_request(
            "GET", "/model-hub/develops/get-datasets-names/", query=query
        )

    def get_table(self, dataset_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/model-hub/develops/{_quote(dataset_id)}/get-dataset-table/",
            query=query,
        )

    def get_row(self, dataset_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "POST",
            f"/model-hub/develops/{_quote(dataset_id)}/get-row-data/",
            body=body,
        )

    def get_columns(self, dataset_id: str | UUID) -> Any:
        return self._raw_request(
            "GET", f"/model-hub/dataset/columns/{_quote(dataset_id)}/"
        )

    def create_empty(self, body: Any) -> Any:
        return self._raw_request(
            "POST", "/model-hub/develops/create-empty-dataset/", body=body
        )

    def create_manual(self, body: Any) -> Any:
        return self._raw_request(
            "POST", "/model-hub/develops/create-dataset-manually/", body=body
        )

    def create_from_file(self, body: Any) -> Any:
        return self._raw_request(
            "POST", "/model-hub/develops/create-dataset-from-local-file/", body=body
        )

    def add_rows(self, dataset_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "POST",
            f"/model-hub/develops/{_quote(dataset_id)}/add_rows/",
            body=body,
        )

    def add_columns(self, dataset_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "POST",
            f"/model-hub/develops/{_quote(dataset_id)}/add_columns/",
            body=body,
        )

    def update_cell(self, dataset_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "POST",
            f"/model-hub/develops/{_quote(dataset_id)}/update_cell_value/",
            body=body,
        )

    def delete_row(self, dataset_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "DELETE",
            f"/model-hub/develops/{_quote(dataset_id)}/delete_row/",
            query=query,
        )

    def delete_column(self, dataset_id: str | UUID, column_id: str | UUID) -> Any:
        return self._raw_request(
            "DELETE",
            f"/model-hub/develops/{_quote(dataset_id)}/delete_column/{_quote(column_id)}/",
        )

    def download(self, dataset_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/model-hub/develops/{_quote(dataset_id)}/download_dataset/",
            query=query,
        )

    def json_schema(self, dataset_id: str | UUID) -> Any:
        return self._raw_request(
            "GET", f"/model-hub/dataset/{_quote(dataset_id)}/json-schema/"
        )

    def eval_stats(self, dataset_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/model-hub/dataset/{_quote(dataset_id)}/eval-stats/",
            query=query,
        )

    def annotation_summary(self, dataset_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/model-hub/dataset/{_quote(dataset_id)}/annotation-summary/",
            query=query,
        )

    def duplicate(self, dataset_id: str | UUID, body: Any | None = None) -> Any:
        return self._raw_request(
            "POST",
            f"/model-hub/datasets/{_quote(dataset_id)}/duplicate/",
            body=body,
        )

    def derived_variables(self, dataset_id: str | UUID) -> Any:
        return self._raw_request(
            "GET", f"/model-hub/datasets/{_quote(dataset_id)}/derived-variables/"
        )

    def base_columns(self, **query: Any) -> Any:
        return self._raw_request(
            "GET", "/model-hub/datasets/get-base-columns/", query=query
        )


class ExperimentsClient(BaseGeneratedClient):
    def list(self, **query: Any) -> Any:
        return self._raw_request("GET", "/model-hub/experiments/v2/list/", query=query)

    def create(self, body: Any) -> Any:
        return self._raw_request("POST", "/model-hub/experiments/v2/", body=body)

    def get(self, experiment_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/model-hub/experiments/v2/{_quote(experiment_id)}/",
            query=query,
        )

    def update(self, experiment_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "PUT",
            f"/model-hub/experiments/v2/{_quote(experiment_id)}/",
            body=body,
        )

    def delete(self, body: Any) -> Any:
        return self._raw_request(
            "DELETE", "/model-hub/experiments/v2/delete/", body=body
        )

    def rows(self, experiment_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/model-hub/experiments/v2/{_quote(experiment_id)}/rows/",
            query=query,
        )

    def row(self, experiment_id: str | UUID, row_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/model-hub/experiments/v2/{_quote(experiment_id)}/rows/{_quote(row_id)}/",
            query=query,
        )

    def stats(self, experiment_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/model-hub/experiments/v2/{_quote(experiment_id)}/stats/",
            query=query,
        )

    def download(self, experiment_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/model-hub/experiments/v2/{_quote(experiment_id)}/download/",
            query=query,
        )

    def rerun(self, body: Any) -> Any:
        return self._raw_request("POST", "/model-hub/experiments/v2/re-run/", body=body)

    def stop(self, experiment_id: str | UUID, body: Any | None = None) -> Any:
        return self._raw_request(
            "POST",
            f"/model-hub/experiments/v2/{_quote(experiment_id)}/stop/",
            body=body,
        )

    def compare(self, experiment_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "POST",
            f"/model-hub/experiments/v2/{_quote(experiment_id)}/compare-experiments/",
            body=body,
        )

    def comparisons(self, experiment_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/model-hub/experiments/v2/{_quote(experiment_id)}/comparisons/",
            query=query,
        )

    def json_schema(self, experiment_id: str | UUID) -> Any:
        return self._raw_request(
            "GET", f"/model-hub/experiments/v2/{_quote(experiment_id)}/json-schema/"
        )


class EvalsClient(BaseGeneratedClient):
    def list_templates(self, body: Any) -> Any:
        return self._raw_request("POST", "/model-hub/eval-templates/list/", body=body)

    def create_template(self, body: Any) -> Any:
        return self._raw_request(
            "POST", "/model-hub/eval-templates/create-v2/", body=body
        )

    def get_template(self, template_id: str | UUID) -> Any:
        return self._raw_request(
            "GET", f"/model-hub/eval-templates/{_quote(template_id)}/detail/"
        )

    def update_template(self, template_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "PUT",
            f"/model-hub/eval-templates/{_quote(template_id)}/update/",
            body=body,
        )

    def delete_template(self, body: Any) -> Any:
        return self._raw_request("POST", "/model-hub/delete-eval-template/", body=body)

    def bulk_delete_templates(self, body: Any) -> Any:
        return self._raw_request(
            "POST", "/model-hub/eval-templates/bulk-delete/", body=body
        )

    def template_usage(self, template_id: str | UUID) -> Any:
        return self._raw_request(
            "GET", f"/model-hub/eval-templates/{_quote(template_id)}/usage/"
        )

    def template_versions(self, template_id: str | UUID) -> Any:
        return self._raw_request(
            "GET", f"/model-hub/eval-templates/{_quote(template_id)}/versions/"
        )

    def create_template_version(self, template_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "POST",
            f"/model-hub/eval-templates/{_quote(template_id)}/versions/create/",
            body=body,
        )

    def restore_template_version(
        self,
        template_id: str | UUID,
        version_id: str | UUID,
        body: Any | None = None,
    ) -> Any:
        return self._raw_request(
            "POST",
            f"/model-hub/eval-templates/{_quote(template_id)}/versions/{_quote(version_id)}/restore/",
            body=body or {},
        )

    def set_default_template_version(
        self,
        template_id: str | UUID,
        version_id: str | UUID,
        body: Any | None = None,
    ) -> Any:
        return self._raw_request(
            "PUT",
            f"/model-hub/eval-templates/{_quote(template_id)}/versions/{_quote(version_id)}/set-default/",
            body=body or {},
        )

    def list_sdk_evals(self) -> Any:
        return self._raw_request("GET", "/sdk/api/v1/get-evals/")

    def configure(self, body: Any) -> Any:
        return self._raw_request(
            "POST", "/sdk/api/v1/configure-evaluations/", body=body
        )

    def run(self, body: Any) -> Any:
        return self._raw_request("POST", "/sdk/api/v1/eval/", body=body)

    def get_run(self, eval_id: str | UUID) -> Any:
        return self._raw_request("GET", f"/sdk/api/v1/eval/{_quote(eval_id)}/")

    def run_v2(self, body: Any) -> Any:
        return self._raw_request("POST", "/sdk/api/v1/new-eval/", body=body)

    def get_run_v2(self, eval_id: str | UUID) -> Any:
        return self._raw_request(
            "GET", "/sdk/api/v1/new-eval/", query={"eval_id": eval_id}
        )

    def list_pipelines(self, **query: Any) -> Any:
        return self._raw_request("GET", "/sdk/api/v1/evaluate-pipeline/", query=query)

    def evaluate_pipeline(self, body: Any) -> Any:
        return self._raw_request("POST", "/sdk/api/v1/evaluate-pipeline/", body=body)

    def dataset_evals(self, dataset_id: str | UUID) -> Any:
        return self._raw_request(
            "GET", f"/model-hub/develops/{_quote(dataset_id)}/get_evals_list/"
        )

    def dataset_eval_structure(
        self, dataset_id: str | UUID, eval_id: str | UUID, **query: Any
    ) -> Any:
        return self._raw_request(
            "GET",
            f"/model-hub/develops/{_quote(dataset_id)}/get_eval_structure/{_quote(eval_id)}/",
            query=query,
        )

    def preview_dataset_eval(self, dataset_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "POST",
            f"/model-hub/develops/{_quote(dataset_id)}/preview_run_eval/",
            body=body,
        )

    def start_dataset_evals(self, dataset_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "POST",
            f"/model-hub/develops/{_quote(dataset_id)}/start_evals_process/",
            body=body,
        )

    def add_dataset_user_eval(self, dataset_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "POST",
            f"/model-hub/develops/{_quote(dataset_id)}/add_user_eval/",
            body=body,
        )

    def edit_and_run_dataset_user_eval(
        self, dataset_id: str | UUID, eval_id: str | UUID, body: Any
    ) -> Any:
        return self._raw_request(
            "POST",
            f"/model-hub/develops/{_quote(dataset_id)}/edit_and_run_user_eval/{_quote(eval_id)}/",
            body=body,
        )

    def stop_dataset_user_eval(
        self, dataset_id: str | UUID, eval_id: str | UUID, body: Any | None = None
    ) -> Any:
        return self._raw_request(
            "POST",
            f"/model-hub/develops/{_quote(dataset_id)}/stop_user_eval/{_quote(eval_id)}/",
            body=body or {},
        )

    def delete_dataset_user_eval(
        self, dataset_id: str | UUID, eval_id: str | UUID
    ) -> Any:
        return self._raw_request(
            "DELETE",
            f"/model-hub/develops/{_quote(dataset_id)}/delete_user_eval/{_quote(eval_id)}/",
        )

    def delete_dataset_template_eval(
        self, dataset_id: str | UUID, eval_id: str | UUID
    ) -> Any:
        return self._raw_request(
            "DELETE",
            f"/model-hub/develops/{_quote(dataset_id)}/delete_template_eval/{_quote(eval_id)}/",
        )


class SimulationsClient(BaseGeneratedClient):
    def __init__(self, client: GeneratedOpenAPIClient) -> None:
        super().__init__(client)
        self.agent_definitions = SimulationAgentDefinitionsClient(client)
        self.run_tests = SimulationRunTestsClient(client)
        self.test_executions = SimulationTestExecutionsClient(client)
        self.personas = SimulationPersonasClient(client)
        self.scenarios = SimulationScenariosClient(client)

    def runs(self, **query: Any) -> Any:
        return self._raw_request("GET", "/sdk/api/v1/simulation/runs/", query=query)

    def metrics(self, **query: Any) -> Any:
        return self._raw_request("GET", "/sdk/api/v1/simulation/metrics/", query=query)

    def analytics(self, **query: Any) -> Any:
        return self._raw_request(
            "GET", "/sdk/api/v1/simulation/analytics/", query=query
        )


class SimulationAgentDefinitionsClient(BaseGeneratedClient):
    def list(self, **query: Any) -> Any:
        return self._raw_request("GET", "/simulate/agent-definitions/", query=query)

    def create(self, body: Any) -> Any:
        return self._raw_request(
            "POST", "/simulate/agent-definitions/create/", body=body
        )

    def get(self, agent_id: str | UUID) -> Any:
        return self._raw_request(
            "GET", f"/simulate/agent-definitions/{_quote(agent_id)}/"
        )

    def update(self, agent_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "PUT", f"/simulate/agent-definitions/{_quote(agent_id)}/edit/", body=body
        )

    def delete(self, agent_id: str | UUID) -> Any:
        return self._raw_request(
            "DELETE", f"/simulate/agent-definitions/{_quote(agent_id)}/delete/"
        )


class SimulationRunTestsClient(BaseGeneratedClient):
    def active(self) -> Any:
        return self._raw_request("GET", "/simulate/run-tests/active/")

    def list(self, **query: Any) -> Any:
        return self._raw_request("GET", "/simulate/run-tests/", query=query)

    def create(self, body: Any) -> Any:
        return self._raw_request("POST", "/simulate/run-tests/create/", body=body)

    def get(self, run_test_id: str | UUID) -> Any:
        return self._raw_request("GET", f"/simulate/run-tests/{_quote(run_test_id)}/")

    def update(self, run_test_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "PATCH", f"/simulate/run-tests/{_quote(run_test_id)}/", body=body
        )

    def delete(self, run_test_id: str | UUID) -> Any:
        return self._raw_request(
            "DELETE", f"/simulate/run-tests/{_quote(run_test_id)}/"
        )

    def execute(self, run_test_id: str | UUID, body: Any | None = None) -> Any:
        return self._raw_request(
            "POST", f"/simulate/run-tests/{_quote(run_test_id)}/execute/", body=body
        )

    def status(self, run_test_id: str | UUID) -> Any:
        return self._raw_request(
            "GET", f"/simulate/run-tests/{_quote(run_test_id)}/status/"
        )

    def analytics(self, run_test_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/simulate/run-tests/{_quote(run_test_id)}/analytics/",
            query=query,
        )

    def executions(self, run_test_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/simulate/run-tests/{_quote(run_test_id)}/executions/",
            query=query,
        )

    def call_executions(self, run_test_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/simulate/run-tests/{_quote(run_test_id)}/call-executions/",
            query=query,
        )

    def add_eval_configs(self, run_test_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "POST",
            f"/simulate/run-tests/{_quote(run_test_id)}/eval-configs/",
            body=body,
        )

    def delete_eval_config(
        self, run_test_id: str | UUID, eval_config_id: str | UUID
    ) -> Any:
        return self._raw_request(
            "DELETE",
            f"/simulate/run-tests/{_quote(run_test_id)}/eval-configs/{_quote(eval_config_id)}/",
        )

    def eval_config_structure(
        self, run_test_id: str | UUID, eval_config_id: str | UUID
    ) -> Any:
        return self._raw_request(
            "GET",
            f"/simulate/run-tests/{_quote(run_test_id)}/eval-configs/{_quote(eval_config_id)}/get-structure/",
        )

    def update_eval_config(
        self, run_test_id: str | UUID, eval_config_id: str | UUID, body: Any
    ) -> Any:
        return self._raw_request(
            "POST",
            f"/simulate/run-tests/{_quote(run_test_id)}/eval-configs/{_quote(eval_config_id)}/update/",
            body=body,
        )

    def eval_summary(self, run_test_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/simulate/run-tests/{_quote(run_test_id)}/eval-summary/",
            query=query,
        )

    def eval_summary_comparison(self, run_test_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/simulate/run-tests/{_quote(run_test_id)}/eval-summary-comparison/",
            query=query,
        )

    def run_new_evals(self, run_test_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "POST",
            f"/simulate/run-tests/{_quote(run_test_id)}/run-new-evals/",
            body=body,
        )

    def scenarios(self, run_test_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/simulate/run-tests/{_quote(run_test_id)}/scenarios/",
            query=query,
        )

    def sdk_code(self, run_test_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/simulate/run-tests/{_quote(run_test_id)}/sdk-code/",
            query=query,
        )


class SimulationTestExecutionsClient(BaseGeneratedClient):
    def list(self, **query: Any) -> Any:
        return self._raw_request("GET", "/simulate/api/test-executions/", query=query)

    def get(self, test_execution_id: str | UUID) -> Any:
        return self._raw_request(
            "GET", f"/simulate/test-executions/{_quote(test_execution_id)}/"
        )

    def analytics(self, test_execution_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/simulate/test-executions/{_quote(test_execution_id)}/analytics/",
            query=query,
        )

    def transcripts(self, test_execution_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/simulate/test-executions/{_quote(test_execution_id)}/transcripts/",
            query=query,
        )

    def kpis(self, test_execution_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/simulate/test-executions/{_quote(test_execution_id)}/kpis/",
            query=query,
        )

    def performance_summary(self, test_execution_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/simulate/test-executions/{_quote(test_execution_id)}/performance-summary/",
            query=query,
        )

    def cancel(self, test_execution_id: str | UUID, body: Any | None = None) -> Any:
        return self._raw_request(
            "POST",
            f"/simulate/test-executions/{_quote(test_execution_id)}/cancel/",
            body=body,
        )


class SimulationPersonasClient(BaseGeneratedClient):
    def list(self, **query: Any) -> Any:
        return self._raw_request("GET", "/simulate/api/personas/", query=query)

    def create(self, body: Any) -> Any:
        return self._raw_request("POST", "/simulate/api/personas/", body=body)

    def get(self, persona_id: str | UUID) -> Any:
        return self._raw_request("GET", f"/simulate/api/personas/{_quote(persona_id)}/")

    def update(self, persona_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "PATCH", f"/simulate/api/personas/{_quote(persona_id)}/", body=body
        )

    def delete(self, persona_id: str | UUID) -> Any:
        return self._raw_request(
            "DELETE", f"/simulate/api/personas/{_quote(persona_id)}/"
        )


class SimulationScenariosClient(BaseGeneratedClient):
    def list(self, **query: Any) -> Any:
        return self._raw_request("GET", "/simulate/scenarios/", query=query)

    def create(self, body: Any) -> Any:
        return self._raw_request("POST", "/simulate/scenarios/create/", body=body)

    def get(self, scenario_id: str | UUID) -> Any:
        return self._raw_request("GET", f"/simulate/scenarios/{_quote(scenario_id)}/")

    def update(self, scenario_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "PUT", f"/simulate/scenarios/{_quote(scenario_id)}/edit/", body=body
        )

    def delete(self, scenario_id: str | UUID) -> Any:
        return self._raw_request(
            "DELETE", f"/simulate/scenarios/{_quote(scenario_id)}/delete/"
        )


class TracingClient(BaseGeneratedClient):
    def projects(self, **query: Any) -> Any:
        return self._raw_request("GET", "/tracer/project/list_projects/", query=query)

    def traces(self, **query: Any) -> Any:
        return self._raw_request("GET", "/tracer/trace/list_traces/", query=query)

    def get_trace(self, trace_id: str | UUID) -> Any:
        return self._raw_request("GET", f"/tracer/trace/{_quote(trace_id)}/")

    def voice_calls(self, **query: Any) -> Any:
        return self._raw_request("GET", "/tracer/trace/list_voice_calls/", query=query)

    def voice_call_detail(self, **query: Any) -> Any:
        return self._raw_request("GET", "/tracer/trace/voice_call_detail/", query=query)

    def properties(self, **query: Any) -> Any:
        return self._raw_request("GET", "/tracer/trace/get_properties/", query=query)

    def update_tags(self, trace_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "PATCH", f"/tracer/trace/{_quote(trace_id)}/tags/", body=body
        )

    def graph_methods(self, body: Any) -> Any:
        return self._raw_request("POST", "/tracer/trace/get_graph_methods/", body=body)

    def sessions(self, **query: Any) -> Any:
        return self._raw_request(
            "GET", "/tracer/trace-session/list_sessions/", query=query
        )

    def get_session(self, session_id: str | UUID) -> Any:
        return self._raw_request("GET", f"/tracer/trace-session/{_quote(session_id)}/")

    def session_graph(self, body: Any) -> Any:
        return self._raw_request(
            "POST", "/tracer/trace-session/get_session_graph_data/", body=body
        )

    def users(self, **query: Any) -> Any:
        return self._raw_request("GET", "/tracer/users/", query=query)

    def annotation_labels(self, **query: Any) -> Any:
        return self._raw_request("GET", "/tracer/get-annotation-labels/", query=query)

    def bulk_annotation(self, body: Any) -> Any:
        return self._raw_request("POST", "/tracer/bulk-annotation/", body=body)

    def issues(self, **query: Any) -> Any:
        return self._raw_request("GET", "/tracer/feed/issues/", query=query)

    def issue(self, cluster_id: str | UUID) -> Any:
        return self._raw_request("GET", f"/tracer/feed/issues/{_quote(cluster_id)}/")

    def issue_stats(self, **query: Any) -> Any:
        return self._raw_request("GET", "/tracer/feed/issues/stats/", query=query)


class UsersClient(BaseGeneratedClient):
    def current(self) -> Any:
        return self._raw_request("GET", "/accounts/user-info/")

    def organization_members(self, **query: Any) -> Any:
        return self._raw_request("GET", "/accounts/organization/members/", query=query)

    def workspaces(self, **query: Any) -> Any:
        return self._raw_request("GET", "/accounts/workspace/list/", query=query)

    def workspace_members(self, workspace_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET", f"/accounts/workspace/{_quote(workspace_id)}/members/", query=query
        )

    def switch_workspace(self, body: Any) -> Any:
        return self._raw_request("POST", "/accounts/workspace/switch/", body=body)


class AlertsClient(BaseGeneratedClient):
    def list(self, **query: Any) -> Any:
        return self._raw_request("GET", "/tracer/user-alerts/", query=query)

    def create(self, body: Any) -> Any:
        return self._raw_request("POST", "/tracer/user-alerts/", body=body)

    def get(self, alert_id: str | UUID) -> Any:
        return self._raw_request("GET", f"/tracer/user-alerts/{_quote(alert_id)}/")

    def update(self, alert_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "PATCH", f"/tracer/user-alerts/{_quote(alert_id)}/", body=body
        )

    def delete(self, alert_id: str | UUID) -> Any:
        return self._raw_request("DELETE", f"/tracer/user-alerts/{_quote(alert_id)}/")

    def metric_options(self, **query: Any) -> Any:
        return self._raw_request(
            "GET", "/tracer/user-alerts/metric-options/", query=query
        )

    def preview_graph(self, body: Any) -> Any:
        return self._raw_request(
            "POST", "/tracer/user-alerts/preview-graph/", body=body
        )

    def graph(self, alert_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET", f"/tracer/user-alerts/{_quote(alert_id)}/graph/", query=query
        )

    def details(self, alert_id: str | UUID) -> Any:
        return self._raw_request(
            "GET", f"/tracer/user-alerts/{_quote(alert_id)}/details/"
        )

    def bulk_mute(self, body: Any) -> Any:
        return self._raw_request("POST", "/tracer/user-alerts/bulk-mute/", body=body)

    def logs(self, **query: Any) -> Any:
        return self._raw_request("GET", "/tracer/user-alert-logs/", query=query)

    def all_logs(self, **query: Any) -> Any:
        return self._raw_request("GET", "/tracer/user-alert-logs/all/", query=query)

    def log(self, log_id: str | UUID) -> Any:
        return self._raw_request("GET", f"/tracer/user-alert-logs/{_quote(log_id)}/")

    def logs_for_alert(self, alert_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET", f"/tracer/user-alert-logs/{_quote(alert_id)}/list/", query=query
        )

    def resolve_logs(self, body: Any) -> Any:
        return self._raw_request("POST", "/tracer/user-alert-logs/resolve/", body=body)
