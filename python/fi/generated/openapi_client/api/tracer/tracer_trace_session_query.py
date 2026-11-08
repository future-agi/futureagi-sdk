from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_error_response import ApiErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.trace_session_detail_response import TraceSessionDetailResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    id: str,
    *,
    navigation_context: str | Unset = UNSET,
    user_id: str | Unset = UNSET,
    filters: str | Unset = "[]",
    sort_params: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["navigation_context"] = navigation_context

    params["user_id"] = user_id

    params["filters"] = filters

    params["sort_params"] = sort_params

    params["page_number"] = page_number

    params["page_size"] = page_size

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/tracer/trace-session/{id}/query/".format(
            id=quote(str(id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiErrorResponse | ManagementAPIErrorResponse | TraceSessionDetailResponse:
    if response.status_code == 200:
        response_200 = TraceSessionDetailResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ApiErrorResponse.from_dict(response.json())

        return response_400

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ApiErrorResponse | ManagementAPIErrorResponse | TraceSessionDetailResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: str,
    *,
    client: AuthenticatedClient | Client,
    navigation_context: str | Unset = UNSET,
    user_id: str | Unset = UNSET,
    filters: str | Unset = "[]",
    sort_params: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
) -> Response[
    ApiErrorResponse | ManagementAPIErrorResponse | TraceSessionDetailResponse
]:
    """Read the same authorized detail without putting filters in the URL.

    Pagination: page_number (0-based); page_size (page size).

    Args:
        id (str):
        navigation_context (str | Unset):
        user_id (str | Unset):
        filters (str | Unset):  Default: '[]'.
        sort_params (str | Unset):  Default: '[]'.
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 30.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | ManagementAPIErrorResponse | TraceSessionDetailResponse]
    """

    kwargs = _get_kwargs(
        id=id,
        navigation_context=navigation_context,
        user_id=user_id,
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
    id: str,
    *,
    client: AuthenticatedClient | Client,
    navigation_context: str | Unset = UNSET,
    user_id: str | Unset = UNSET,
    filters: str | Unset = "[]",
    sort_params: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
) -> ApiErrorResponse | ManagementAPIErrorResponse | TraceSessionDetailResponse | None:
    """Read the same authorized detail without putting filters in the URL.

    Pagination: page_number (0-based); page_size (page size).

    Args:
        id (str):
        navigation_context (str | Unset):
        user_id (str | Unset):
        filters (str | Unset):  Default: '[]'.
        sort_params (str | Unset):  Default: '[]'.
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 30.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | ManagementAPIErrorResponse | TraceSessionDetailResponse
    """

    return sync_detailed(
        id=id,
        client=client,
        navigation_context=navigation_context,
        user_id=user_id,
        filters=filters,
        sort_params=sort_params,
        page_number=page_number,
        page_size=page_size,
    ).parsed


async def asyncio_detailed(
    id: str,
    *,
    client: AuthenticatedClient | Client,
    navigation_context: str | Unset = UNSET,
    user_id: str | Unset = UNSET,
    filters: str | Unset = "[]",
    sort_params: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
) -> Response[
    ApiErrorResponse | ManagementAPIErrorResponse | TraceSessionDetailResponse
]:
    """Read the same authorized detail without putting filters in the URL.

    Pagination: page_number (0-based); page_size (page size).

    Args:
        id (str):
        navigation_context (str | Unset):
        user_id (str | Unset):
        filters (str | Unset):  Default: '[]'.
        sort_params (str | Unset):  Default: '[]'.
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 30.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | ManagementAPIErrorResponse | TraceSessionDetailResponse]
    """

    kwargs = _get_kwargs(
        id=id,
        navigation_context=navigation_context,
        user_id=user_id,
        filters=filters,
        sort_params=sort_params,
        page_number=page_number,
        page_size=page_size,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: str,
    *,
    client: AuthenticatedClient | Client,
    navigation_context: str | Unset = UNSET,
    user_id: str | Unset = UNSET,
    filters: str | Unset = "[]",
    sort_params: str | Unset = "[]",
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
) -> ApiErrorResponse | ManagementAPIErrorResponse | TraceSessionDetailResponse | None:
    """Read the same authorized detail without putting filters in the URL.

    Pagination: page_number (0-based); page_size (page size).

    Args:
        id (str):
        navigation_context (str | Unset):
        user_id (str | Unset):
        filters (str | Unset):  Default: '[]'.
        sort_params (str | Unset):  Default: '[]'.
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 30.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | ManagementAPIErrorResponse | TraceSessionDetailResponse
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            navigation_context=navigation_context,
            user_id=user_id,
            filters=filters,
            sort_params=sort_params,
            page_number=page_number,
            page_size=page_size,
        )
    ).parsed
