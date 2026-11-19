"""Prompt templates, versions and labels on the shared platform client.

The legacy ``fi.prompt.Prompt`` API is unchanged. Methods here return wire
mappings (or one page), unwrapping the server's ``status/result`` envelope.

``create`` makes the template and its first version in one call; commit that
version, label it, fetch it by label and render it locally with ``compile``.
"""

from __future__ import annotations

from typing import Any, Mapping

from fi._resources import AsyncCoreResource, CoreResource, JsonBody
from fi.errors import BadRequestError
from fi.prompts._compile import compile_prompt
from fi.generated.openapi_client.api.model_hub import (
    model_hub_prompt_labels_assign_label_by_id as assign_label,
    model_hub_prompt_labels_create as create_label,
    model_hub_prompt_labels_delete as delete_label,
    model_hub_prompt_labels_get_by_name as get_by_name,
    model_hub_prompt_labels_list as list_labels,
    model_hub_prompt_labels_partial_update as update_label,
    model_hub_prompt_labels_read as read_label,
    model_hub_prompt_labels_remove_label_from_version as remove_label,
    model_hub_prompt_labels_set_default as set_default,
    model_hub_prompt_labels_template_labels as template_labels,
    model_hub_prompt_templates_add_new_draft as create_version,
    model_hub_prompt_templates_commit as commit_version,
    model_hub_prompt_templates_create_draft as create_template,
    model_hub_prompt_templates_delete as delete_template,
    model_hub_prompt_templates_list as list_templates,
    model_hub_prompt_templates_partial_update as update_template,
    model_hub_prompt_templates_read as read_template,
    model_hub_prompt_templates_versions as list_versions,
)
from fi.generated.openapi_client.client import Client

__all__ = [
    "AsyncPromptLabelsClient", "AsyncPromptVersionsClient", "AsyncPromptsClient",
    "PromptLabelsClient", "PromptVersionsClient", "PromptsClient", "compile_prompt",
]


def _with_first_version(body: Mapping[str, Any]) -> JsonBody:
    """The create body: template fields plus ``prompt_config``, whose first entry becomes v1."""
    config = body.get("prompt_config")
    if not isinstance(config, (list, tuple)) or not config:
        raise ValueError(
            "prompt_config must be a non-empty list; its first entry (messages and model settings) becomes v1"
        )
    return JsonBody(body)


def _lookup_query(name: str, version: str | None, label: str | None) -> dict[str, str]:
    selected = version if version is not None else label
    if (version is None) == (label is None) or not isinstance(selected, str) or not selected.strip():
        message = "provide exactly one of version or label as a non-empty string; no default version is selected"
        raise BadRequestError(400, {"detail": message}, code="invalid_prompt_selector", message=message)
    return {"name": name, "version" if version is not None else "label": selected}


class PromptLabelsClient(CoreResource):
    def list(self, **query: Any) -> Any:
        """Pagination: limit (page size); page (1-based)."""
        return self._request(list_labels, query=query)

    def create(self, body: Mapping[str, Any]) -> Any:
        return self._request(create_label, body=JsonBody(body))

    def get(self, label_id: str) -> Any:
        return self._request(read_label, label_id)

    def update(self, label_id: str, body: Mapping[str, Any]) -> Any:
        return self._request(update_label, label_id, body=JsonBody(body))

    def delete(self, label_id: str) -> Any:
        return self._request(delete_label, label_id)

    def assign(self, template_id: str, label_id: str, *, version: str) -> Any:
        """Assign an existing label to a committed version; never creates a label."""
        return self._request(assign_label, template_id, label_id, body=JsonBody({"version": version}))

    def remove(self, version_id: str, label_id: str) -> Any:
        return self._request(remove_label, body=JsonBody({"version_id": version_id, "label_id": label_id}))

    def for_template(self, template_id: str) -> Any:
        """Pagination: no supported paging parameters."""
        return self._request(template_labels, query={"template_id": template_id})


class PromptVersionsClient(CoreResource):
    def list(self, template_id: str, **query: Any) -> Any:
        """Pagination: page (1-based); limit (page size)."""
        return self._request(list_versions, template_id, query=query)

    def create(self, template_id: str, body: Mapping[str, Any]) -> Any:
        """Create a new draft from a template."""
        return self._request(create_version, template_id, body=JsonBody(body))

    def commit(self, template_id: str, version: str, *, message: str = "", set_default: bool = False) -> Any:
        return self._request(commit_version, template_id, body=JsonBody({"version_name": version, "message": message, "set_default": set_default, "is_draft": False}))

    def set_default(self, template_name: str, version: str) -> Any:
        return self._request(set_default, body=JsonBody({"template_name": template_name, "version": version}))


