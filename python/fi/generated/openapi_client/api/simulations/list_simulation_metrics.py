from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.sdk_error_response import SDKErrorResponse
from ...models.sdk_simulation_metrics_response import SDKSimulationMetricsResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    run_test_name: str | Unset = UNSET,
    execution_id: UUID | Unset = UNSET,
    call_execution_id: UUID | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["run_test_name"] = run_test_name

    json_execution_id: str | Unset = UNSET
    if not isinstance(execution_id, Unset):
        json_execution_id = str(execution_id)
    params["execution_id"] = json_execution_id

    json_call_execution_id: str | Unset = UNSET
    if not isinstance(call_execution_id, Unset):
        json_call_execution_id = str(call_execution_id)
    params["call_execution_id"] = json_call_execution_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/sdk/api/v1/simulation/metrics/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ManagementAPIErrorResponse | SDKErrorResponse | SDKSimulationMetricsResponse:
    if response.status_code == 200:
        response_200 = SDKSimulationMetricsResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = SDKErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 404:
        response_404 = SDKErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = SDKErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ManagementAPIErrorResponse | SDKErrorResponse | SDKSimulationMetricsResponse
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
    run_test_name: str | Unset = UNSET,
    execution_id: UUID | Unset = UNSET,
    call_execution_id: UUID | Unset = UNSET,
) -> Response[
    ManagementAPIErrorResponse | SDKErrorResponse | SDKSimulationMetricsResponse
]:
    """GET /simulation/metrics/

     Aggregated system metrics: latency (by subsystem), cost, conversation metrics.

    Args:
        run_test_name (str | Unset):
        execution_id (UUID | Unset):
        call_execution_id (UUID | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | SDKErrorResponse | SDKSimulationMetricsResponse]
    """

    kwargs = _get_kwargs(
        run_test_name=run_test_name,
        execution_id=execution_id,
        call_execution_id=call_execution_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    run_test_name: str | Unset = UNSET,
    execution_id: UUID | Unset = UNSET,
    call_execution_id: UUID | Unset = UNSET,
) -> (
    ManagementAPIErrorResponse | SDKErrorResponse | SDKSimulationMetricsResponse | None
):
    """GET /simulation/metrics/

     Aggregated system metrics: latency (by subsystem), cost, conversation metrics.

    Args:
        run_test_name (str | Unset):
        execution_id (UUID | Unset):
        call_execution_id (UUID | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | SDKErrorResponse | SDKSimulationMetricsResponse
    """

    return sync_detailed(
        client=client,
        run_test_name=run_test_name,
        execution_id=execution_id,
        call_execution_id=call_execution_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    run_test_name: str | Unset = UNSET,
    execution_id: UUID | Unset = UNSET,
    call_execution_id: UUID | Unset = UNSET,
) -> Response[
    ManagementAPIErrorResponse | SDKErrorResponse | SDKSimulationMetricsResponse
]:
    """GET /simulation/metrics/

     Aggregated system metrics: latency (by subsystem), cost, conversation metrics.

    Args:
        run_test_name (str | Unset):
        execution_id (UUID | Unset):
        call_execution_id (UUID | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | SDKErrorResponse | SDKSimulationMetricsResponse]
    """

    kwargs = _get_kwargs(
        run_test_name=run_test_name,
        execution_id=execution_id,
        call_execution_id=call_execution_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    run_test_name: str | Unset = UNSET,
    execution_id: UUID | Unset = UNSET,
    call_execution_id: UUID | Unset = UNSET,
) -> (
    ManagementAPIErrorResponse | SDKErrorResponse | SDKSimulationMetricsResponse | None
):
    """GET /simulation/metrics/

     Aggregated system metrics: latency (by subsystem), cost, conversation metrics.

    Args:
        run_test_name (str | Unset):
        execution_id (UUID | Unset):
        call_execution_id (UUID | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | SDKErrorResponse | SDKSimulationMetricsResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            run_test_name=run_test_name,
            execution_id=execution_id,
            call_execution_id=call_execution_id,
        )
    ).parsed
