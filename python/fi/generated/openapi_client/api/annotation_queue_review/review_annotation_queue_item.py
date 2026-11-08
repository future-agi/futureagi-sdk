from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_text_error_response import ApiTextErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.queue_review_item_response import QueueReviewItemResponse
from ...models.review_item_request import ReviewItemRequest
from ...types import Response


def _get_kwargs(
    queue_id: str,
    id: UUID,
    *,
    body: ReviewItemRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/model-hub/annotation-queues/{queue_id}/items/{id}/review/".format(
            queue_id=quote(str(queue_id), safe=""),
            id=quote(str(id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | QueueReviewItemResponse:
    if response.status_code == 200:
        response_200 = QueueReviewItemResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ApiTextErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 403:
        response_403 = ApiTextErrorResponse.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = ApiTextErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 409:
        response_409 = ApiTextErrorResponse.from_dict(response.json())

        return response_409

    if response.status_code == 500:
        response_500 = ApiTextErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | QueueReviewItemResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    queue_id: str,
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: ReviewItemRequest,
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | QueueReviewItemResponse
]:
    """Approve, request changes, or leave reviewer feedback on an item.

    Args:
        queue_id (str):
        id (UUID):
        body (ReviewItemRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | QueueReviewItemResponse]
    """

    kwargs = _get_kwargs(
        queue_id=queue_id,
        id=id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    queue_id: str,
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: ReviewItemRequest,
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | QueueReviewItemResponse | None:
    """Approve, request changes, or leave reviewer feedback on an item.

    Args:
        queue_id (str):
        id (UUID):
        body (ReviewItemRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | QueueReviewItemResponse
    """

    return sync_detailed(
        queue_id=queue_id,
        id=id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    queue_id: str,
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: ReviewItemRequest,
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | QueueReviewItemResponse
]:
    """Approve, request changes, or leave reviewer feedback on an item.

    Args:
        queue_id (str):
        id (UUID):
        body (ReviewItemRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | QueueReviewItemResponse]
    """

    kwargs = _get_kwargs(
        queue_id=queue_id,
        id=id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    queue_id: str,
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: ReviewItemRequest,
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | QueueReviewItemResponse | None:
    """Approve, request changes, or leave reviewer feedback on an item.

    Args:
        queue_id (str):
        id (UUID):
        body (ReviewItemRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | QueueReviewItemResponse
    """

    return (
        await asyncio_detailed(
            queue_id=queue_id,
            id=id,
            client=client,
            body=body,
        )
    ).parsed
