from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_error_response import ApiErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.trace_session import TraceSession
from ...models.tracer_trace_session_get_session_filter_values_column import (
    TracerTraceSessionGetSessionFilterValuesColumn,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    project_id: UUID,
    column: TracerTraceSessionGetSessionFilterValuesColumn,
    search: str | Unset = "",
    page: int | Unset = 0,
    page_size: int | Unset = 50,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_project_id = str(project_id)
    params["project_id"] = json_project_id

    json_column = column.value
    params["column"] = json_column

    params["search"] = search

    params["page"] = page

    params["page_size"] = page_size

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/tracer/trace-session/get_session_filter_values/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiErrorResponse | ManagementAPIErrorResponse | list[TraceSession]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = TraceSession.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200

    if response.status_code == 400:
        response_400 = ApiErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 500:
        response_500 = ApiErrorResponse.from_dict(response.json())

        return response_500

    if response.status_code == 503:
        response_503 = ApiErrorResponse.from_dict(response.json())

        return response_503

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ApiErrorResponse | ManagementAPIErrorResponse | list[TraceSession]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    project_id: UUID,
    column: TracerTraceSessionGetSessionFilterValuesColumn,
    search: str | Unset = "",
    page: int | Unset = 0,
    page_size: int | Unset = 50,
) -> Response[ApiErrorResponse | ManagementAPIErrorResponse | list[TraceSession]]:
    r"""Return distinct values for a session-level column.
    Used by the filter panel's value picker for session-specific fields
    (session_id, user_id, first_message, etc.).

    Query params:
        project_id: required
        column: canonical session column name, e.g. \"session_id\"
        search: optional search substring
        page: page number (0-based), default 0
        page_size: default 50

    Pagination: page (0-based); page_size (page size).

    Args:
        project_id (UUID):
        column (TracerTraceSessionGetSessionFilterValuesColumn):
        search (str | Unset):  Default: ''.
        page (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 50.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | ManagementAPIErrorResponse | list[TraceSession]]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        column=column,
        search=search,
        page=page,
        page_size=page_size,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    project_id: UUID,
    column: TracerTraceSessionGetSessionFilterValuesColumn,
    search: str | Unset = "",
    page: int | Unset = 0,
    page_size: int | Unset = 50,
) -> ApiErrorResponse | ManagementAPIErrorResponse | list[TraceSession] | None:
    r"""Return distinct values for a session-level column.
    Used by the filter panel's value picker for session-specific fields
    (session_id, user_id, first_message, etc.).

    Query params:
        project_id: required
        column: canonical session column name, e.g. \"session_id\"
        search: optional search substring
        page: page number (0-based), default 0
        page_size: default 50

    Pagination: page (0-based); page_size (page size).

    Args:
        project_id (UUID):
        column (TracerTraceSessionGetSessionFilterValuesColumn):
        search (str | Unset):  Default: ''.
        page (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 50.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | ManagementAPIErrorResponse | list[TraceSession]
    """

    return sync_detailed(
        client=client,
        project_id=project_id,
        column=column,
        search=search,
        page=page,
        page_size=page_size,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    project_id: UUID,
    column: TracerTraceSessionGetSessionFilterValuesColumn,
    search: str | Unset = "",
    page: int | Unset = 0,
    page_size: int | Unset = 50,
) -> Response[ApiErrorResponse | ManagementAPIErrorResponse | list[TraceSession]]:
    r"""Return distinct values for a session-level column.
    Used by the filter panel's value picker for session-specific fields
    (session_id, user_id, first_message, etc.).

    Query params:
        project_id: required
        column: canonical session column name, e.g. \"session_id\"
        search: optional search substring
        page: page number (0-based), default 0
        page_size: default 50

    Pagination: page (0-based); page_size (page size).

    Args:
        project_id (UUID):
        column (TracerTraceSessionGetSessionFilterValuesColumn):
        search (str | Unset):  Default: ''.
        page (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 50.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | ManagementAPIErrorResponse | list[TraceSession]]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        column=column,
        search=search,
        page=page,
        page_size=page_size,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    project_id: UUID,
    column: TracerTraceSessionGetSessionFilterValuesColumn,
    search: str | Unset = "",
    page: int | Unset = 0,
    page_size: int | Unset = 50,
) -> ApiErrorResponse | ManagementAPIErrorResponse | list[TraceSession] | None:
    r"""Return distinct values for a session-level column.
    Used by the filter panel's value picker for session-specific fields
    (session_id, user_id, first_message, etc.).

    Query params:
        project_id: required
        column: canonical session column name, e.g. \"session_id\"
        search: optional search substring
        page: page number (0-based), default 0
        page_size: default 50

    Pagination: page (0-based); page_size (page size).

    Args:
        project_id (UUID):
        column (TracerTraceSessionGetSessionFilterValuesColumn):
        search (str | Unset):  Default: ''.
        page (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 50.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | ManagementAPIErrorResponse | list[TraceSession]
    """

    return (
        await asyncio_detailed(
            client=client,
            project_id=project_id,
            column=column,
            search=search,
            page=page,
            page_size=page_size,
        )
    ).parsed
