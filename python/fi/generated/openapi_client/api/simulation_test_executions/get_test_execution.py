from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error_response import ErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.test_execution_detail_response import TestExecutionDetailResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    test_execution_id: str,
    *,
    search: str | Unset = "",
    filters: str | Unset = "[]",
    row_groups: str | Unset = "[]",
    group_keys: str | Unset = "[]",
    page: int | Unset = 1,
    limit: int | Unset = 30,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["search"] = search

    params["filters"] = filters

    params["row_groups"] = row_groups

    params["group_keys"] = group_keys

    params["page"] = page

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/simulate/test-executions/{test_execution_id}/".format(
            test_execution_id=quote(str(test_execution_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | ManagementAPIErrorResponse | TestExecutionDetailResponse:
    if response.status_code == 200:
        response_200 = TestExecutionDetailResponse.from_dict(response.json())

        return response_200

    if response.status_code == 404:
        response_404 = ErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = ErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorResponse | ManagementAPIErrorResponse | TestExecutionDetailResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    test_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
    search: str | Unset = "",
    filters: str | Unset = "[]",
    row_groups: str | Unset = "[]",
    group_keys: str | Unset = "[]",
    page: int | Unset = 1,
    limit: int | Unset = 30,
) -> Response[ErrorResponse | ManagementAPIErrorResponse | TestExecutionDetailResponse]:
    """Get a specific test execution with all its details and paginated call executions
    Query Parameters:
    - search: search string to filter call executions
    - page: page number for call executions (default: 1)
    - filters: JSON array of filter objects
    - row_groups: JSON array of column IDs to group by
    - group_keys: JSON array of group keys

    Args:
        test_execution_id (str):
        search (str | Unset):  Default: ''.
        filters (str | Unset):  Default: '[]'.
        row_groups (str | Unset):  Default: '[]'.
        group_keys (str | Unset):  Default: '[]'.
        page (int | Unset):  Default: 1.
        limit (int | Unset):  Default: 30.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | ManagementAPIErrorResponse | TestExecutionDetailResponse]
    """

    kwargs = _get_kwargs(
        test_execution_id=test_execution_id,
        search=search,
        filters=filters,
        row_groups=row_groups,
        group_keys=group_keys,
        page=page,
        limit=limit,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    test_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
    search: str | Unset = "",
    filters: str | Unset = "[]",
    row_groups: str | Unset = "[]",
    group_keys: str | Unset = "[]",
    page: int | Unset = 1,
    limit: int | Unset = 30,
) -> ErrorResponse | ManagementAPIErrorResponse | TestExecutionDetailResponse | None:
    """Get a specific test execution with all its details and paginated call executions
    Query Parameters:
    - search: search string to filter call executions
    - page: page number for call executions (default: 1)
    - filters: JSON array of filter objects
    - row_groups: JSON array of column IDs to group by
    - group_keys: JSON array of group keys

    Args:
        test_execution_id (str):
        search (str | Unset):  Default: ''.
        filters (str | Unset):  Default: '[]'.
        row_groups (str | Unset):  Default: '[]'.
        group_keys (str | Unset):  Default: '[]'.
        page (int | Unset):  Default: 1.
        limit (int | Unset):  Default: 30.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | ManagementAPIErrorResponse | TestExecutionDetailResponse
    """

    return sync_detailed(
        test_execution_id=test_execution_id,
        client=client,
        search=search,
        filters=filters,
        row_groups=row_groups,
        group_keys=group_keys,
        page=page,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    test_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
    search: str | Unset = "",
    filters: str | Unset = "[]",
    row_groups: str | Unset = "[]",
    group_keys: str | Unset = "[]",
    page: int | Unset = 1,
    limit: int | Unset = 30,
) -> Response[ErrorResponse | ManagementAPIErrorResponse | TestExecutionDetailResponse]:
    """Get a specific test execution with all its details and paginated call executions
    Query Parameters:
    - search: search string to filter call executions
    - page: page number for call executions (default: 1)
    - filters: JSON array of filter objects
    - row_groups: JSON array of column IDs to group by
    - group_keys: JSON array of group keys

    Args:
        test_execution_id (str):
        search (str | Unset):  Default: ''.
        filters (str | Unset):  Default: '[]'.
        row_groups (str | Unset):  Default: '[]'.
        group_keys (str | Unset):  Default: '[]'.
        page (int | Unset):  Default: 1.
        limit (int | Unset):  Default: 30.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | ManagementAPIErrorResponse | TestExecutionDetailResponse]
    """

    kwargs = _get_kwargs(
        test_execution_id=test_execution_id,
        search=search,
        filters=filters,
        row_groups=row_groups,
        group_keys=group_keys,
        page=page,
        limit=limit,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    test_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
    search: str | Unset = "",
    filters: str | Unset = "[]",
    row_groups: str | Unset = "[]",
    group_keys: str | Unset = "[]",
    page: int | Unset = 1,
    limit: int | Unset = 30,
) -> ErrorResponse | ManagementAPIErrorResponse | TestExecutionDetailResponse | None:
    """Get a specific test execution with all its details and paginated call executions
    Query Parameters:
    - search: search string to filter call executions
    - page: page number for call executions (default: 1)
    - filters: JSON array of filter objects
    - row_groups: JSON array of column IDs to group by
    - group_keys: JSON array of group keys

    Args:
        test_execution_id (str):
        search (str | Unset):  Default: ''.
        filters (str | Unset):  Default: '[]'.
        row_groups (str | Unset):  Default: '[]'.
        group_keys (str | Unset):  Default: '[]'.
        page (int | Unset):  Default: 1.
        limit (int | Unset):  Default: 30.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | ManagementAPIErrorResponse | TestExecutionDetailResponse
    """

    return (
        await asyncio_detailed(
            test_execution_id=test_execution_id,
            client=client,
            search=search,
            filters=filters,
            row_groups=row_groups,
            group_keys=group_keys,
            page=page,
            limit=limit,
        )
    ).parsed
