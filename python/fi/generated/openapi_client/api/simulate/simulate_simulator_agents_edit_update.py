from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.simulator_agent import SimulatorAgent
from ...models.simulator_agent_validation_error_response import (
    SimulatorAgentValidationErrorResponse,
)
from ...types import Response


def _get_kwargs(
    agent_id: str,
    *,
    body: SimulatorAgent,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/simulate/simulator-agents/{agent_id}/edit/".format(
            agent_id=quote(str(agent_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ManagementAPIErrorResponse | SimulatorAgent | SimulatorAgentValidationErrorResponse
):
    if response.status_code == 200:
        response_200 = SimulatorAgent.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = SimulatorAgentValidationErrorResponse.from_dict(response.json())

        return response_400

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ManagementAPIErrorResponse | SimulatorAgent | SimulatorAgentValidationErrorResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    agent_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: SimulatorAgent,
) -> Response[
    ManagementAPIErrorResponse | SimulatorAgent | SimulatorAgentValidationErrorResponse
]:
    """Edit an existing simulator agent

    Args:
        agent_id (str):
        body (SimulatorAgent):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | SimulatorAgent | SimulatorAgentValidationErrorResponse]
    """

    kwargs = _get_kwargs(
        agent_id=agent_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    agent_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: SimulatorAgent,
) -> (
    ManagementAPIErrorResponse
    | SimulatorAgent
    | SimulatorAgentValidationErrorResponse
    | None
):
    """Edit an existing simulator agent

    Args:
        agent_id (str):
        body (SimulatorAgent):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | SimulatorAgent | SimulatorAgentValidationErrorResponse
    """

    return sync_detailed(
        agent_id=agent_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    agent_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: SimulatorAgent,
) -> Response[
    ManagementAPIErrorResponse | SimulatorAgent | SimulatorAgentValidationErrorResponse
]:
    """Edit an existing simulator agent

    Args:
        agent_id (str):
        body (SimulatorAgent):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | SimulatorAgent | SimulatorAgentValidationErrorResponse]
    """

    kwargs = _get_kwargs(
        agent_id=agent_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    agent_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: SimulatorAgent,
) -> (
    ManagementAPIErrorResponse
    | SimulatorAgent
    | SimulatorAgentValidationErrorResponse
    | None
):
    """Edit an existing simulator agent

    Args:
        agent_id (str):
        body (SimulatorAgent):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | SimulatorAgent | SimulatorAgentValidationErrorResponse
    """

    return (
        await asyncio_detailed(
            agent_id=agent_id,
            client=client,
            body=body,
        )
    ).parsed
