from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.automation_rule import AutomationRule
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...types import Response


def _get_kwargs(
    queue_id: str,
    id: UUID,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/model-hub/annotation-queues/{queue_id}/automation-rules/{id}/".format(
            queue_id=quote(str(queue_id), safe=""),
            id=quote(str(id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AutomationRule | ManagementAPIErrorResponse:
    if response.status_code == 200:
        response_200 = AutomationRule.from_dict(response.json())

        return response_200

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[AutomationRule | ManagementAPIErrorResponse]:
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
) -> Response[AutomationRule | ManagementAPIErrorResponse]:
    """
    Args:
        queue_id (str):
        id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AutomationRule | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        queue_id=queue_id,
        id=id,
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
) -> AutomationRule | ManagementAPIErrorResponse | None:
    """
    Args:
        queue_id (str):
        id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AutomationRule | ManagementAPIErrorResponse
    """

    return sync_detailed(
        queue_id=queue_id,
        id=id,
        client=client,
    ).parsed


async def asyncio_detailed(
    queue_id: str,
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
) -> Response[AutomationRule | ManagementAPIErrorResponse]:
    """
    Args:
        queue_id (str):
        id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AutomationRule | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        queue_id=queue_id,
        id=id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    queue_id: str,
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
) -> AutomationRule | ManagementAPIErrorResponse | None:
    """
    Args:
        queue_id (str):
        id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AutomationRule | ManagementAPIErrorResponse
    """

    return (
        await asyncio_detailed(
            queue_id=queue_id,
            id=id,
            client=client,
        )
    ).parsed
