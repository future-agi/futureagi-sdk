from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.accounts_error_response import AccountsErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.member_user_mutation_response import MemberUserMutationResponse
from ...models.workspace_member_remove import WorkspaceMemberRemove
from ...types import Response


def _get_kwargs(
    workspace_id: str,
    *,
    body: WorkspaceMemberRemove,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/accounts/workspace/{workspace_id}/members/remove/".format(
            workspace_id=quote(str(workspace_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AccountsErrorResponse | ManagementAPIErrorResponse | MemberUserMutationResponse:
    if response.status_code == 200:
        response_200 = MemberUserMutationResponse.from_dict(response.json())

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
    AccountsErrorResponse | ManagementAPIErrorResponse | MemberUserMutationResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    workspace_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: WorkspaceMemberRemove,
) -> Response[
    AccountsErrorResponse | ManagementAPIErrorResponse | MemberUserMutationResponse
]:
    """DELETE /accounts/workspace/<workspace_id>/members/remove/

     Remove a member from a workspace only (keeps org membership).

    Args:
        workspace_id (str):
        body (WorkspaceMemberRemove):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AccountsErrorResponse | ManagementAPIErrorResponse | MemberUserMutationResponse]
    """

    kwargs = _get_kwargs(
        workspace_id=workspace_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    workspace_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: WorkspaceMemberRemove,
) -> (
    AccountsErrorResponse
    | ManagementAPIErrorResponse
    | MemberUserMutationResponse
    | None
):
    """DELETE /accounts/workspace/<workspace_id>/members/remove/

     Remove a member from a workspace only (keeps org membership).

    Args:
        workspace_id (str):
        body (WorkspaceMemberRemove):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AccountsErrorResponse | ManagementAPIErrorResponse | MemberUserMutationResponse
    """

    return sync_detailed(
        workspace_id=workspace_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    workspace_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: WorkspaceMemberRemove,
) -> Response[
    AccountsErrorResponse | ManagementAPIErrorResponse | MemberUserMutationResponse
]:
    """DELETE /accounts/workspace/<workspace_id>/members/remove/

     Remove a member from a workspace only (keeps org membership).

    Args:
        workspace_id (str):
        body (WorkspaceMemberRemove):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AccountsErrorResponse | ManagementAPIErrorResponse | MemberUserMutationResponse]
    """

    kwargs = _get_kwargs(
        workspace_id=workspace_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    workspace_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: WorkspaceMemberRemove,
) -> (
    AccountsErrorResponse
    | ManagementAPIErrorResponse
    | MemberUserMutationResponse
    | None
):
    """DELETE /accounts/workspace/<workspace_id>/members/remove/

     Remove a member from a workspace only (keeps org membership).

    Args:
        workspace_id (str):
        body (WorkspaceMemberRemove):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AccountsErrorResponse | ManagementAPIErrorResponse | MemberUserMutationResponse
    """

    return (
        await asyncio_detailed(
            workspace_id=workspace_id,
            client=client,
            body=body,
        )
    ).parsed
