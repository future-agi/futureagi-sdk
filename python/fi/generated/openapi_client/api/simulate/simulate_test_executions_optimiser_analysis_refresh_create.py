from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_text_error_response import ApiTextErrorResponse
from ...models.empty_request import EmptyRequest
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.optimiser_analysis_refresh_response import (
    OptimiserAnalysisRefreshResponse,
)
from ...types import Response


def _get_kwargs(
    test_execution_id: str,
    *,
    body: EmptyRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/simulate/test-executions/{test_execution_id}/optimiser-analysis/refresh/".format(
            test_execution_id=quote(str(test_execution_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ApiTextErrorResponse | ManagementAPIErrorResponse | OptimiserAnalysisRefreshResponse
):
    if response.status_code == 200:
        response_200 = OptimiserAnalysisRefreshResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ApiTextErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 404:
        response_404 = ApiTextErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = ApiTextErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | OptimiserAnalysisRefreshResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    test_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: EmptyRequest,
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | OptimiserAnalysisRefreshResponse
]:
    """Trigger a new agent optimiser analysis run.

    Args:
        test_execution_id (str):
        body (EmptyRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | OptimiserAnalysisRefreshResponse]
    """

    kwargs = _get_kwargs(
        test_execution_id=test_execution_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    test_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: EmptyRequest,
) -> (
    ApiTextErrorResponse
    | ManagementAPIErrorResponse
    | OptimiserAnalysisRefreshResponse
    | None
):
    """Trigger a new agent optimiser analysis run.

    Args:
        test_execution_id (str):
        body (EmptyRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | OptimiserAnalysisRefreshResponse
    """

    return sync_detailed(
        test_execution_id=test_execution_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    test_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: EmptyRequest,
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | OptimiserAnalysisRefreshResponse
]:
    """Trigger a new agent optimiser analysis run.

    Args:
        test_execution_id (str):
        body (EmptyRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | OptimiserAnalysisRefreshResponse]
    """

    kwargs = _get_kwargs(
        test_execution_id=test_execution_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    test_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: EmptyRequest,
) -> (
    ApiTextErrorResponse
    | ManagementAPIErrorResponse
    | OptimiserAnalysisRefreshResponse
    | None
):
    """Trigger a new agent optimiser analysis run.

    Args:
        test_execution_id (str):
        body (EmptyRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | OptimiserAnalysisRefreshResponse
    """

    return (
        await asyncio_detailed(
            test_execution_id=test_execution_id,
            client=client,
            body=body,
        )
    ).parsed
