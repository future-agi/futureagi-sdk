from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.agent_version_restore_response import AgentVersionRestoreResponse
from ...models.api_error_with_details_response import ApiErrorWithDetailsResponse
from ...models.empty_request import EmptyRequest
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...types import Response


def _get_kwargs(
    agent_id: str,
    version_id: str,
    *,
    body: EmptyRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/simulate/agent-definitions/{agent_id}/versions/{version_id}/restore/".format(
            agent_id=quote(str(agent_id), safe=""),
            version_id=quote(str(version_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    AgentVersionRestoreResponse
    | ApiErrorWithDetailsResponse
    | ManagementAPIErrorResponse
):
    if response.status_code == 200:
        response_200 = AgentVersionRestoreResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ApiErrorWithDetailsResponse.from_dict(response.json())

        return response_400

    if response.status_code == 404:
        response_404 = ApiErrorWithDetailsResponse.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = ApiErrorWithDetailsResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    AgentVersionRestoreResponse
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
    agent_id: str,
    version_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: EmptyRequest,
) -> Response[
    AgentVersionRestoreResponse
    | ApiErrorWithDetailsResponse
    | ManagementAPIErrorResponse
]:
    """Restore agent definition from a specific version.

    Args:
        agent_id (str):
        version_id (str):
        body (EmptyRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AgentVersionRestoreResponse | ApiErrorWithDetailsResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        agent_id=agent_id,
        version_id=version_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    agent_id: str,
    version_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: EmptyRequest,
) -> (
    AgentVersionRestoreResponse
    | ApiErrorWithDetailsResponse
    | ManagementAPIErrorResponse
    | None
):
    """Restore agent definition from a specific version.

    Args:
        agent_id (str):
        version_id (str):
        body (EmptyRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AgentVersionRestoreResponse | ApiErrorWithDetailsResponse | ManagementAPIErrorResponse
    """

    return sync_detailed(
        agent_id=agent_id,
        version_id=version_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    agent_id: str,
    version_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: EmptyRequest,
) -> Response[
    AgentVersionRestoreResponse
    | ApiErrorWithDetailsResponse
    | ManagementAPIErrorResponse
]:
    """Restore agent definition from a specific version.

    Args:
        agent_id (str):
        version_id (str):
        body (EmptyRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AgentVersionRestoreResponse | ApiErrorWithDetailsResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        agent_id=agent_id,
        version_id=version_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    agent_id: str,
    version_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: EmptyRequest,
) -> (
    AgentVersionRestoreResponse
    | ApiErrorWithDetailsResponse
    | ManagementAPIErrorResponse
    | None
):
    """Restore agent definition from a specific version.

    Args:
        agent_id (str):
        version_id (str):
        body (EmptyRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AgentVersionRestoreResponse | ApiErrorWithDetailsResponse | ManagementAPIErrorResponse
    """

    return (
        await asyncio_detailed(
            agent_id=agent_id,
            version_id=version_id,
            client=client,
            body=body,
        )
    ).parsed
