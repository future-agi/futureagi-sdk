from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.accounts_error_response import AccountsErrorResponse
from ...models.list_organization_members_filter_status_item import (
    ListOrganizationMembersFilterStatusItem,
)
from ...models.list_organization_members_sort import ListOrganizationMembersSort
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.member_list_response import MemberListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    page: int | Unset = 1,
    limit: int | Unset = 20,
    search: str | Unset = "",
    filter_status: list[ListOrganizationMembersFilterStatusItem] | Unset = UNSET,
    filter_role: list[str] | Unset = UNSET,
    sort: ListOrganizationMembersSort | Unset = ListOrganizationMembersSort.VALUE_11,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["page"] = page

    params["limit"] = limit

    params["search"] = search

    json_filter_status: list[str] | Unset = UNSET
    if not isinstance(filter_status, Unset):
        json_filter_status = []
        for filter_status_item_data in filter_status:
            filter_status_item = filter_status_item_data.value
            json_filter_status.append(filter_status_item)

    params["filter_status"] = json_filter_status

    json_filter_role: list[str] | Unset = UNSET
    if not isinstance(filter_role, Unset):
        json_filter_role = filter_role

    params["filter_role"] = json_filter_role

    json_sort: str | Unset = UNSET
    if not isinstance(sort, Unset):
        json_sort = sort.value

    params["sort"] = json_sort

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/accounts/organization/members/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AccountsErrorResponse | ManagementAPIErrorResponse | MemberListResponse:
    if response.status_code == 200:
        response_200 = MemberListResponse.from_dict(response.json())

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
) -> Response[AccountsErrorResponse | ManagementAPIErrorResponse | MemberListResponse]:
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
    limit: int | Unset = 20,
    search: str | Unset = "",
    filter_status: list[ListOrganizationMembersFilterStatusItem] | Unset = UNSET,
    filter_role: list[str] | Unset = UNSET,
    sort: ListOrganizationMembersSort | Unset = ListOrganizationMembersSort.VALUE_11,
) -> Response[AccountsErrorResponse | ManagementAPIErrorResponse | MemberListResponse]:
    """GET /accounts/organization/members/

     Returns UNION of active members + pending/expired invites.
    Status is derived at query time (Active / Pending / Expired).

    Args:
        page (int | Unset):  Default: 1.
        limit (int | Unset):  Default: 20.
        search (str | Unset):  Default: ''.
        filter_status (list[ListOrganizationMembersFilterStatusItem] | Unset):
        filter_role (list[str] | Unset):
        sort (ListOrganizationMembersSort | Unset):  Default:
            ListOrganizationMembersSort.VALUE_11.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AccountsErrorResponse | ManagementAPIErrorResponse | MemberListResponse]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
        search=search,
        filter_status=filter_status,
        filter_role=filter_role,
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
    limit: int | Unset = 20,
    search: str | Unset = "",
    filter_status: list[ListOrganizationMembersFilterStatusItem] | Unset = UNSET,
    filter_role: list[str] | Unset = UNSET,
    sort: ListOrganizationMembersSort | Unset = ListOrganizationMembersSort.VALUE_11,
) -> AccountsErrorResponse | ManagementAPIErrorResponse | MemberListResponse | None:
    """GET /accounts/organization/members/

     Returns UNION of active members + pending/expired invites.
    Status is derived at query time (Active / Pending / Expired).

    Args:
        page (int | Unset):  Default: 1.
        limit (int | Unset):  Default: 20.
        search (str | Unset):  Default: ''.
        filter_status (list[ListOrganizationMembersFilterStatusItem] | Unset):
        filter_role (list[str] | Unset):
        sort (ListOrganizationMembersSort | Unset):  Default:
            ListOrganizationMembersSort.VALUE_11.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AccountsErrorResponse | ManagementAPIErrorResponse | MemberListResponse
    """

    return sync_detailed(
        client=client,
        page=page,
        limit=limit,
        search=search,
        filter_status=filter_status,
        filter_role=filter_role,
        sort=sort,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = 1,
    limit: int | Unset = 20,
    search: str | Unset = "",
    filter_status: list[ListOrganizationMembersFilterStatusItem] | Unset = UNSET,
    filter_role: list[str] | Unset = UNSET,
    sort: ListOrganizationMembersSort | Unset = ListOrganizationMembersSort.VALUE_11,
) -> Response[AccountsErrorResponse | ManagementAPIErrorResponse | MemberListResponse]:
    """GET /accounts/organization/members/

     Returns UNION of active members + pending/expired invites.
    Status is derived at query time (Active / Pending / Expired).

    Args:
        page (int | Unset):  Default: 1.
        limit (int | Unset):  Default: 20.
        search (str | Unset):  Default: ''.
        filter_status (list[ListOrganizationMembersFilterStatusItem] | Unset):
        filter_role (list[str] | Unset):
        sort (ListOrganizationMembersSort | Unset):  Default:
            ListOrganizationMembersSort.VALUE_11.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AccountsErrorResponse | ManagementAPIErrorResponse | MemberListResponse]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
        search=search,
        filter_status=filter_status,
        filter_role=filter_role,
        sort=sort,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = 1,
    limit: int | Unset = 20,
    search: str | Unset = "",
    filter_status: list[ListOrganizationMembersFilterStatusItem] | Unset = UNSET,
    filter_role: list[str] | Unset = UNSET,
    sort: ListOrganizationMembersSort | Unset = ListOrganizationMembersSort.VALUE_11,
) -> AccountsErrorResponse | ManagementAPIErrorResponse | MemberListResponse | None:
    """GET /accounts/organization/members/

     Returns UNION of active members + pending/expired invites.
    Status is derived at query time (Active / Pending / Expired).

    Args:
        page (int | Unset):  Default: 1.
        limit (int | Unset):  Default: 20.
        search (str | Unset):  Default: ''.
        filter_status (list[ListOrganizationMembersFilterStatusItem] | Unset):
        filter_role (list[str] | Unset):
        sort (ListOrganizationMembersSort | Unset):  Default:
            ListOrganizationMembersSort.VALUE_11.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AccountsErrorResponse | ManagementAPIErrorResponse | MemberListResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            page=page,
            limit=limit,
            search=search,
            filter_status=filter_status,
            filter_role=filter_role,
            sort=sort,
        )
    ).parsed
