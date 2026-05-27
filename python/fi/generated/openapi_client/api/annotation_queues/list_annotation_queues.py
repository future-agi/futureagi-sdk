from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.list_annotation_queues_response_200 import (
    ListAnnotationQueuesResponse200,
)
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    status: str | Unset = UNSET,
    search: str | Unset = UNSET,
    include_counts: bool | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["page"] = page

    params["limit"] = limit

    params["status"] = status

    params["search"] = search

    params["include_counts"] = include_counts

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/model-hub/annotation-queues/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ListAnnotationQueuesResponse200 | ManagementAPIErrorResponse:
    if response.status_code == 200:
        response_200 = ListAnnotationQueuesResponse200.from_dict(response.json())

        return response_200

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ListAnnotationQueuesResponse200 | ManagementAPIErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    status: str | Unset = UNSET,
    search: str | Unset = UNSET,
    include_counts: bool | Unset = UNSET,
) -> Response[ListAnnotationQueuesResponse200 | ManagementAPIErrorResponse]:
    """
    Args:
        page (int | Unset):
        limit (int | Unset):
        status (str | Unset):
        search (str | Unset):
        include_counts (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ListAnnotationQueuesResponse200 | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
        status=status,
        search=search,
        include_counts=include_counts,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    status: str | Unset = UNSET,
    search: str | Unset = UNSET,
    include_counts: bool | Unset = UNSET,
) -> ListAnnotationQueuesResponse200 | ManagementAPIErrorResponse | None:
    """
    Args:
        page (int | Unset):
        limit (int | Unset):
        status (str | Unset):
        search (str | Unset):
        include_counts (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ListAnnotationQueuesResponse200 | ManagementAPIErrorResponse
    """

    return sync_detailed(
        client=client,
        page=page,
        limit=limit,
        status=status,
        search=search,
        include_counts=include_counts,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    status: str | Unset = UNSET,
    search: str | Unset = UNSET,
    include_counts: bool | Unset = UNSET,
) -> Response[ListAnnotationQueuesResponse200 | ManagementAPIErrorResponse]:
    """
    Args:
        page (int | Unset):
        limit (int | Unset):
        status (str | Unset):
        search (str | Unset):
        include_counts (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ListAnnotationQueuesResponse200 | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
        status=status,
        search=search,
        include_counts=include_counts,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    status: str | Unset = UNSET,
    search: str | Unset = UNSET,
    include_counts: bool | Unset = UNSET,
) -> ListAnnotationQueuesResponse200 | ManagementAPIErrorResponse | None:
    """
    Args:
        page (int | Unset):
        limit (int | Unset):
        status (str | Unset):
        search (str | Unset):
        include_counts (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ListAnnotationQueuesResponse200 | ManagementAPIErrorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            page=page,
            limit=limit,
            status=status,
            search=search,
            include_counts=include_counts,
        )
    ).parsed
