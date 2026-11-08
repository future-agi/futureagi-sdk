from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.list_trace_projects_sort_direction import ListTraceProjectsSortDirection
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.project_list_response import ProjectListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    name: str | Unset = UNSET,
    project_type: str | Unset = UNSET,
    tags: str | Unset = UNSET,
    filters: str | Unset = "[]",
    sort_by: str | Unset = "created_at",
    sort_direction: ListTraceProjectsSortDirection
    | Unset = ListTraceProjectsSortDirection.DESC,
    page_number: int | Unset = 0,
    page_size: int | Unset = 20,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["name"] = name

    params["project_type"] = project_type

    params["tags"] = tags

    params["filters"] = filters

    params["sort_by"] = sort_by

    json_sort_direction: str | Unset = UNSET
    if not isinstance(sort_direction, Unset):
        json_sort_direction = sort_direction.value

    params["sort_direction"] = json_sort_direction

    params["page_number"] = page_number

    params["page_size"] = page_size

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/tracer/project/list_projects/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ManagementAPIErrorResponse | ProjectListResponse:
    if response.status_code == 200:
        response_200 = ProjectListResponse.from_dict(response.json())

        return response_200

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ManagementAPIErrorResponse | ProjectListResponse]:
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
    project_type: str | Unset = UNSET,
    tags: str | Unset = UNSET,
    filters: str | Unset = "[]",
    sort_by: str | Unset = "created_at",
    sort_direction: ListTraceProjectsSortDirection
    | Unset = ListTraceProjectsSortDirection.DESC,
    page_number: int | Unset = 0,
    page_size: int | Unset = 20,
) -> Response[ManagementAPIErrorResponse | ProjectListResponse]:
    """List projects filtered by organization ID.

     Volume counts come from ClickHouse (fast) instead of a PG
    JOIN on observation_spans (was 12+ seconds).

    Pagination: page_number (0-based); page_size (page size).

    Args:
        name (str | Unset):
        project_type (str | Unset):
        tags (str | Unset):
        filters (str | Unset):  Default: '[]'.
        sort_by (str | Unset):  Default: 'created_at'.
        sort_direction (ListTraceProjectsSortDirection | Unset):  Default:
            ListTraceProjectsSortDirection.DESC.
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 20.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ProjectListResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        project_type=project_type,
        tags=tags,
        filters=filters,
        sort_by=sort_by,
        sort_direction=sort_direction,
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
    name: str | Unset = UNSET,
    project_type: str | Unset = UNSET,
    tags: str | Unset = UNSET,
    filters: str | Unset = "[]",
    sort_by: str | Unset = "created_at",
    sort_direction: ListTraceProjectsSortDirection
    | Unset = ListTraceProjectsSortDirection.DESC,
    page_number: int | Unset = 0,
    page_size: int | Unset = 20,
) -> ManagementAPIErrorResponse | ProjectListResponse | None:
    """List projects filtered by organization ID.

     Volume counts come from ClickHouse (fast) instead of a PG
    JOIN on observation_spans (was 12+ seconds).

    Pagination: page_number (0-based); page_size (page size).

    Args:
        name (str | Unset):
        project_type (str | Unset):
        tags (str | Unset):
        filters (str | Unset):  Default: '[]'.
        sort_by (str | Unset):  Default: 'created_at'.
        sort_direction (ListTraceProjectsSortDirection | Unset):  Default:
            ListTraceProjectsSortDirection.DESC.
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 20.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ProjectListResponse
    """

    return sync_detailed(
        client=client,
        name=name,
        project_type=project_type,
        tags=tags,
        filters=filters,
        sort_by=sort_by,
        sort_direction=sort_direction,
        page_number=page_number,
        page_size=page_size,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    name: str | Unset = UNSET,
    project_type: str | Unset = UNSET,
    tags: str | Unset = UNSET,
    filters: str | Unset = "[]",
    sort_by: str | Unset = "created_at",
    sort_direction: ListTraceProjectsSortDirection
    | Unset = ListTraceProjectsSortDirection.DESC,
    page_number: int | Unset = 0,
    page_size: int | Unset = 20,
) -> Response[ManagementAPIErrorResponse | ProjectListResponse]:
    """List projects filtered by organization ID.

     Volume counts come from ClickHouse (fast) instead of a PG
    JOIN on observation_spans (was 12+ seconds).

    Pagination: page_number (0-based); page_size (page size).

    Args:
        name (str | Unset):
        project_type (str | Unset):
        tags (str | Unset):
        filters (str | Unset):  Default: '[]'.
        sort_by (str | Unset):  Default: 'created_at'.
        sort_direction (ListTraceProjectsSortDirection | Unset):  Default:
            ListTraceProjectsSortDirection.DESC.
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 20.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ProjectListResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        project_type=project_type,
        tags=tags,
        filters=filters,
        sort_by=sort_by,
        sort_direction=sort_direction,
        page_number=page_number,
        page_size=page_size,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    name: str | Unset = UNSET,
    project_type: str | Unset = UNSET,
    tags: str | Unset = UNSET,
    filters: str | Unset = "[]",
    sort_by: str | Unset = "created_at",
    sort_direction: ListTraceProjectsSortDirection
    | Unset = ListTraceProjectsSortDirection.DESC,
    page_number: int | Unset = 0,
    page_size: int | Unset = 20,
) -> ManagementAPIErrorResponse | ProjectListResponse | None:
    """List projects filtered by organization ID.

     Volume counts come from ClickHouse (fast) instead of a PG
    JOIN on observation_spans (was 12+ seconds).

    Pagination: page_number (0-based); page_size (page size).

    Args:
        name (str | Unset):
        project_type (str | Unset):
        tags (str | Unset):
        filters (str | Unset):  Default: '[]'.
        sort_by (str | Unset):  Default: 'created_at'.
        sort_direction (ListTraceProjectsSortDirection | Unset):  Default:
            ListTraceProjectsSortDirection.DESC.
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 20.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ProjectListResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            name=name,
            project_type=project_type,
            tags=tags,
            filters=filters,
            sort_by=sort_by,
            sort_direction=sort_direction,
            page_number=page_number,
            page_size=page_size,
        )
    ).parsed