class PromptsClient(CoreResource):
    """Template CRUD plus ``versions``, ``labels`` and pure local ``compile``."""

    def __init__(self, client: Client) -> None:
        super().__init__(client)
        self.labels = PromptLabelsClient(client)
        self.versions = PromptVersionsClient(client)

    def list(self, **query: Any) -> Any:
        """Pagination: limit (page size); page (1-based)."""
        return self._request(list_templates, query=query)

    def create(self, body: Mapping[str, Any]) -> Any:
        """Create a template and its first version (v1, a draft until committed) in one call.

        ``body`` holds ``name`` and ``prompt_config`` (a list; its first entry becomes v1), and
        optionally ``description``, ``variable_names``, ``metadata`` and ``prompt_folder``. The
        result carries the template ``id`` and ``created_version``; commit that version next.
        """
        return self._request(create_template, body=_with_first_version(body))

    def get(self, template_id: str) -> Any:
        return self._request(read_template, template_id)

    def get_by_name(self, name: str, *, version: str | None = None, label: str | None = None) -> Any:
        """Fetch by template name and exactly one non-empty ``version`` or ``label``.

        No default version is selected when the selector is omitted. Missing, empty
        or conflicting selectors raise ``BadRequestError`` before any request.

        Pagination: no supported paging parameters."""
        return self._request(get_by_name, query=_lookup_query(name, version, label))

    def get_by_label(self, name: str, label: str) -> Any:
        return self.get_by_name(name, label=label)

    def update(self, template_id: str, body: Mapping[str, Any]) -> Any:
        return self._request(update_template, template_id, body=JsonBody(body))

    def delete(self, template_id: str) -> Any:
        return self._request(delete_template, template_id)

    @staticmethod
    def compile(template: Mapping[str, Any], variables: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        return compile_prompt(template, variables)


class AsyncPromptLabelsClient(AsyncCoreResource):
    async def list(self, **query: Any) -> Any:
        """Pagination: limit (page size); page (1-based)."""
        return await self._request(list_labels, query=query)

    async def create(self, body: Mapping[str, Any]) -> Any:
        return await self._request(create_label, body=JsonBody(body))

    async def get(self, label_id: str) -> Any:
        return await self._request(read_label, label_id)

    async def update(self, label_id: str, body: Mapping[str, Any]) -> Any:
        return await self._request(update_label, label_id, body=JsonBody(body))

    async def delete(self, label_id: str) -> Any:
        return await self._request(delete_label, label_id)

    async def assign(self, template_id: str, label_id: str, *, version: str) -> Any:
        return await self._request(assign_label, template_id, label_id, body=JsonBody({"version": version}))

    async def remove(self, version_id: str, label_id: str) -> Any:
        return await self._request(remove_label, body=JsonBody({"version_id": version_id, "label_id": label_id}))

    async def for_template(self, template_id: str) -> Any:
        """Pagination: no supported paging parameters."""
        return await self._request(template_labels, query={"template_id": template_id})


class AsyncPromptVersionsClient(AsyncCoreResource):
    async def list(self, template_id: str, **query: Any) -> Any:
        """Pagination: page (1-based); limit (page size)."""
        return await self._request(list_versions, template_id, query=query)

    async def create(self, template_id: str, body: Mapping[str, Any]) -> Any:
        return await self._request(create_version, template_id, body=JsonBody(body))

    async def commit(self, template_id: str, version: str, *, message: str = "", set_default: bool = False) -> Any:
        return await self._request(commit_version, template_id, body=JsonBody({"version_name": version, "message": message, "set_default": set_default, "is_draft": False}))

    async def set_default(self, template_name: str, version: str) -> Any:
        return await self._request(set_default, body=JsonBody({"template_name": template_name, "version": version}))


class AsyncPromptsClient(AsyncCoreResource):
    def __init__(self, client: Client) -> None:
        super().__init__(client)
        self.labels = AsyncPromptLabelsClient(client)
        self.versions = AsyncPromptVersionsClient(client)

    async def list(self, **query: Any) -> Any:
        """Pagination: limit (page size); page (1-based)."""
        return await self._request(list_templates, query=query)

    async def create(self, body: Mapping[str, Any]) -> Any:
        """Create a template and its first version (v1, a draft until committed) in one call."""
        return await self._request(create_template, body=_with_first_version(body))

    async def get(self, template_id: str) -> Any:
        return await self._request(read_template, template_id)

    async def get_by_name(self, name: str, *, version: str | None = None, label: str | None = None) -> Any:
        """Fetch by template name and exactly one non-empty ``version`` or ``label``.

        No default version is selected when the selector is omitted. Missing, empty
        or conflicting selectors raise ``BadRequestError`` before any request.

        Pagination: no supported paging parameters."""
        return await self._request(get_by_name, query=_lookup_query(name, version, label))

    async def get_by_label(self, name: str, label: str) -> Any:
        return await self.get_by_name(name, label=label)

    async def update(self, template_id: str, body: Mapping[str, Any]) -> Any:
        return await self._request(update_template, template_id, body=JsonBody(body))

    async def delete(self, template_id: str) -> Any:
        return await self._request(delete_template, template_id)

    @staticmethod
    def compile(template: Mapping[str, Any], variables: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        return compile_prompt(template, variables)
