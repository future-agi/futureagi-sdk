from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.accounts_error_response import AccountsErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.workspace_list_paginated_response import WorkspaceListPaginatedResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    page: int | Unset = 1,
    limit: int | Unset = 10,
    search: str | Unset = "",
    sort: str | Unset = "",
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["page"] = page

    params["limit"] = limit

    params["search"] = search

    params["sort"] = sort

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/accounts/workspace/list/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    AccountsErrorResponse | ManagementAPIErrorResponse | WorkspaceListPaginatedResponse
):
    if response.status_code == 200:
        response_200 = WorkspaceListPaginatedResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = AccountsErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = AccountsErrorResponse.from_dict(response.json())

        return response_401

    if response.status_code == 403:
        response_403 = AccountsErrorResponse.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = AccountsErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = AccountsErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    AccountsErrorResponse | ManagementAPIErrorResponse | WorkspaceListPaginatedResponse
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
    page: int | Unset = 1,
    limit: int | Unset = 10,
    search: str | Unset = "",
    sort: str | Unset = "",
) -> Response[
    AccountsErrorResponse | ManagementAPIErrorResponse | WorkspaceListPaginatedResponse
]:
    """Get paginated list of workspaces

    Args:
        page (int | Unset):  Default: 1.
        limit (int | Unset):  Default: 10.
        search (str | Unset):  Default: ''.
        sort (str | Unset):  Default: ''.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AccountsErrorResponse | ManagementAPIErrorResponse | WorkspaceListPaginatedResponse]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
        search=search,
        sort=sort,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = 1,
    limit: int | Unset = 10,
    search: str | Unset = "",
    sort: str | Unset = "",
) -> (
    AccountsErrorResponse
    | ManagementAPIErrorResponse
    | WorkspaceListPaginatedResponse
    | None
):
    """Get paginated list of workspaces

    Args:
        page (int | Unset):  Default: 1.
        limit (int | Unset):  Default: 10.
        search (str | Unset):  Default: ''.
        sort (str | Unset):  Default: ''.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AccountsErrorResponse | ManagementAPIErrorResponse | WorkspaceListPaginatedResponse
    """

    return sync_detailed(
        client=client,
        page=page,
        limit=limit,
        search=search,
        sort=sort,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = 1,
    limit: int | Unset = 10,
    search: str | Unset = "",
    sort: str | Unset = "",
) -> Response[
    AccountsErrorResponse | ManagementAPIErrorResponse | WorkspaceListPaginatedResponse
]:
    """Get paginated list of workspaces

    Args:
        page (int | Unset):  Default: 1.
        limit (int | Unset):  Default: 10.
        search (str | Unset):  Default: ''.
        sort (str | Unset):  Default: ''.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AccountsErrorResponse | ManagementAPIErrorResponse | WorkspaceListPaginatedResponse]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
        search=search,
        sort=sort,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = 1,
    limit: int | Unset = 10,
    search: str | Unset = "",
    sort: str | Unset = "",
) -> (
    AccountsErrorResponse
    | ManagementAPIErrorResponse
    | WorkspaceListPaginatedResponse
    | None
):
    """Get paginated list of workspaces

    Args:
        page (int | Unset):  Default: 1.
        limit (int | Unset):  Default: 10.
        search (str | Unset):  Default: ''.
        sort (str | Unset):  Default: ''.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AccountsErrorResponse | ManagementAPIErrorResponse | WorkspaceListPaginatedResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            page=page,
            limit=limit,
            search=search,
            sort=sort,
        )
    ).parsed
