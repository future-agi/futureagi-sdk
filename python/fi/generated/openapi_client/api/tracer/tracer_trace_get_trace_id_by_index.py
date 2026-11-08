from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.trace_navigation_response import TraceNavigationResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    trace_id: UUID,
    project_version_id: UUID,
    filters: str | Unset = "[]",
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_trace_id = str(trace_id)
    params["trace_id"] = json_trace_id

    json_project_version_id = str(project_version_id)
    params["project_version_id"] = json_project_version_id

    params["filters"] = filters

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/tracer/trace/get_trace_id_by_index/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ManagementAPIErrorResponse | TraceNavigationResponse:
    if response.status_code == 200:
        response_200 = TraceNavigationResponse.from_dict(response.json())

        return response_200

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ManagementAPIErrorResponse | TraceNavigationResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    trace_id: UUID,
    project_version_id: UUID,
    filters: str | Unset = "[]",
) -> Response[ManagementAPIErrorResponse | TraceNavigationResponse]:
    """Get the previous and next trace id by index using efficient database queries.

    Pagination: no supported paging parameters.

    Args:
        trace_id (UUID):
        project_version_id (UUID):
        filters (str | Unset):  Default: '[]'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | TraceNavigationResponse]
    """

    kwargs = _get_kwargs(
        trace_id=trace_id,
        project_version_id=project_version_id,
        filters=filters,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    trace_id: UUID,
    project_version_id: UUID,
    filters: str | Unset = "[]",
) -> ManagementAPIErrorResponse | TraceNavigationResponse | None:
    """Get the previous and next trace id by index using efficient database queries.

    Pagination: no supported paging parameters.

    Args:
        trace_id (UUID):
        project_version_id (UUID):
        filters (str | Unset):  Default: '[]'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | TraceNavigationResponse
    """

    return sync_detailed(
        client=client,
        trace_id=trace_id,
        project_version_id=project_version_id,
        filters=filters,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    trace_id: UUID,
    project_version_id: UUID,
    filters: str | Unset = "[]",
) -> Response[ManagementAPIErrorResponse | TraceNavigationResponse]:
    """Get the previous and next trace id by index using efficient database queries.

    Pagination: no supported paging parameters.

    Args:
        trace_id (UUID):
        project_version_id (UUID):
        filters (str | Unset):  Default: '[]'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | TraceNavigationResponse]
    """

    kwargs = _get_kwargs(
        trace_id=trace_id,
        project_version_id=project_version_id,
        filters=filters,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    trace_id: UUID,
    project_version_id: UUID,
    filters: str | Unset = "[]",
) -> ManagementAPIErrorResponse | TraceNavigationResponse | None:
    """Get the previous and next trace id by index using efficient database queries.

    Pagination: no supported paging parameters.

    Args:
        trace_id (UUID):
        project_version_id (UUID):
        filters (str | Unset):  Default: '[]'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | TraceNavigationResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            trace_id=trace_id,
            project_version_id=project_version_id,
            filters=filters,
        )
    ).parsed
