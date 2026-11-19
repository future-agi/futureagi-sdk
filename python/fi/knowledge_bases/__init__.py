"""Knowledge-base CRUD and document uploads using the shared generated client."""

from __future__ import annotations

from typing import Any, Mapping

from fi._resources import AsyncCoreResource, CoreResource, JsonBody
from fi.generated.openapi_client.api.model_hub import (
    model_hub_knowledge_base_create as create_kb,
    model_hub_knowledge_base_delete as delete_kb,
    model_hub_knowledge_base_files_create as list_files,
    model_hub_knowledge_base_files_delete as delete_files,
    model_hub_knowledge_base_list_list as list_kbs,
    model_hub_knowledge_base_partial_update as update_kb,
)
from fi.generated.openapi_client.client import Client


def _document(name: str, text: str) -> list[tuple[str, tuple[str, bytes, str]]]:
    if not name or any(char in name for char in ("/", "\\", "\r", "\n", "\x00")):
        raise ValueError("document name must be a filename, not a path")
    if not name.lower().endswith(".txt"):
        raise ValueError("text documents must use a .txt filename")
    return [("file", (name, text.encode("utf-8"), "text/plain"))]


class KnowledgeBaseDocumentsClient(CoreResource):
    def list(self, kb_id: str, **query: Any) -> Any:
        """List files with the server's zero-based page_number/page_size fields.

        Pagination: page_number (0-based); page_size (page size). Pass these in the request body."""
        return self._request(list_files, body=JsonBody({**query, "kb_id": kb_id}))

    def add_text(self, kb_id: str, name: str, text: str) -> Any:
        """Upload UTF-8 text via the generated update operation's multipart form."""
        return self._request(update_kb, body=JsonBody({"kb_id": kb_id}), files=_document(name, text))

    def delete(self, kb_id: str, file_names: list[str]) -> Any:
        if not file_names:
            raise ValueError("at least one filename is required")
        return self._request(delete_files, body=JsonBody({"kb_id": kb_id, "file_names": file_names}))


class KnowledgeBasesClient(CoreResource):
    def __init__(self, client: Client) -> None:
        super().__init__(client)
        self.documents = KnowledgeBaseDocumentsClient(client)

    def list(self, *, search: str | None = None) -> Any:
        return self._request(list_kbs, query={"search": search})

    def create(self, name: str) -> Any:
        return self._request(create_kb, body=JsonBody({"name": name}))

    def update(self, kb_id: str, body: Mapping[str, Any]) -> Any:
        """Rename with ``{\"name\": ...}``; upload content through ``documents``."""
        return self._request(update_kb, body=JsonBody({**body, "kb_id": kb_id}))

    def delete(self, kb_id: str) -> Any:
        return self._request(delete_kb, body=JsonBody({"kb_ids": [kb_id]}))


class AsyncKnowledgeBaseDocumentsClient(AsyncCoreResource):
    async def list(self, kb_id: str, **query: Any) -> Any:
        """Pagination: page_number (0-based); page_size (page size). Pass these in the request body."""
        return await self._request(list_files, body=JsonBody({**query, "kb_id": kb_id}))

    async def add_text(self, kb_id: str, name: str, text: str) -> Any:
        return await self._request(update_kb, body=JsonBody({"kb_id": kb_id}), files=_document(name, text))

    async def delete(self, kb_id: str, file_names: list[str]) -> Any:
        if not file_names:
            raise ValueError("at least one filename is required")
        return await self._request(delete_files, body=JsonBody({"kb_id": kb_id, "file_names": file_names}))


class AsyncKnowledgeBasesClient(AsyncCoreResource):
    def __init__(self, client: Client) -> None:
        super().__init__(client)
        self.documents = AsyncKnowledgeBaseDocumentsClient(client)

    async def list(self, *, search: str | None = None) -> Any:
        return await self._request(list_kbs, query={"search": search})

    async def create(self, name: str) -> Any:
        return await self._request(create_kb, body=JsonBody({"name": name}))

    async def update(self, kb_id: str, body: Mapping[str, Any]) -> Any:
        return await self._request(update_kb, body=JsonBody({**body, "kb_id": kb_id}))

    async def delete(self, kb_id: str) -> Any:
        return await self._request(delete_kb, body=JsonBody({"kb_ids": [kb_id]}))
