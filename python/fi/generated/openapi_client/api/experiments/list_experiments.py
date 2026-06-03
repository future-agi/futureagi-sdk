from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.list_experiments_response_200 import ListExperimentsResponse200
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    created_at: str | Unset = UNSET,
    status: str | Unset = UNSET,
    dataset_id: str | Unset = UNSET,
    search: str | Unset = UNSET,
    ordering: str | Unset = UNSET,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["created_at"] = created_at

    params["status"] = status

    params["dataset_id"] = dataset_id

    params["search"] = search

    params["ordering"] = ordering

    params["page"] = page

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/model-hub/experiments/v2/list/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ListExperimentsResponse200 | ManagementAPIErrorResponse:
    if response.status_code == 200:
        response_200 = ListExperimentsResponse200.from_dict(response.json())

        return response_200

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ListExperimentsResponse200 | ManagementAPIErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    created_at: str | Unset = UNSET,
    status: str | Unset = UNSET,
    dataset_id: str | Unset = UNSET,
    search: str | Unset = UNSET,
    ordering: str | Unset = UNSET,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
) -> Response[ListExperimentsResponse200 | ManagementAPIErrorResponse]:
    """V2 experiment list with filtering, search, and pagination.

    Args:
        created_at (str | Unset):
        status (str | Unset):
        dataset_id (str | Unset):
        search (str | Unset):
        ordering (str | Unset):
        page (int | Unset):
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ListExperimentsResponse200 | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        created_at=created_at,
        status=status,
        dataset_id=dataset_id,
        search=search,
        ordering=ordering,
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
    created_at: str | Unset = UNSET,
    status: str | Unset = UNSET,
    dataset_id: str | Unset = UNSET,
    search: str | Unset = UNSET,
    ordering: str | Unset = UNSET,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
) -> ListExperimentsResponse200 | ManagementAPIErrorResponse | None:
    """V2 experiment list with filtering, search, and pagination.

    Args:
        created_at (str | Unset):
        status (str | Unset):
        dataset_id (str | Unset):
        search (str | Unset):
        ordering (str | Unset):
        page (int | Unset):
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ListExperimentsResponse200 | ManagementAPIErrorResponse
    """

    return sync_detailed(
        client=client,
        created_at=created_at,
        status=status,
        dataset_id=dataset_id,
        search=search,
        ordering=ordering,
        page=page,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    created_at: str | Unset = UNSET,
    status: str | Unset = UNSET,
    dataset_id: str | Unset = UNSET,
    search: str | Unset = UNSET,
    ordering: str | Unset = UNSET,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
) -> Response[ListExperimentsResponse200 | ManagementAPIErrorResponse]:
    """V2 experiment list with filtering, search, and pagination.

    Args:
        created_at (str | Unset):
        status (str | Unset):
        dataset_id (str | Unset):
        search (str | Unset):
        ordering (str | Unset):
        page (int | Unset):
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ListExperimentsResponse200 | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        created_at=created_at,
        status=status,
        dataset_id=dataset_id,
        search=search,
        ordering=ordering,
        page=page,
        limit=limit,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    created_at: str | Unset = UNSET,
    status: str | Unset = UNSET,
    dataset_id: str | Unset = UNSET,
    search: str | Unset = UNSET,
    ordering: str | Unset = UNSET,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
) -> ListExperimentsResponse200 | ManagementAPIErrorResponse | None:
    """V2 experiment list with filtering, search, and pagination.

    Args:
        created_at (str | Unset):
        status (str | Unset):
        dataset_id (str | Unset):
        search (str | Unset):
        ordering (str | Unset):
        page (int | Unset):
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ListExperimentsResponse200 | ManagementAPIErrorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            created_at=created_at,
            status=status,
            dataset_id=dataset_id,
            search=search,
            ordering=ordering,
            page=page,
            limit=limit,
        )
    ).parsed
