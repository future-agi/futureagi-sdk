from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_error_response import ApiErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.page_depth_exceeded_error import PageDepthExceededError
from ...models.trace_observe_list_response import TraceObserveListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    sort_params: str | Unset = "[]",
    project_id: UUID | Unset = UNSET,
    project_version_id: UUID | Unset = UNSET,
    session_id: UUID | Unset = UNSET,
    filters: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
    cursor: str | Unset = UNSET,
    cursor_mode: bool | Unset = False,
    attribute_keys: str | Unset = UNSET,
    allow_sampled: bool | Unset = UNSET,
    interval: str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["sort_params"] = sort_params

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

    params["cursor"] = cursor

    params["cursor_mode"] = cursor_mode

    params["attribute_keys"] = attribute_keys

    params["allow_sampled"] = allow_sampled

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
) -> (
    ApiErrorResponse
    | ManagementAPIErrorResponse
    | PageDepthExceededError
    | TraceObserveListResponse
):
    if response.status_code == 200:
        response_200 = TraceObserveListResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ApiErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 422:
        response_422 = PageDepthExceededError.from_dict(response.json())

        return response_422

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
) -> Response[
    ApiErrorResponse
    | ManagementAPIErrorResponse
    | PageDepthExceededError
    | TraceObserveListResponse
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
    sort_params: str | Unset = "[]",
    project_id: UUID | Unset = UNSET,
    project_version_id: UUID | Unset = UNSET,
    session_id: UUID | Unset = UNSET,
    filters: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
    cursor: str | Unset = UNSET,
    cursor_mode: bool | Unset = False,
    attribute_keys: str | Unset = UNSET,
    allow_sampled: bool | Unset = UNSET,
    interval: str | Unset = UNSET,
) -> Response[
    ApiErrorResponse
    | ManagementAPIErrorResponse
    | PageDepthExceededError
    | TraceObserveListResponse
]:
    """List traces filtered by project ID with optimized queries.

    Pagination: page_number (0-based); page_size (page size); cursor (opaque continuation token);
    cursor_mode (enable cursor pagination).

    Args:
        sort_params (str | Unset):  Default: '[]'.
        project_id (UUID | Unset):
        project_version_id (UUID | Unset):
        session_id (UUID | Unset):
        filters (str | Unset):  Default: '[]'.
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 30.
        cursor (str | Unset):
        cursor_mode (bool | Unset):  Default: False.
        attribute_keys (str | Unset):
        allow_sampled (bool | Unset):
        interval (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | ManagementAPIErrorResponse | PageDepthExceededError | TraceObserveListResponse]
    """

    kwargs = _get_kwargs(
        sort_params=sort_params,
        project_id=project_id,
        project_version_id=project_version_id,
        session_id=session_id,
        filters=filters,
        page_number=page_number,
        page_size=page_size,
        cursor=cursor,
        cursor_mode=cursor_mode,
        attribute_keys=attribute_keys,
        allow_sampled=allow_sampled,
        interval=interval,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    sort_params: str | Unset = "[]",
    project_id: UUID | Unset = UNSET,
    project_version_id: UUID | Unset = UNSET,
    session_id: UUID | Unset = UNSET,
    filters: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
    cursor: str | Unset = UNSET,
    cursor_mode: bool | Unset = False,
    attribute_keys: str | Unset = UNSET,
    allow_sampled: bool | Unset = UNSET,
    interval: str | Unset = UNSET,
) -> (
    ApiErrorResponse
    | ManagementAPIErrorResponse
    | PageDepthExceededError
    | TraceObserveListResponse
    | None
):
    """List traces filtered by project ID with optimized queries.

    Pagination: page_number (0-based); page_size (page size); cursor (opaque continuation token);
    cursor_mode (enable cursor pagination).

    Args:
        sort_params (str | Unset):  Default: '[]'.
        project_id (UUID | Unset):
        project_version_id (UUID | Unset):
        session_id (UUID | Unset):
        filters (str | Unset):  Default: '[]'.
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 30.
        cursor (str | Unset):
        cursor_mode (bool | Unset):  Default: False.
        attribute_keys (str | Unset):
        allow_sampled (bool | Unset):
        interval (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | ManagementAPIErrorResponse | PageDepthExceededError | TraceObserveListResponse
    """

    return sync_detailed(
        client=client,
        sort_params=sort_params,
        project_id=project_id,
        project_version_id=project_version_id,
        session_id=session_id,
        filters=filters,
        page_number=page_number,
        page_size=page_size,
        cursor=cursor,
        cursor_mode=cursor_mode,
        attribute_keys=attribute_keys,
        allow_sampled=allow_sampled,
        interval=interval,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    sort_params: str | Unset = "[]",
    project_id: UUID | Unset = UNSET,
    project_version_id: UUID | Unset = UNSET,
    session_id: UUID | Unset = UNSET,
    filters: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
    cursor: str | Unset = UNSET,
    cursor_mode: bool | Unset = False,
    attribute_keys: str | Unset = UNSET,
    allow_sampled: bool | Unset = UNSET,
    interval: str | Unset = UNSET,
) -> Response[
    ApiErrorResponse
    | ManagementAPIErrorResponse
    | PageDepthExceededError
    | TraceObserveListResponse
]:
    """List traces filtered by project ID with optimized queries.

    Pagination: page_number (0-based); page_size (page size); cursor (opaque continuation token);
    cursor_mode (enable cursor pagination).

    Args:
        sort_params (str | Unset):  Default: '[]'.
        project_id (UUID | Unset):
        project_version_id (UUID | Unset):
        session_id (UUID | Unset):
        filters (str | Unset):  Default: '[]'.
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 30.
        cursor (str | Unset):
        cursor_mode (bool | Unset):  Default: False.
        attribute_keys (str | Unset):
        allow_sampled (bool | Unset):
        interval (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | ManagementAPIErrorResponse | PageDepthExceededError | TraceObserveListResponse]
    """

    kwargs = _get_kwargs(
        sort_params=sort_params,
        project_id=project_id,
        project_version_id=project_version_id,
        session_id=session_id,
        filters=filters,
        page_number=page_number,
        page_size=page_size,
        cursor=cursor,
        cursor_mode=cursor_mode,
        attribute_keys=attribute_keys,
        allow_sampled=allow_sampled,
        interval=interval,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    sort_params: str | Unset = "[]",
    project_id: UUID | Unset = UNSET,
    project_version_id: UUID | Unset = UNSET,
    session_id: UUID | Unset = UNSET,
    filters: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
    cursor: str | Unset = UNSET,
    cursor_mode: bool | Unset = False,
    attribute_keys: str | Unset = UNSET,
    allow_sampled: bool | Unset = UNSET,
    interval: str | Unset = UNSET,
) -> (
    ApiErrorResponse
    | ManagementAPIErrorResponse
    | PageDepthExceededError
    | TraceObserveListResponse
    | None
):
    """List traces filtered by project ID with optimized queries.

    Pagination: page_number (0-based); page_size (page size); cursor (opaque continuation token);
    cursor_mode (enable cursor pagination).

    Args:
        sort_params (str | Unset):  Default: '[]'.
        project_id (UUID | Unset):
        project_version_id (UUID | Unset):
        session_id (UUID | Unset):
        filters (str | Unset):  Default: '[]'.
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 30.
        cursor (str | Unset):
        cursor_mode (bool | Unset):  Default: False.
        attribute_keys (str | Unset):
        allow_sampled (bool | Unset):
        interval (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | ManagementAPIErrorResponse | PageDepthExceededError | TraceObserveListResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            sort_params=sort_params,
            project_id=project_id,
            project_version_id=project_version_id,
            session_id=session_id,
            filters=filters,
            page_number=page_number,
            page_size=page_size,
            cursor=cursor,
            cursor_mode=cursor_mode,
            attribute_keys=attribute_keys,
            allow_sampled=allow_sampled,
            interval=interval,
        )
    ).parsed
