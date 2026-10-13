from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.agent_definition_bulk_delete_request import (
    AgentDefinitionBulkDeleteRequest,
)
from ...models.agent_definition_bulk_delete_response import (
    AgentDefinitionBulkDeleteResponse,
)
from ...models.api_error_with_details_response import ApiErrorWithDetailsResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...types import Response


def _get_kwargs(
    *,
    body: AgentDefinitionBulkDeleteRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/simulate/agent-definitions/",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    AgentDefinitionBulkDeleteResponse
    | ApiErrorWithDetailsResponse
    | ManagementAPIErrorResponse
):
    if response.status_code == 200:
        response_200 = AgentDefinitionBulkDeleteResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ApiErrorWithDetailsResponse.from_dict(response.json())

        return response_400

    if response.status_code == 500:
        response_500 = ApiErrorWithDetailsResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    AgentDefinitionBulkDeleteResponse
    | ApiErrorWithDetailsResponse
    | ManagementAPIErrorResponse
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
    body: AgentDefinitionBulkDeleteRequest,
) -> Response[
    AgentDefinitionBulkDeleteResponse
    | ApiErrorWithDetailsResponse
    | ManagementAPIErrorResponse
]:
    """Bulk soft-delete agent definitions.

    Args:
        body (AgentDefinitionBulkDeleteRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AgentDefinitionBulkDeleteResponse | ApiErrorWithDetailsResponse | ManagementAPIErrorResponse]
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
    body: AgentDefinitionBulkDeleteRequest,
) -> (
    AgentDefinitionBulkDeleteResponse
    | ApiErrorWithDetailsResponse
    | ManagementAPIErrorResponse
    | None
):
    """Bulk soft-delete agent definitions.

    Args:
        body (AgentDefinitionBulkDeleteRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AgentDefinitionBulkDeleteResponse | ApiErrorWithDetailsResponse | ManagementAPIErrorResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: AgentDefinitionBulkDeleteRequest,
) -> Response[
    AgentDefinitionBulkDeleteResponse
    | ApiErrorWithDetailsResponse
    | ManagementAPIErrorResponse
]:
    """Bulk soft-delete agent definitions.

    Args:
        body (AgentDefinitionBulkDeleteRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AgentDefinitionBulkDeleteResponse | ApiErrorWithDetailsResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: AgentDefinitionBulkDeleteRequest,
) -> (
    AgentDefinitionBulkDeleteResponse
    | ApiErrorWithDetailsResponse
    | ManagementAPIErrorResponse
    | None
):
    """Bulk soft-delete agent definitions.

    Args:
        body (AgentDefinitionBulkDeleteRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AgentDefinitionBulkDeleteResponse | ApiErrorWithDetailsResponse | ManagementAPIErrorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
