from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.call_execution import CallExecution
from ...models.call_execution_error_response import CallExecutionErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    search: str | Unset = "",
    status: str | Unset = "",
    test_execution_id: UUID | Unset = UNSET,
    page: int | Unset = 1,
    limit: int | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["search"] = search

    params["status"] = status

    json_test_execution_id: str | Unset = UNSET
    if not isinstance(test_execution_id, Unset):
        json_test_execution_id = str(test_execution_id)
    params["test_execution_id"] = json_test_execution_id

    params["page"] = page

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/simulate/api/call-executions/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CallExecutionErrorResponse | ManagementAPIErrorResponse | list[CallExecution]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = CallExecution.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200

    if response.status_code == 404:
        response_404 = CallExecutionErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = CallExecutionErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    CallExecutionErrorResponse | ManagementAPIErrorResponse | list[CallExecution]
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
    search: str | Unset = "",
    status: str | Unset = "",
    test_execution_id: UUID | Unset = UNSET,
    page: int | Unset = 1,
    limit: int | Unset = UNSET,
) -> Response[
    CallExecutionErrorResponse | ManagementAPIErrorResponse | list[CallExecution]
]:
    """Get paginated list of call executions for the user's organization
    Query Parameters:
    - search: search string to filter call executions by phone number or scenario name
    - status: filter by call status
    - test_execution_id: filter by specific test execution
    - limit: number of items per page (default: 10)
    - page: page number (default: 1)

    Args:
        search (str | Unset):  Default: ''.
        status (str | Unset):  Default: ''.
        test_execution_id (UUID | Unset):
        page (int | Unset):  Default: 1.
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CallExecutionErrorResponse | ManagementAPIErrorResponse | list[CallExecution]]
    """

    kwargs = _get_kwargs(
        search=search,
        status=status,
        test_execution_id=test_execution_id,
        page=page,
        limit=limit,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    search: str | Unset = "",
    status: str | Unset = "",
    test_execution_id: UUID | Unset = UNSET,
    page: int | Unset = 1,
    limit: int | Unset = UNSET,
) -> (
    CallExecutionErrorResponse | ManagementAPIErrorResponse | list[CallExecution] | None
):
    """Get paginated list of call executions for the user's organization
    Query Parameters:
    - search: search string to filter call executions by phone number or scenario name
    - status: filter by call status
    - test_execution_id: filter by specific test execution
    - limit: number of items per page (default: 10)
    - page: page number (default: 1)

    Args:
        search (str | Unset):  Default: ''.
        status (str | Unset):  Default: ''.
        test_execution_id (UUID | Unset):
        page (int | Unset):  Default: 1.
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CallExecutionErrorResponse | ManagementAPIErrorResponse | list[CallExecution]
    """

    return sync_detailed(
        client=client,
        search=search,
        status=status,
        test_execution_id=test_execution_id,
        page=page,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    search: str | Unset = "",
    status: str | Unset = "",
    test_execution_id: UUID | Unset = UNSET,
    page: int | Unset = 1,
    limit: int | Unset = UNSET,
) -> Response[
    CallExecutionErrorResponse | ManagementAPIErrorResponse | list[CallExecution]
]:
    """Get paginated list of call executions for the user's organization
    Query Parameters:
    - search: search string to filter call executions by phone number or scenario name
    - status: filter by call status
    - test_execution_id: filter by specific test execution
    - limit: number of items per page (default: 10)
    - page: page number (default: 1)

    Args:
        search (str | Unset):  Default: ''.
        status (str | Unset):  Default: ''.
        test_execution_id (UUID | Unset):
        page (int | Unset):  Default: 1.
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CallExecutionErrorResponse | ManagementAPIErrorResponse | list[CallExecution]]
    """

    kwargs = _get_kwargs(
        search=search,
        status=status,
        test_execution_id=test_execution_id,
        page=page,
        limit=limit,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    search: str | Unset = "",
    status: str | Unset = "",
    test_execution_id: UUID | Unset = UNSET,
    page: int | Unset = 1,
    limit: int | Unset = UNSET,
) -> (
    CallExecutionErrorResponse | ManagementAPIErrorResponse | list[CallExecution] | None
):
    """Get paginated list of call executions for the user's organization
    Query Parameters:
    - search: search string to filter call executions by phone number or scenario name
    - status: filter by call status
    - test_execution_id: filter by specific test execution
    - limit: number of items per page (default: 10)
    - page: page number (default: 1)

    Args:
        search (str | Unset):  Default: ''.
        status (str | Unset):  Default: ''.
        test_execution_id (UUID | Unset):
        page (int | Unset):  Default: 1.
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CallExecutionErrorResponse | ManagementAPIErrorResponse | list[CallExecution]
    """

    return (
        await asyncio_detailed(
            client=client,
            search=search,
            status=status,
            test_execution_id=test_execution_id,
            page=page,
            limit=limit,
        )
    ).parsed
