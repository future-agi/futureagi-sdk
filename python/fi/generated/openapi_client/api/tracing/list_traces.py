from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.list_traces_response_200 import ListTracesResponse200
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    project_version_id: UUID,
    trace_ids: str | Unset = UNSET,
    filters: str | Unset = "[]",
    sort_params: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["page"] = page

    params["limit"] = limit

    json_project_version_id = str(project_version_id)
    params["project_version_id"] = json_project_version_id

    params["trace_ids"] = trace_ids

    params["filters"] = filters

    params["sort_params"] = sort_params

    params["page_number"] = page_number

    params["page_size"] = page_size

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/tracer/trace/list_traces/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ListTracesResponse200 | ManagementAPIErrorResponse:
    if response.status_code == 200:
        response_200 = ListTracesResponse200.from_dict(response.json())

        return response_200

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ListTracesResponse200 | ManagementAPIErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    project_version_id: UUID,
    trace_ids: str | Unset = UNSET,
    filters: str | Unset = "[]",
    sort_params: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
) -> Response[ListTracesResponse200 | ManagementAPIErrorResponse]:
    """List traces filtered by project ID and project version ID with optimized queries.

    Args:
        page (int | Unset):
        limit (int | Unset):
        project_version_id (UUID):
        trace_ids (str | Unset):
        filters (str | Unset):  Default: '[]'.
        sort_params (str | Unset):  Default: '[]'.
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 30.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ListTracesResponse200 | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
        project_version_id=project_version_id,
        trace_ids=trace_ids,
        filters=filters,
        sort_params=sort_params,
        page_number=page_number,
        page_size=page_size,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    project_version_id: UUID,
    trace_ids: str | Unset = UNSET,
    filters: str | Unset = "[]",
    sort_params: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
) -> ListTracesResponse200 | ManagementAPIErrorResponse | None:
    """List traces filtered by project ID and project version ID with optimized queries.

    Args:
        page (int | Unset):
        limit (int | Unset):
        project_version_id (UUID):
        trace_ids (str | Unset):
        filters (str | Unset):  Default: '[]'.
        sort_params (str | Unset):  Default: '[]'.
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 30.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ListTracesResponse200 | ManagementAPIErrorResponse
    """

    return sync_detailed(
        client=client,
        page=page,
        limit=limit,
        project_version_id=project_version_id,
        trace_ids=trace_ids,
        filters=filters,
        sort_params=sort_params,
        page_number=page_number,
        page_size=page_size,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    project_version_id: UUID,
    trace_ids: str | Unset = UNSET,
    filters: str | Unset = "[]",
    sort_params: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
) -> Response[ListTracesResponse200 | ManagementAPIErrorResponse]:
    """List traces filtered by project ID and project version ID with optimized queries.

    Args:
        page (int | Unset):
        limit (int | Unset):
        project_version_id (UUID):
        trace_ids (str | Unset):
        filters (str | Unset):  Default: '[]'.
        sort_params (str | Unset):  Default: '[]'.
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 30.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ListTracesResponse200 | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
        project_version_id=project_version_id,
        trace_ids=trace_ids,
        filters=filters,
        sort_params=sort_params,
        page_number=page_number,
        page_size=page_size,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    project_version_id: UUID,
    trace_ids: str | Unset = UNSET,
    filters: str | Unset = "[]",
    sort_params: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
) -> ListTracesResponse200 | ManagementAPIErrorResponse | None:
    """List traces filtered by project ID and project version ID with optimized queries.

    Args:
        page (int | Unset):
        limit (int | Unset):
        project_version_id (UUID):
        trace_ids (str | Unset):
        filters (str | Unset):  Default: '[]'.
        sort_params (str | Unset):  Default: '[]'.
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 30.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ListTracesResponse200 | ManagementAPIErrorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            page=page,
            limit=limit,
            project_version_id=project_version_id,
            trace_ids=trace_ids,
            filters=filters,
            sort_params=sort_params,
            page_number=page_number,
            page_size=page_size,
        )
    ).parsed
