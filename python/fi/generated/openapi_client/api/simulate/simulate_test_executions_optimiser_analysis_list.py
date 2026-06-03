from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_text_error_response import ApiTextErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.optimiser_analysis_response import OptimiserAnalysisResponse
from ...types import Response


def _get_kwargs(
    test_execution_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/simulate/test-executions/{test_execution_id}/optimiser-analysis/".format(
            test_execution_id=quote(str(test_execution_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | OptimiserAnalysisResponse:
    if response.status_code == 200:
        response_200 = OptimiserAnalysisResponse.from_dict(response.json())

        return response_200

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
    ApiTextErrorResponse | ManagementAPIErrorResponse | OptimiserAnalysisResponse
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
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | OptimiserAnalysisResponse
]:
    """Fetch the agent optimiser analysis for a test execution.
    If not present or pending, returns status information.

    Args:
        test_execution_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | OptimiserAnalysisResponse]
    """

    kwargs = _get_kwargs(
        test_execution_id=test_execution_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    test_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    ApiTextErrorResponse | ManagementAPIErrorResponse | OptimiserAnalysisResponse | None
):
    """Fetch the agent optimiser analysis for a test execution.
    If not present or pending, returns status information.

    Args:
        test_execution_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | OptimiserAnalysisResponse
    """

    return sync_detailed(
        test_execution_id=test_execution_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    test_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | OptimiserAnalysisResponse
]:
    """Fetch the agent optimiser analysis for a test execution.
    If not present or pending, returns status information.

    Args:
        test_execution_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | OptimiserAnalysisResponse]
    """

    kwargs = _get_kwargs(
        test_execution_id=test_execution_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    test_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    ApiTextErrorResponse | ManagementAPIErrorResponse | OptimiserAnalysisResponse | None
):
    """Fetch the agent optimiser analysis for a test execution.
    If not present or pending, returns status information.

    Args:
        test_execution_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | OptimiserAnalysisResponse
    """

    return (
        await asyncio_detailed(
            test_execution_id=test_execution_id,
            client=client,
        )
    ).parsed
