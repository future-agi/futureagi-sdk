from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.accounts_error_response import AccountsErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.member_role_update import MemberRoleUpdate
from ...models.member_role_update_response import MemberRoleUpdateResponse
from ...types import Response


def _get_kwargs(
    *,
    body: MemberRoleUpdate,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/accounts/organization/members/role/",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AccountsErrorResponse | ManagementAPIErrorResponse | MemberRoleUpdateResponse:
    if response.status_code == 200:
        response_200 = MemberRoleUpdateResponse.from_dict(response.json())

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
    AccountsErrorResponse | ManagementAPIErrorResponse | MemberRoleUpdateResponse
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
    body: MemberRoleUpdate,
) -> Response[
    AccountsErrorResponse | ManagementAPIErrorResponse | MemberRoleUpdateResponse
]:
    """POST /accounts/organization/members/role/

     Update a member's org level and/or workspace level.

    Args:
        body (MemberRoleUpdate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AccountsErrorResponse | ManagementAPIErrorResponse | MemberRoleUpdateResponse]
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
    body: MemberRoleUpdate,
) -> (
    AccountsErrorResponse | ManagementAPIErrorResponse | MemberRoleUpdateResponse | None
):
    """POST /accounts/organization/members/role/

     Update a member's org level and/or workspace level.

    Args:
        body (MemberRoleUpdate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AccountsErrorResponse | ManagementAPIErrorResponse | MemberRoleUpdateResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: MemberRoleUpdate,
) -> Response[
    AccountsErrorResponse | ManagementAPIErrorResponse | MemberRoleUpdateResponse
]:
    """POST /accounts/organization/members/role/

     Update a member's org level and/or workspace level.

    Args:
        body (MemberRoleUpdate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AccountsErrorResponse | ManagementAPIErrorResponse | MemberRoleUpdateResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: MemberRoleUpdate,
) -> (
    AccountsErrorResponse | ManagementAPIErrorResponse | MemberRoleUpdateResponse | None
):
    """POST /accounts/organization/members/role/

     Update a member's org level and/or workspace level.

    Args:
        body (MemberRoleUpdate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AccountsErrorResponse | ManagementAPIErrorResponse | MemberRoleUpdateResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
