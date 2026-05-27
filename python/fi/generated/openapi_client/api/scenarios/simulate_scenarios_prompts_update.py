from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.scenario_edit_prompts_request import ScenarioEditPromptsRequest
from ...models.scenario_error_response import ScenarioErrorResponse
from ...models.scenario_prompts_update_response import ScenarioPromptsUpdateResponse
from ...types import Response


def _get_kwargs(
    scenario_id: str,
    *,
    body: ScenarioEditPromptsRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/simulate/scenarios/{scenario_id}/prompts/".format(
            scenario_id=quote(str(scenario_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ManagementAPIErrorResponse | ScenarioErrorResponse | ScenarioPromptsUpdateResponse:
    if response.status_code == 200:
        response_200 = ScenarioPromptsUpdateResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ScenarioErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 404:
        response_404 = ScenarioErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = ScenarioErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ManagementAPIErrorResponse | ScenarioErrorResponse | ScenarioPromptsUpdateResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    scenario_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: ScenarioEditPromptsRequest,
) -> Response[
    ManagementAPIErrorResponse | ScenarioErrorResponse | ScenarioPromptsUpdateResponse
]:
    """Edit scenario prompts

     Updates the simulator agent prompt for a scenario.

    Args:
        scenario_id (str):
        body (ScenarioEditPromptsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ScenarioErrorResponse | ScenarioPromptsUpdateResponse]
    """

    kwargs = _get_kwargs(
        scenario_id=scenario_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    scenario_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: ScenarioEditPromptsRequest,
) -> (
    ManagementAPIErrorResponse
    | ScenarioErrorResponse
    | ScenarioPromptsUpdateResponse
    | None
):
    """Edit scenario prompts

     Updates the simulator agent prompt for a scenario.

    Args:
        scenario_id (str):
        body (ScenarioEditPromptsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ScenarioErrorResponse | ScenarioPromptsUpdateResponse
    """

    return sync_detailed(
        scenario_id=scenario_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    scenario_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: ScenarioEditPromptsRequest,
) -> Response[
    ManagementAPIErrorResponse | ScenarioErrorResponse | ScenarioPromptsUpdateResponse
]:
    """Edit scenario prompts

     Updates the simulator agent prompt for a scenario.

    Args:
        scenario_id (str):
        body (ScenarioEditPromptsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ScenarioErrorResponse | ScenarioPromptsUpdateResponse]
    """

    kwargs = _get_kwargs(
        scenario_id=scenario_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    scenario_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: ScenarioEditPromptsRequest,
) -> (
    ManagementAPIErrorResponse
    | ScenarioErrorResponse
    | ScenarioPromptsUpdateResponse
    | None
):
    """Edit scenario prompts

     Updates the simulator agent prompt for a scenario.

    Args:
        scenario_id (str):
        body (ScenarioEditPromptsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ScenarioErrorResponse | ScenarioPromptsUpdateResponse
    """

    return (
        await asyncio_detailed(
            scenario_id=scenario_id,
            client=client,
            body=body,
        )
    ).parsed
