from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.add_items import AddItems
from ...models.api_text_error_response import ApiTextErrorResponse
from ...models.api_too_large_error import ApiTooLargeError
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.queue_add_items_response import QueueAddItemsResponse
from ...types import Response


def _get_kwargs(
    queue_id: str,
    *,
    body: AddItems,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/model-hub/annotation-queues/{queue_id}/items/add-items/".format(
            queue_id=quote(str(queue_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ApiTextErrorResponse
    | ApiTooLargeError
    | ManagementAPIErrorResponse
    | QueueAddItemsResponse
):
    if response.status_code == 200:
        response_200 = QueueAddItemsResponse.from_dict(response.json())

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

    if response.status_code == 413:
        response_413 = ApiTooLargeError.from_dict(response.json())

        return response_413

    if response.status_code == 503:
        response_503 = ApiTextErrorResponse.from_dict(response.json())

        return response_503

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ApiTextErrorResponse
    | ApiTooLargeError
    | ManagementAPIErrorResponse
    | QueueAddItemsResponse
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
    body: AddItems,
) -> Response[
    ApiTextErrorResponse
    | ApiTooLargeError
    | ManagementAPIErrorResponse
    | QueueAddItemsResponse
]:
    """
    Args:
        queue_id (str):
        body (AddItems):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ApiTooLargeError | ManagementAPIErrorResponse | QueueAddItemsResponse]
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
    body: AddItems,
) -> (
    ApiTextErrorResponse
    | ApiTooLargeError
    | ManagementAPIErrorResponse
    | QueueAddItemsResponse
    | None
):
    """
    Args:
        queue_id (str):
        body (AddItems):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ApiTooLargeError | ManagementAPIErrorResponse | QueueAddItemsResponse
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
    body: AddItems,
) -> Response[
    ApiTextErrorResponse
    | ApiTooLargeError
    | ManagementAPIErrorResponse
    | QueueAddItemsResponse
]:
    """
    Args:
        queue_id (str):
        body (AddItems):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ApiTooLargeError | ManagementAPIErrorResponse | QueueAddItemsResponse]
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
    body: AddItems,
) -> (
    ApiTextErrorResponse
    | ApiTooLargeError
    | ManagementAPIErrorResponse
    | QueueAddItemsResponse
    | None
):
    """
    Args:
        queue_id (str):
        body (AddItems):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ApiTooLargeError | ManagementAPIErrorResponse | QueueAddItemsResponse
    """

    return (
        await asyncio_detailed(
            queue_id=queue_id,
            client=client,
            body=body,
        )
    ).parsed
