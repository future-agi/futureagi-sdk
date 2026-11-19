from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_text_error_response import ApiTextErrorResponse
from ...models.bulk_review_items_request import BulkReviewItemsRequest
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.queue_bulk_review_items_response import QueueBulkReviewItemsResponse
from ...types import Response


def _get_kwargs(
    queue_id: str,
    *,
    body: BulkReviewItemsRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/model-hub/annotation-queues/{queue_id}/items/bulk-review/".format(
            queue_id=quote(str(queue_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | QueueBulkReviewItemsResponse:
    if response.status_code == 200:
        response_200 = QueueBulkReviewItemsResponse.from_dict(response.json())

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
    ApiTextErrorResponse | ManagementAPIErrorResponse | QueueBulkReviewItemsResponse
]:
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
    body: BulkReviewItemsRequest,
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | QueueBulkReviewItemsResponse
]:
    """Approve or send back multiple pending-review items.

    Args:
        queue_id (str):
        body (BulkReviewItemsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | QueueBulkReviewItemsResponse]
    """

    kwargs = _get_kwargs(
        queue_id=queue_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    queue_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: BulkReviewItemsRequest,
) -> (
    ApiTextErrorResponse
    | ManagementAPIErrorResponse
    | QueueBulkReviewItemsResponse
    | None
):
    """Approve or send back multiple pending-review items.

    Args:
        queue_id (str):
        body (BulkReviewItemsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | QueueBulkReviewItemsResponse
    """

    return sync_detailed(
        queue_id=queue_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    queue_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: BulkReviewItemsRequest,
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | QueueBulkReviewItemsResponse
]:
    """Approve or send back multiple pending-review items.

    Args:
        queue_id (str):
        body (BulkReviewItemsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | QueueBulkReviewItemsResponse]
    """

    kwargs = _get_kwargs(
        queue_id=queue_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    queue_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: BulkReviewItemsRequest,
) -> (
    ApiTextErrorResponse
    | ManagementAPIErrorResponse
    | QueueBulkReviewItemsResponse
    | None
):
    """Approve or send back multiple pending-review items.

    Args:
        queue_id (str):
        body (BulkReviewItemsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | QueueBulkReviewItemsResponse
    """

    return (
        await asyncio_detailed(
            queue_id=queue_id,
            client=client,
            body=body,
        )
    ).parsed
