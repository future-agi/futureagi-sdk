from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.model_hub_prompt_history_executions_get_execution_details_response_200 import (
    ModelHubPromptHistoryExecutionsGetExecutionDetailsResponse200,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    execution_id: str,
    *,
    template_name: str | Unset = UNSET,
    template_version: str | Unset = UNSET,
    created_at: str | Unset = UNSET,
    search: str | Unset = UNSET,
    ordering: str | Unset = UNSET,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["template_name"] = template_name

    params["template_version"] = template_version

    params["created_at"] = created_at

    params["search"] = search

    params["ordering"] = ordering

    params["page"] = page

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/model-hub/prompt-history-executions/execution-details/{execution_id}/".format(
            execution_id=quote(str(execution_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ManagementAPIErrorResponse
    | ModelHubPromptHistoryExecutionsGetExecutionDetailsResponse200
):
    if response.status_code == 200:
        response_200 = (
            ModelHubPromptHistoryExecutionsGetExecutionDetailsResponse200.from_dict(
                response.json()
            )
        )

        return response_200

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ManagementAPIErrorResponse
    | ModelHubPromptHistoryExecutionsGetExecutionDetailsResponse200
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    execution_id: str,
    *,
    client: AuthenticatedClient | Client,
    template_name: str | Unset = UNSET,
    template_version: str | Unset = UNSET,
    created_at: str | Unset = UNSET,
    search: str | Unset = UNSET,
    ordering: str | Unset = UNSET,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
) -> Response[
    ManagementAPIErrorResponse
    | ModelHubPromptHistoryExecutionsGetExecutionDetailsResponse200
]:
    """Get detailed information about a specific PromptVersion

    Args:
        execution_id (str):
        template_name (str | Unset):
        template_version (str | Unset):
        created_at (str | Unset):
        search (str | Unset):
        ordering (str | Unset):
        page (int | Unset):
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ModelHubPromptHistoryExecutionsGetExecutionDetailsResponse200]
    """

    kwargs = _get_kwargs(
        execution_id=execution_id,
        template_name=template_name,
        template_version=template_version,
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
    execution_id: str,
    *,
    client: AuthenticatedClient | Client,
    template_name: str | Unset = UNSET,
    template_version: str | Unset = UNSET,
    created_at: str | Unset = UNSET,
    search: str | Unset = UNSET,
    ordering: str | Unset = UNSET,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
) -> (
    ManagementAPIErrorResponse
    | ModelHubPromptHistoryExecutionsGetExecutionDetailsResponse200
    | None
):
    """Get detailed information about a specific PromptVersion

    Args:
        execution_id (str):
        template_name (str | Unset):
        template_version (str | Unset):
        created_at (str | Unset):
        search (str | Unset):
        ordering (str | Unset):
        page (int | Unset):
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ModelHubPromptHistoryExecutionsGetExecutionDetailsResponse200
    """

    return sync_detailed(
        execution_id=execution_id,
        client=client,
        template_name=template_name,
        template_version=template_version,
        created_at=created_at,
        search=search,
        ordering=ordering,
        page=page,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    execution_id: str,
    *,
    client: AuthenticatedClient | Client,
    template_name: str | Unset = UNSET,
    template_version: str | Unset = UNSET,
    created_at: str | Unset = UNSET,
    search: str | Unset = UNSET,
    ordering: str | Unset = UNSET,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
) -> Response[
    ManagementAPIErrorResponse
    | ModelHubPromptHistoryExecutionsGetExecutionDetailsResponse200
]:
    """Get detailed information about a specific PromptVersion

    Args:
        execution_id (str):
        template_name (str | Unset):
        template_version (str | Unset):
        created_at (str | Unset):
        search (str | Unset):
        ordering (str | Unset):
        page (int | Unset):
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ModelHubPromptHistoryExecutionsGetExecutionDetailsResponse200]
    """

    kwargs = _get_kwargs(
        execution_id=execution_id,
        template_name=template_name,
        template_version=template_version,
        created_at=created_at,
        search=search,
        ordering=ordering,
        page=page,
        limit=limit,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    execution_id: str,
    *,
    client: AuthenticatedClient | Client,
    template_name: str | Unset = UNSET,
    template_version: str | Unset = UNSET,
    created_at: str | Unset = UNSET,
    search: str | Unset = UNSET,
    ordering: str | Unset = UNSET,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
) -> (
    ManagementAPIErrorResponse
    | ModelHubPromptHistoryExecutionsGetExecutionDetailsResponse200
    | None
):
    """Get detailed information about a specific PromptVersion

    Args:
        execution_id (str):
        template_name (str | Unset):
        template_version (str | Unset):
        created_at (str | Unset):
        search (str | Unset):
        ordering (str | Unset):
        page (int | Unset):
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ModelHubPromptHistoryExecutionsGetExecutionDetailsResponse200
    """

    return (
        await asyncio_detailed(
            execution_id=execution_id,
            client=client,
            template_name=template_name,
            template_version=template_version,
            created_at=created_at,
            search=search,
            ordering=ordering,
            page=page,
            limit=limit,
        )
    ).parsed
