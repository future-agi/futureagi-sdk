from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_error_response import ApiErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    project_id: UUID,
    user_id: str | Unset = UNSET,
    bookmarked: bool | Unset = UNSET,
    filters: str | Unset = "[]",
    sort_params: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
    cursor: str | Unset = UNSET,
    cursor_mode: bool | Unset = False,
    interval: str | Unset = UNSET,
    allow_sampled: bool | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_project_id = str(project_id)
    params["project_id"] = json_project_id

    params["user_id"] = user_id

    params["bookmarked"] = bookmarked

    params["filters"] = filters

    params["sort_params"] = sort_params

    params["page_number"] = page_number

    params["page_size"] = page_size

    params["cursor"] = cursor

    params["cursor_mode"] = cursor_mode

    params["interval"] = interval

    params["allow_sampled"] = allow_sampled

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/tracer/trace-session/get_trace_session_export_data/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiErrorResponse | ManagementAPIErrorResponse | str:
    if response.status_code == 200:
        response_200 = response.text
        return response_200

    if response.status_code == 400:
        response_400 = ApiErrorResponse.from_dict(response.text)

        return response_400

    if response.status_code == 500:
        response_500 = ApiErrorResponse.from_dict(response.text)

        return response_500

    if response.status_code == 503:
        response_503 = ApiErrorResponse.from_dict(response.text)

        return response_503

    response_default = ManagementAPIErrorResponse.from_dict(response.text)

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ApiErrorResponse | ManagementAPIErrorResponse | str]:
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
    user_id: str | Unset = UNSET,
    bookmarked: bool | Unset = UNSET,
    filters: str | Unset = "[]",
    sort_params: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
    cursor: str | Unset = UNSET,
    cursor_mode: bool | Unset = False,
    interval: str | Unset = UNSET,
    allow_sampled: bool | Unset = UNSET,
) -> Response[ApiErrorResponse | ManagementAPIErrorResponse | str]:
    """Export traces filtered by project ID and project version ID with optimized queries.

    Pagination: page_number (0-based); page_size (page size); cursor (opaque continuation token);
    cursor_mode (enable cursor pagination).

    Args:
        project_id (UUID):
        user_id (str | Unset):
        bookmarked (bool | Unset):
        filters (str | Unset):  Default: '[]'.
        sort_params (str | Unset):  Default: '[]'.
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 30.
        cursor (str | Unset):
        cursor_mode (bool | Unset):  Default: False.
        interval (str | Unset):
        allow_sampled (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | ManagementAPIErrorResponse | str]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        user_id=user_id,
        bookmarked=bookmarked,
        filters=filters,
        sort_params=sort_params,
        page_number=page_number,
        page_size=page_size,
        cursor=cursor,
        cursor_mode=cursor_mode,
        interval=interval,
        allow_sampled=allow_sampled,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    project_id: UUID,
    user_id: str | Unset = UNSET,
    bookmarked: bool | Unset = UNSET,
    filters: str | Unset = "[]",
    sort_params: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
    cursor: str | Unset = UNSET,
    cursor_mode: bool | Unset = False,
    interval: str | Unset = UNSET,
    allow_sampled: bool | Unset = UNSET,
) -> ApiErrorResponse | ManagementAPIErrorResponse | str | None:
    """Export traces filtered by project ID and project version ID with optimized queries.

    Pagination: page_number (0-based); page_size (page size); cursor (opaque continuation token);
    cursor_mode (enable cursor pagination).

    Args:
        project_id (UUID):
        user_id (str | Unset):
        bookmarked (bool | Unset):
        filters (str | Unset):  Default: '[]'.
        sort_params (str | Unset):  Default: '[]'.
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 30.
        cursor (str | Unset):
        cursor_mode (bool | Unset):  Default: False.
        interval (str | Unset):
        allow_sampled (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | ManagementAPIErrorResponse | str
    """

    return sync_detailed(
        client=client,
        project_id=project_id,
        user_id=user_id,
        bookmarked=bookmarked,
        filters=filters,
        sort_params=sort_params,
        page_number=page_number,
        page_size=page_size,
        cursor=cursor,
        cursor_mode=cursor_mode,
        interval=interval,
        allow_sampled=allow_sampled,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    project_id: UUID,
    user_id: str | Unset = UNSET,
    bookmarked: bool | Unset = UNSET,
    filters: str | Unset = "[]",
    sort_params: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
    cursor: str | Unset = UNSET,
    cursor_mode: bool | Unset = False,
    interval: str | Unset = UNSET,
    allow_sampled: bool | Unset = UNSET,
) -> Response[ApiErrorResponse | ManagementAPIErrorResponse | str]:
    """Export traces filtered by project ID and project version ID with optimized queries.

    Pagination: page_number (0-based); page_size (page size); cursor (opaque continuation token);
    cursor_mode (enable cursor pagination).

    Args:
        project_id (UUID):
        user_id (str | Unset):
        bookmarked (bool | Unset):
        filters (str | Unset):  Default: '[]'.
        sort_params (str | Unset):  Default: '[]'.
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 30.
        cursor (str | Unset):
        cursor_mode (bool | Unset):  Default: False.
        interval (str | Unset):
        allow_sampled (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | ManagementAPIErrorResponse | str]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        user_id=user_id,
        bookmarked=bookmarked,
        filters=filters,
        sort_params=sort_params,
        page_number=page_number,
        page_size=page_size,
        cursor=cursor,
        cursor_mode=cursor_mode,
        interval=interval,
        allow_sampled=allow_sampled,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    project_id: UUID,
    user_id: str | Unset = UNSET,
    bookmarked: bool | Unset = UNSET,
    filters: str | Unset = "[]",
    sort_params: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
    cursor: str | Unset = UNSET,
    cursor_mode: bool | Unset = False,
    interval: str | Unset = UNSET,
    allow_sampled: bool | Unset = UNSET,
) -> ApiErrorResponse | ManagementAPIErrorResponse | str | None:
    """Export traces filtered by project ID and project version ID with optimized queries.

    Pagination: page_number (0-based); page_size (page size); cursor (opaque continuation token);
    cursor_mode (enable cursor pagination).

    Args:
        project_id (UUID):
        user_id (str | Unset):
        bookmarked (bool | Unset):
        filters (str | Unset):  Default: '[]'.
        sort_params (str | Unset):  Default: '[]'.
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 30.
        cursor (str | Unset):
        cursor_mode (bool | Unset):  Default: False.
        interval (str | Unset):
        allow_sampled (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | ManagementAPIErrorResponse | str
    """

    return (
        await asyncio_detailed(
            client=client,
            project_id=project_id,
            user_id=user_id,
            bookmarked=bookmarked,
            filters=filters,
            sort_params=sort_params,
            page_number=page_number,
            page_size=page_size,
            cursor=cursor,
            cursor_mode=cursor_mode,
            interval=interval,
            allow_sampled=allow_sampled,
        )
    ).parsed
