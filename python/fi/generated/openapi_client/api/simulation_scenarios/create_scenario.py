from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.scenario_create_request import ScenarioCreateRequest
from ...models.scenario_create_response import ScenarioCreateResponse
from ...models.scenario_error_response import ScenarioErrorResponse
from ...types import Response


def _get_kwargs(
    *,
    body: ScenarioCreateRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/simulate/scenarios/create/",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ManagementAPIErrorResponse | ScenarioCreateResponse | ScenarioErrorResponse:
    if response.status_code == 202:
        response_202 = ScenarioCreateResponse.from_dict(response.json())

        return response_202

    if response.status_code == 400:
        response_400 = ScenarioErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 500:
        response_500 = ScenarioErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ManagementAPIErrorResponse | ScenarioCreateResponse | ScenarioErrorResponse
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
    body: ScenarioCreateRequest,
) -> Response[
    ManagementAPIErrorResponse | ScenarioCreateResponse | ScenarioErrorResponse
]:
    """Create scenario

     Creates a new scenario (dataset, script, or graph kind). Returns 202 with processing status.

    Args:
        body (ScenarioCreateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ScenarioCreateResponse | ScenarioErrorResponse]
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
    body: ScenarioCreateRequest,
) -> ManagementAPIErrorResponse | ScenarioCreateResponse | ScenarioErrorResponse | None:
    """Create scenario

     Creates a new scenario (dataset, script, or graph kind). Returns 202 with processing status.

    Args:
        body (ScenarioCreateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ScenarioCreateResponse | ScenarioErrorResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: ScenarioCreateRequest,
) -> Response[
    ManagementAPIErrorResponse | ScenarioCreateResponse | ScenarioErrorResponse
]:
    """Create scenario

     Creates a new scenario (dataset, script, or graph kind). Returns 202 with processing status.

    Args:
        body (ScenarioCreateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ScenarioCreateResponse | ScenarioErrorResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: ScenarioCreateRequest,
) -> ManagementAPIErrorResponse | ScenarioCreateResponse | ScenarioErrorResponse | None:
    """Create scenario

     Creates a new scenario (dataset, script, or graph kind). Returns 202 with processing status.

    Args:
        body (ScenarioCreateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ScenarioCreateResponse | ScenarioErrorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
