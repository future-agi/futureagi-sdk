from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.tracer_trace_list_traces_of_session_response_200 import (
    TracerTraceListTracesOfSessionResponse200,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    project_id: UUID | Unset = UNSET,
    project_version_id: UUID | Unset = UNSET,
    session_id: UUID | Unset = UNSET,
    filters: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
    interval: str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["page"] = page

    params["limit"] = limit

    json_project_id: str | Unset = UNSET
    if not isinstance(project_id, Unset):
        json_project_id = str(project_id)
    params["project_id"] = json_project_id

    json_project_version_id: str | Unset = UNSET
    if not isinstance(project_version_id, Unset):
        json_project_version_id = str(project_version_id)
    params["project_version_id"] = json_project_version_id

    json_session_id: str | Unset = UNSET
    if not isinstance(session_id, Unset):
        json_session_id = str(session_id)
    params["session_id"] = json_session_id

    params["filters"] = filters

    params["page_number"] = page_number

    params["page_size"] = page_size

    params["interval"] = interval

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/tracer/trace/list_traces_of_session/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ManagementAPIErrorResponse | TracerTraceListTracesOfSessionResponse200:
    if response.status_code == 200:
        response_200 = TracerTraceListTracesOfSessionResponse200.from_dict(
            response.json()
        )

        return response_200

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ManagementAPIErrorResponse | TracerTraceListTracesOfSessionResponse200]:
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
    project_id: UUID | Unset = UNSET,
    project_version_id: UUID | Unset = UNSET,
    session_id: UUID | Unset = UNSET,
    filters: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
    interval: str | Unset = UNSET,
) -> Response[ManagementAPIErrorResponse | TracerTraceListTracesOfSessionResponse200]:
    """List traces filtered by project ID with optimized queries.

    Args:
        page (int | Unset):
        limit (int | Unset):
        project_id (UUID | Unset):
        project_version_id (UUID | Unset):
        session_id (UUID | Unset):
        filters (str | Unset):  Default: '[]'.
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 30.
        interval (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | TracerTraceListTracesOfSessionResponse200]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
        project_id=project_id,
        project_version_id=project_version_id,
        session_id=session_id,
        filters=filters,
        page_number=page_number,
        page_size=page_size,
        interval=interval,
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
    project_id: UUID | Unset = UNSET,
    project_version_id: UUID | Unset = UNSET,
    session_id: UUID | Unset = UNSET,
    filters: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
    interval: str | Unset = UNSET,
) -> ManagementAPIErrorResponse | TracerTraceListTracesOfSessionResponse200 | None:
    """List traces filtered by project ID with optimized queries.

    Args:
        page (int | Unset):
        limit (int | Unset):
        project_id (UUID | Unset):
        project_version_id (UUID | Unset):
        session_id (UUID | Unset):
        filters (str | Unset):  Default: '[]'.
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 30.
        interval (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | TracerTraceListTracesOfSessionResponse200
    """

    return sync_detailed(
        client=client,
        page=page,
        limit=limit,
        project_id=project_id,
        project_version_id=project_version_id,
        session_id=session_id,
        filters=filters,
        page_number=page_number,
        page_size=page_size,
        interval=interval,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    project_id: UUID | Unset = UNSET,
    project_version_id: UUID | Unset = UNSET,
    session_id: UUID | Unset = UNSET,
    filters: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
    interval: str | Unset = UNSET,
) -> Response[ManagementAPIErrorResponse | TracerTraceListTracesOfSessionResponse200]:
    """List traces filtered by project ID with optimized queries.

    Args:
        page (int | Unset):
        limit (int | Unset):
        project_id (UUID | Unset):
        project_version_id (UUID | Unset):
        session_id (UUID | Unset):
        filters (str | Unset):  Default: '[]'.
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 30.
        interval (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | TracerTraceListTracesOfSessionResponse200]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
        project_id=project_id,
        project_version_id=project_version_id,
        session_id=session_id,
        filters=filters,
        page_number=page_number,
        page_size=page_size,
        interval=interval,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    project_id: UUID | Unset = UNSET,
    project_version_id: UUID | Unset = UNSET,
    session_id: UUID | Unset = UNSET,
    filters: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
    interval: str | Unset = UNSET,
) -> ManagementAPIErrorResponse | TracerTraceListTracesOfSessionResponse200 | None:
    """List traces filtered by project ID with optimized queries.

    Args:
        page (int | Unset):
        limit (int | Unset):
        project_id (UUID | Unset):
        project_version_id (UUID | Unset):
        session_id (UUID | Unset):
        filters (str | Unset):  Default: '[]'.
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 30.
        interval (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | TracerTraceListTracesOfSessionResponse200
    """

    return (
        await asyncio_detailed(
            client=client,
            page=page,
            limit=limit,
            project_id=project_id,
            project_version_id=project_version_id,
            session_id=session_id,
            filters=filters,
            page_number=page_number,
            page_size=page_size,
            interval=interval,
        )
    ).parsed
