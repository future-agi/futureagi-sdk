from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.scenario_add_rows_request import ScenarioAddRowsRequest
from ...models.scenario_add_rows_response import ScenarioAddRowsResponse
from ...models.scenario_error_response import ScenarioErrorResponse
from ...types import Response


def _get_kwargs(
    scenario_id: str,
    *,
    body: ScenarioAddRowsRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/simulate/scenarios/{scenario_id}/add-rows/".format(
            scenario_id=quote(str(scenario_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ManagementAPIErrorResponse | ScenarioAddRowsResponse | ScenarioErrorResponse:
    if response.status_code == 202:
        response_202 = ScenarioAddRowsResponse.from_dict(response.json())

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
    ManagementAPIErrorResponse | ScenarioAddRowsResponse | ScenarioErrorResponse
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
    body: ScenarioAddRowsRequest,
) -> Response[
    ManagementAPIErrorResponse | ScenarioAddRowsResponse | ScenarioErrorResponse
]:
    """Add rows to scenario

     Adds new rows to a scenario's dataset via Temporal workflow. Returns 202 Accepted.

    Args:
        scenario_id (str):
        body (ScenarioAddRowsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ScenarioAddRowsResponse | ScenarioErrorResponse]
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
    body: ScenarioAddRowsRequest,
) -> (
    ManagementAPIErrorResponse | ScenarioAddRowsResponse | ScenarioErrorResponse | None
):
    """Add rows to scenario

     Adds new rows to a scenario's dataset via Temporal workflow. Returns 202 Accepted.

    Args:
        scenario_id (str):
        body (ScenarioAddRowsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ScenarioAddRowsResponse | ScenarioErrorResponse
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
    body: ScenarioAddRowsRequest,
) -> Response[
    ManagementAPIErrorResponse | ScenarioAddRowsResponse | ScenarioErrorResponse
]:
    """Add rows to scenario

     Adds new rows to a scenario's dataset via Temporal workflow. Returns 202 Accepted.

    Args:
        scenario_id (str):
        body (ScenarioAddRowsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ScenarioAddRowsResponse | ScenarioErrorResponse]
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
    body: ScenarioAddRowsRequest,
) -> (
    ManagementAPIErrorResponse | ScenarioAddRowsResponse | ScenarioErrorResponse | None
):
    """Add rows to scenario

     Adds new rows to a scenario's dataset via Temporal workflow. Returns 202 Accepted.

    Args:
        scenario_id (str):
        body (ScenarioAddRowsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ScenarioAddRowsResponse | ScenarioErrorResponse
    """

    return (
        await asyncio_detailed(
            scenario_id=scenario_id,
            client=client,
            body=body,
        )
    ).parsed
