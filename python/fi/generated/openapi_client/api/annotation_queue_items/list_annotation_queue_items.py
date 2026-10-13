from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.list_annotation_queue_items_ordering import (
    ListAnnotationQueueItemsOrdering,
)
from ...models.list_annotation_queue_items_response_200 import (
    ListAnnotationQueueItemsResponse200,
)
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    queue_id: str,
    *,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    status: list[str] | Unset = UNSET,
    source_type: list[str] | Unset = UNSET,
    assigned_to: str | Unset = UNSET,
    review_status: str | Unset = UNSET,
    ordering: ListAnnotationQueueItemsOrdering | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["page"] = page

    params["limit"] = limit

    json_status: list[str] | Unset = UNSET
    if not isinstance(status, Unset):
        json_status = status

    params["status"] = json_status

    json_source_type: list[str] | Unset = UNSET
    if not isinstance(source_type, Unset):
        json_source_type = source_type

    params["source_type"] = json_source_type

    params["assigned_to"] = assigned_to

    params["review_status"] = review_status

    json_ordering: str | Unset = UNSET
    if not isinstance(ordering, Unset):
        json_ordering = ordering.value

    params["ordering"] = json_ordering

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/model-hub/annotation-queues/{queue_id}/items/".format(
            queue_id=quote(str(queue_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ListAnnotationQueueItemsResponse200 | ManagementAPIErrorResponse:
    if response.status_code == 200:
        response_200 = ListAnnotationQueueItemsResponse200.from_dict(response.json())

        return response_200

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ListAnnotationQueueItemsResponse200 | ManagementAPIErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    queue_id: str,
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    status: list[str] | Unset = UNSET,
    source_type: list[str] | Unset = UNSET,
    assigned_to: str | Unset = UNSET,
    review_status: str | Unset = UNSET,
    ordering: ListAnnotationQueueItemsOrdering | Unset = UNSET,
) -> Response[ListAnnotationQueueItemsResponse200 | ManagementAPIErrorResponse]:
    """
    Args:
        queue_id (str):
        page (int | Unset):
        limit (int | Unset):
        status (list[str] | Unset):
        source_type (list[str] | Unset):
        assigned_to (str | Unset):
        review_status (str | Unset):
        ordering (ListAnnotationQueueItemsOrdering | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ListAnnotationQueueItemsResponse200 | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        queue_id=queue_id,
        page=page,
        limit=limit,
        status=status,
        source_type=source_type,
        assigned_to=assigned_to,
        review_status=review_status,
        ordering=ordering,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    queue_id: str,
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    status: list[str] | Unset = UNSET,
    source_type: list[str] | Unset = UNSET,
    assigned_to: str | Unset = UNSET,
    review_status: str | Unset = UNSET,
    ordering: ListAnnotationQueueItemsOrdering | Unset = UNSET,
) -> ListAnnotationQueueItemsResponse200 | ManagementAPIErrorResponse | None:
    """
    Args:
        queue_id (str):
        page (int | Unset):
        limit (int | Unset):
        status (list[str] | Unset):
        source_type (list[str] | Unset):
        assigned_to (str | Unset):
        review_status (str | Unset):
        ordering (ListAnnotationQueueItemsOrdering | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ListAnnotationQueueItemsResponse200 | ManagementAPIErrorResponse
    """

    return sync_detailed(
        queue_id=queue_id,
        client=client,
        page=page,
        limit=limit,
        status=status,
        source_type=source_type,
        assigned_to=assigned_to,
        review_status=review_status,
        ordering=ordering,
    ).parsed


async def asyncio_detailed(
    queue_id: str,
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    status: list[str] | Unset = UNSET,
    source_type: list[str] | Unset = UNSET,
    assigned_to: str | Unset = UNSET,
    review_status: str | Unset = UNSET,
    ordering: ListAnnotationQueueItemsOrdering | Unset = UNSET,
) -> Response[ListAnnotationQueueItemsResponse200 | ManagementAPIErrorResponse]:
    """
    Args:
        queue_id (str):
        page (int | Unset):
        limit (int | Unset):
        status (list[str] | Unset):
        source_type (list[str] | Unset):
        assigned_to (str | Unset):
        review_status (str | Unset):
        ordering (ListAnnotationQueueItemsOrdering | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ListAnnotationQueueItemsResponse200 | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        queue_id=queue_id,
        page=page,
        limit=limit,
        status=status,
        source_type=source_type,
        assigned_to=assigned_to,
        review_status=review_status,
        ordering=ordering,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    queue_id: str,
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    status: list[str] | Unset = UNSET,
    source_type: list[str] | Unset = UNSET,
    assigned_to: str | Unset = UNSET,
    review_status: str | Unset = UNSET,
    ordering: ListAnnotationQueueItemsOrdering | Unset = UNSET,
) -> ListAnnotationQueueItemsResponse200 | ManagementAPIErrorResponse | None:
    """
    Args:
        queue_id (str):
        page (int | Unset):
        limit (int | Unset):
        status (list[str] | Unset):
        source_type (list[str] | Unset):
        assigned_to (str | Unset):
        review_status (str | Unset):
        ordering (ListAnnotationQueueItemsOrdering | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ListAnnotationQueueItemsResponse200 | ManagementAPIErrorResponse
    """

    return (
        await asyncio_detailed(
            queue_id=queue_id,
            client=client,
            page=page,
            limit=limit,
            status=status,
            source_type=source_type,
            assigned_to=assigned_to,
            review_status=review_status,
            ordering=ordering,
        )
    ).parsed
