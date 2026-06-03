from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.model_hub_prompt_templates_get_template_by_name_response_200 import (
    ModelHubPromptTemplatesGetTemplateByNameResponse200,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    name: str | Unset = UNSET,
    version: str | Unset = UNSET,
    created_at: str | Unset = UNSET,
    search: str | Unset = UNSET,
    ordering: str | Unset = UNSET,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["name"] = name

    params["version"] = version

    params["created_at"] = created_at

    params["search"] = search

    params["ordering"] = ordering

    params["page"] = page

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/model-hub/prompt-templates/get-template-by-name/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ManagementAPIErrorResponse | ModelHubPromptTemplatesGetTemplateByNameResponse200:
    if response.status_code == 200:
        response_200 = ModelHubPromptTemplatesGetTemplateByNameResponse200.from_dict(
            response.json()
        )

        return response_200

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ManagementAPIErrorResponse | ModelHubPromptTemplatesGetTemplateByNameResponse200
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    name: str | Unset = UNSET,
    version: str | Unset = UNSET,
    created_at: str | Unset = UNSET,
    search: str | Unset = UNSET,
    ordering: str | Unset = UNSET,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
) -> Response[
    ManagementAPIErrorResponse | ModelHubPromptTemplatesGetTemplateByNameResponse200
]:
    """Retrieve a prompt template by name.
    If no version is specified, returns the default version (is_default=True).
    If a version is specified, returns that specific version.

    Args:
        name (str | Unset):
        version (str | Unset):
        created_at (str | Unset):
        search (str | Unset):
        ordering (str | Unset):
        page (int | Unset):
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ModelHubPromptTemplatesGetTemplateByNameResponse200]
    """

    kwargs = _get_kwargs(
        name=name,
        version=version,
        created_at=created_at,
        search=search,
        ordering=ordering,
        page=page,
        limit=limit,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    name: str | Unset = UNSET,
    version: str | Unset = UNSET,
    created_at: str | Unset = UNSET,
    search: str | Unset = UNSET,
    ordering: str | Unset = UNSET,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
) -> (
    ManagementAPIErrorResponse
    | ModelHubPromptTemplatesGetTemplateByNameResponse200
    | None
):
    """Retrieve a prompt template by name.
    If no version is specified, returns the default version (is_default=True).
    If a version is specified, returns that specific version.

    Args:
        name (str | Unset):
        version (str | Unset):
        created_at (str | Unset):
        search (str | Unset):
        ordering (str | Unset):
        page (int | Unset):
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ModelHubPromptTemplatesGetTemplateByNameResponse200
    """

    return sync_detailed(
        client=client,
        name=name,
        version=version,
        created_at=created_at,
        search=search,
        ordering=ordering,
        page=page,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    name: str | Unset = UNSET,
    version: str | Unset = UNSET,
    created_at: str | Unset = UNSET,
    search: str | Unset = UNSET,
    ordering: str | Unset = UNSET,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
) -> Response[
    ManagementAPIErrorResponse | ModelHubPromptTemplatesGetTemplateByNameResponse200
]:
    """Retrieve a prompt template by name.
    If no version is specified, returns the default version (is_default=True).
    If a version is specified, returns that specific version.

    Args:
        name (str | Unset):
        version (str | Unset):
        created_at (str | Unset):
        search (str | Unset):
        ordering (str | Unset):
        page (int | Unset):
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ModelHubPromptTemplatesGetTemplateByNameResponse200]
    """

    kwargs = _get_kwargs(
        name=name,
        version=version,
        created_at=created_at,
        search=search,
        ordering=ordering,
        page=page,
        limit=limit,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    name: str | Unset = UNSET,
    version: str | Unset = UNSET,
    created_at: str | Unset = UNSET,
    search: str | Unset = UNSET,
    ordering: str | Unset = UNSET,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
) -> (
    ManagementAPIErrorResponse
    | ModelHubPromptTemplatesGetTemplateByNameResponse200
    | None
):
    """Retrieve a prompt template by name.
    If no version is specified, returns the default version (is_default=True).
    If a version is specified, returns that specific version.

    Args:
        name (str | Unset):
        version (str | Unset):
        created_at (str | Unset):
        search (str | Unset):
        ordering (str | Unset):
        page (int | Unset):
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ModelHubPromptTemplatesGetTemplateByNameResponse200
    """

    return (
        await asyncio_detailed(
            client=client,
            name=name,
            version=version,
            created_at=created_at,
            search=search,
            ordering=ordering,
            page=page,
            limit=limit,
        )
    ).parsed
