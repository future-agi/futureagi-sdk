from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_error_response import ApiErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.page_depth_exceeded_error import PageDepthExceededError
from ...models.trace_prototype_list_response import TracePrototypeListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    project_version_id: UUID,
    trace_ids: str | Unset = UNSET,
    filters: str | Unset = "[]",
    sort_params: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
    allow_sampled: bool | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_project_version_id = str(project_version_id)
    params["project_version_id"] = json_project_version_id

    params["trace_ids"] = trace_ids

    params["filters"] = filters

    params["sort_params"] = sort_params

    params["page_number"] = page_number

    params["page_size"] = page_size

    params["allow_sampled"] = allow_sampled

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/tracer/trace/list_traces/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ApiErrorResponse
    | ManagementAPIErrorResponse
    | PageDepthExceededError
    | TracePrototypeListResponse
):
    if response.status_code == 200:
        response_200 = TracePrototypeListResponse.from_dict(response.json())

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
    | TracePrototypeListResponse
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
    project_version_id: UUID,
    trace_ids: str | Unset = UNSET,
    filters: str | Unset = "[]",
    sort_params: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
    allow_sampled: bool | Unset = UNSET,
) -> Response[
    ApiErrorResponse
    | ManagementAPIErrorResponse
    | PageDepthExceededError
    | TracePrototypeListResponse
]:
    """List traces filtered by project ID and project version ID with optimized queries.

    Pagination: page_number (0-based); page_size (page size).

    Args:
        project_version_id (UUID):
        trace_ids (str | Unset):
        filters (str | Unset):  Default: '[]'.
        sort_params (str | Unset):  Default: '[]'.
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 30.
        allow_sampled (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | ManagementAPIErrorResponse | PageDepthExceededError | TracePrototypeListResponse]
    """

    kwargs = _get_kwargs(
        project_version_id=project_version_id,
        trace_ids=trace_ids,
        filters=filters,
        sort_params=sort_params,
        page_number=page_number,
        page_size=page_size,
        allow_sampled=allow_sampled,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    project_version_id: UUID,
    trace_ids: str | Unset = UNSET,
    filters: str | Unset = "[]",
    sort_params: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
    allow_sampled: bool | Unset = UNSET,
) -> (
    ApiErrorResponse
    | ManagementAPIErrorResponse
    | PageDepthExceededError
    | TracePrototypeListResponse
    | None
):
    """List traces filtered by project ID and project version ID with optimized queries.

    Pagination: page_number (0-based); page_size (page size).

    Args:
        project_version_id (UUID):
        trace_ids (str | Unset):
        filters (str | Unset):  Default: '[]'.
        sort_params (str | Unset):  Default: '[]'.
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 30.
        allow_sampled (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | ManagementAPIErrorResponse | PageDepthExceededError | TracePrototypeListResponse
    """

    return sync_detailed(
        client=client,
        project_version_id=project_version_id,
        trace_ids=trace_ids,
        filters=filters,
        sort_params=sort_params,
        page_number=page_number,
        page_size=page_size,
        allow_sampled=allow_sampled,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    project_version_id: UUID,
    trace_ids: str | Unset = UNSET,
    filters: str | Unset = "[]",
    sort_params: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
    allow_sampled: bool | Unset = UNSET,
) -> Response[
    ApiErrorResponse
    | ManagementAPIErrorResponse
    | PageDepthExceededError
    | TracePrototypeListResponse
]:
    """List traces filtered by project ID and project version ID with optimized queries.

    Pagination: page_number (0-based); page_size (page size).

    Args:
        project_version_id (UUID):
        trace_ids (str | Unset):
        filters (str | Unset):  Default: '[]'.
        sort_params (str | Unset):  Default: '[]'.
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 30.
        allow_sampled (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | ManagementAPIErrorResponse | PageDepthExceededError | TracePrototypeListResponse]
    """

    kwargs = _get_kwargs(
        project_version_id=project_version_id,
        trace_ids=trace_ids,
        filters=filters,
        sort_params=sort_params,
        page_number=page_number,
        page_size=page_size,
        allow_sampled=allow_sampled,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    project_version_id: UUID,
    trace_ids: str | Unset = UNSET,
    filters: str | Unset = "[]",
    sort_params: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
    allow_sampled: bool | Unset = UNSET,
) -> (
    ApiErrorResponse
    | ManagementAPIErrorResponse
    | PageDepthExceededError
    | TracePrototypeListResponse
    | None
):
    """List traces filtered by project ID and project version ID with optimized queries.

    Pagination: page_number (0-based); page_size (page size).

    Args:
        project_version_id (UUID):
        trace_ids (str | Unset):
        filters (str | Unset):  Default: '[]'.
        sort_params (str | Unset):  Default: '[]'.
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 30.
        allow_sampled (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | ManagementAPIErrorResponse | PageDepthExceededError | TracePrototypeListResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            project_version_id=project_version_id,
            trace_ids=trace_ids,
            filters=filters,
            sort_params=sort_params,
            page_number=page_number,
            page_size=page_size,
            allow_sampled=allow_sampled,
        )
    ).parsed
