from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.scenario_add_columns_request import ScenarioAddColumnsRequest
from ...models.scenario_add_columns_response import ScenarioAddColumnsResponse
from ...models.scenario_error_response import ScenarioErrorResponse
from ...types import Response


def _get_kwargs(
    scenario_id: str,
    *,
    body: ScenarioAddColumnsRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/simulate/scenarios/{scenario_id}/add-columns/".format(
            scenario_id=quote(str(scenario_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ManagementAPIErrorResponse | ScenarioAddColumnsResponse | ScenarioErrorResponse:
    if response.status_code == 202:
        response_202 = ScenarioAddColumnsResponse.from_dict(response.json())

        return response_202

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
    ManagementAPIErrorResponse | ScenarioAddColumnsResponse | ScenarioErrorResponse
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
    body: ScenarioAddColumnsRequest,
) -> Response[
    ManagementAPIErrorResponse | ScenarioAddColumnsResponse | ScenarioErrorResponse
]:
    """Add columns to scenario

     Adds new columns to a scenario's dataset via Temporal workflow. Returns 202 Accepted.

    Args:
        scenario_id (str):
        body (ScenarioAddColumnsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ScenarioAddColumnsResponse | ScenarioErrorResponse]
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
    body: ScenarioAddColumnsRequest,
) -> (
    ManagementAPIErrorResponse
    | ScenarioAddColumnsResponse
    | ScenarioErrorResponse
    | None
):
    """Add columns to scenario

     Adds new columns to a scenario's dataset via Temporal workflow. Returns 202 Accepted.

    Args:
        scenario_id (str):
        body (ScenarioAddColumnsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ScenarioAddColumnsResponse | ScenarioErrorResponse
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
    body: ScenarioAddColumnsRequest,
) -> Response[
    ManagementAPIErrorResponse | ScenarioAddColumnsResponse | ScenarioErrorResponse
]:
    """Add columns to scenario

     Adds new columns to a scenario's dataset via Temporal workflow. Returns 202 Accepted.

    Args:
        scenario_id (str):
        body (ScenarioAddColumnsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ScenarioAddColumnsResponse | ScenarioErrorResponse]
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
    body: ScenarioAddColumnsRequest,
) -> (
    ManagementAPIErrorResponse
    | ScenarioAddColumnsResponse
    | ScenarioErrorResponse
    | None
):
    """Add columns to scenario

     Adds new columns to a scenario's dataset via Temporal workflow. Returns 202 Accepted.

    Args:
        scenario_id (str):
        body (ScenarioAddColumnsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ScenarioAddColumnsResponse | ScenarioErrorResponse
    """

    return (
        await asyncio_detailed(
            scenario_id=scenario_id,
            client=client,
            body=body,
        )
    ).parsed
