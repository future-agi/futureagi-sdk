"""Scores and annotation labels over generated core operations."""

from __future__ import annotations

from typing import Any, Mapping

from fi._resources import AsyncCoreResource, CoreResource, JsonBody
from fi.generated.openapi_client.api.model_hub import (
    model_hub_annotations_labels_create as create_label,
    model_hub_annotations_labels_delete as delete_label,
    model_hub_annotations_labels_list as list_labels,
    model_hub_annotations_labels_partial_update as update_label,
    model_hub_annotations_labels_read as read_label,
    model_hub_annotations_labels_restore as restore_label,
    model_hub_scores_bulk_create as create_scores,
    model_hub_scores_create as create_score,
    model_hub_scores_delete as delete_score,
    model_hub_scores_for_source as source_scores,
    model_hub_scores_list as list_scores,
    model_hub_scores_partial_update as update_score,
    model_hub_scores_read as read_score,
)
from fi.generated.openapi_client.client import Client
from fi.generated.openapi_client.models.model_hub_scores_for_source_source_type import (
    ModelHubScoresForSourceSourceType,
)


class AnnotationLabelsClient(CoreResource):
    def list(self, **query: Any) -> Any:
        """Pagination: page (1-based); limit (page size)."""
        return self._request(list_labels, query=query)

    def create(self, body: Mapping[str, Any]) -> Any:
        return self._request(create_label, body=JsonBody(body))

    def get(self, label_id: str) -> Any:
        return self._request(read_label, label_id)

    def update(self, label_id: str, body: Mapping[str, Any]) -> Any:
        return self._request(update_label, label_id, body=JsonBody(body))

    def delete(self, label_id: str) -> Any:
        """Archive a label; restore makes it available again."""
        return self._request(delete_label, label_id)

    def restore(self, label_id: str) -> Any:
        return self._request(restore_label, label_id, body=JsonBody({}))


class ScoresClient(CoreResource):
    def __init__(self, client: Client) -> None:
        super().__init__(client)
        self.labels = AnnotationLabelsClient(client)

    def list(self, **query: Any) -> Any:
        """Pagination: no supported paging parameters. The strict list serializer does not admit page or limit; the server returns its default page."""
        return self._request(list_scores, query=query)

    def create(self, body: Mapping[str, Any]) -> Any:
        return self._request(create_score, body=JsonBody(body))

    def bulk_create(self, body: Mapping[str, Any]) -> Any:
        return self._request(create_scores, body=JsonBody(body))

    def get(self, score_id: str) -> Any:
        return self._request(read_score, score_id)

    def update(self, score_id: str, body: Mapping[str, Any]) -> Any:
        return self._request(update_score, score_id, body=JsonBody(body))

    def delete(self, score_id: str) -> Any:
        return self._request(delete_score, score_id)

    def for_source(self, source_type: str, source_id: str, **query: Any) -> Any:
        """Return the complete response: scores in ``result`` and optional ``span_notes``.

        Pagination: no supported paging parameters."""
        return self._request(
            source_scores, source_type=ModelHubScoresForSourceSourceType(source_type),
            source_id=source_id, query=query, unwrap_result=False,
        )


class AsyncAnnotationLabelsClient(AsyncCoreResource):
    async def list(self, **query: Any) -> Any:
        """Pagination: page (1-based); limit (page size)."""
        return await self._request(list_labels, query=query)

    async def create(self, body: Mapping[str, Any]) -> Any:
        return await self._request(create_label, body=JsonBody(body))

    async def get(self, label_id: str) -> Any:
        return await self._request(read_label, label_id)

    async def update(self, label_id: str, body: Mapping[str, Any]) -> Any:
        return await self._request(update_label, label_id, body=JsonBody(body))

    async def delete(self, label_id: str) -> Any:
        return await self._request(delete_label, label_id)

    async def restore(self, label_id: str) -> Any:
        return await self._request(restore_label, label_id, body=JsonBody({}))


class AsyncScoresClient(AsyncCoreResource):
    def __init__(self, client: Client) -> None:
        super().__init__(client)
        self.labels = AsyncAnnotationLabelsClient(client)

    async def list(self, **query: Any) -> Any:
        """Pagination: no supported paging parameters. The strict list serializer does not admit page or limit; the server returns its default page."""
        return await self._request(list_scores, query=query)

    async def create(self, body: Mapping[str, Any]) -> Any:
        return await self._request(create_score, body=JsonBody(body))

    async def bulk_create(self, body: Mapping[str, Any]) -> Any:
        return await self._request(create_scores, body=JsonBody(body))

    async def get(self, score_id: str) -> Any:
        return await self._request(read_score, score_id)

    async def update(self, score_id: str, body: Mapping[str, Any]) -> Any:
        return await self._request(update_score, score_id, body=JsonBody(body))

    async def delete(self, score_id: str) -> Any:
        return await self._request(delete_score, score_id)

    async def for_source(self, source_type: str, source_id: str, **query: Any) -> Any:
        """Return the complete response: scores in ``result`` and optional ``span_notes``.

        Pagination: no supported paging parameters."""
        return await self._request(
            source_scores, source_type=ModelHubScoresForSourceSourceType(source_type),
            source_id=source_id, query=query, unwrap_result=False,
        )
