from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.scenario_detail_response import ScenarioDetailResponse
from ...models.scenario_error_response import ScenarioErrorResponse
from ...types import Response


def _get_kwargs(
    scenario_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/simulate/scenarios/{scenario_id}/".format(
            scenario_id=quote(str(scenario_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ManagementAPIErrorResponse | ScenarioDetailResponse | ScenarioErrorResponse:
    if response.status_code == 200:
        response_200 = ScenarioDetailResponse.from_dict(response.json())

        return response_200

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
    ManagementAPIErrorResponse | ScenarioDetailResponse | ScenarioErrorResponse
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
) -> Response[
    ManagementAPIErrorResponse | ScenarioDetailResponse | ScenarioErrorResponse
]:
    """Get scenario detail

     Returns full detail of a specific scenario including graph data and prompts.

    Args:
        scenario_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ScenarioDetailResponse | ScenarioErrorResponse]
    """

    kwargs = _get_kwargs(
        scenario_id=scenario_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    scenario_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> ManagementAPIErrorResponse | ScenarioDetailResponse | ScenarioErrorResponse | None:
    """Get scenario detail

     Returns full detail of a specific scenario including graph data and prompts.

    Args:
        scenario_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ScenarioDetailResponse | ScenarioErrorResponse
    """

    return sync_detailed(
        scenario_id=scenario_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    scenario_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    ManagementAPIErrorResponse | ScenarioDetailResponse | ScenarioErrorResponse
]:
    """Get scenario detail

     Returns full detail of a specific scenario including graph data and prompts.

    Args:
        scenario_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ScenarioDetailResponse | ScenarioErrorResponse]
    """

    kwargs = _get_kwargs(
        scenario_id=scenario_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    scenario_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> ManagementAPIErrorResponse | ScenarioDetailResponse | ScenarioErrorResponse | None:
    """Get scenario detail

     Returns full detail of a specific scenario including graph data and prompts.

    Args:
        scenario_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ScenarioDetailResponse | ScenarioErrorResponse
    """

    return (
        await asyncio_detailed(
            scenario_id=scenario_id,
            client=client,
        )
    ).parsed
