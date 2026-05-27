from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.accounts_error_response import AccountsErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.switch_workspace import SwitchWorkspace
from ...models.switch_workspace_response import SwitchWorkspaceResponse
from ...types import Response


def _get_kwargs(
    *,
    body: SwitchWorkspace,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/accounts/workspace/switch/",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AccountsErrorResponse | ManagementAPIErrorResponse | SwitchWorkspaceResponse:
    if response.status_code == 200:
        response_200 = SwitchWorkspaceResponse.from_dict(response.json())

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
    AccountsErrorResponse | ManagementAPIErrorResponse | SwitchWorkspaceResponse
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
    body: SwitchWorkspace,
) -> Response[
    AccountsErrorResponse | ManagementAPIErrorResponse | SwitchWorkspaceResponse
]:
    """Switch to a different workspace with proper validation

    Args:
        body (SwitchWorkspace):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AccountsErrorResponse | ManagementAPIErrorResponse | SwitchWorkspaceResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: SwitchWorkspace,
) -> (
    AccountsErrorResponse | ManagementAPIErrorResponse | SwitchWorkspaceResponse | None
):
    """Switch to a different workspace with proper validation

    Args:
        body (SwitchWorkspace):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AccountsErrorResponse | ManagementAPIErrorResponse | SwitchWorkspaceResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: SwitchWorkspace,
) -> Response[
    AccountsErrorResponse | ManagementAPIErrorResponse | SwitchWorkspaceResponse
]:
    """Switch to a different workspace with proper validation

    Args:
        body (SwitchWorkspace):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AccountsErrorResponse | ManagementAPIErrorResponse | SwitchWorkspaceResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: SwitchWorkspace,
) -> (
    AccountsErrorResponse | ManagementAPIErrorResponse | SwitchWorkspaceResponse | None
):
    """Switch to a different workspace with proper validation

    Args:
        body (SwitchWorkspace):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AccountsErrorResponse | ManagementAPIErrorResponse | SwitchWorkspaceResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
