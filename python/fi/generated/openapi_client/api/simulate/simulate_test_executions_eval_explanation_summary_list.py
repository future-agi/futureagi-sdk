from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error_response import ErrorResponse
from ...models.eval_explanation_summary_response import EvalExplanationSummaryResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...types import Response


def _get_kwargs(
    test_execution_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/simulate/test-executions/{test_execution_id}/eval-explanation-summary/".format(
            test_execution_id=quote(str(test_execution_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | EvalExplanationSummaryResponse | ManagementAPIErrorResponse:
    if response.status_code == 200:
        response_200 = EvalExplanationSummaryResponse.from_dict(response.json())

        return response_200

    if response.status_code == 404:
        response_404 = ErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = ErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ErrorResponse | EvalExplanationSummaryResponse | ManagementAPIErrorResponse
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
    ErrorResponse | EvalExplanationSummaryResponse | ManagementAPIErrorResponse
]:
    """Fetch the evaluation explanation summary from the database.
    If not present, trigger async calculation and return empty response.

    Args:
        test_execution_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | EvalExplanationSummaryResponse | ManagementAPIErrorResponse]
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
) -> ErrorResponse | EvalExplanationSummaryResponse | ManagementAPIErrorResponse | None:
    """Fetch the evaluation explanation summary from the database.
    If not present, trigger async calculation and return empty response.

    Args:
        test_execution_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | EvalExplanationSummaryResponse | ManagementAPIErrorResponse
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
    ErrorResponse | EvalExplanationSummaryResponse | ManagementAPIErrorResponse
]:
    """Fetch the evaluation explanation summary from the database.
    If not present, trigger async calculation and return empty response.

    Args:
        test_execution_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | EvalExplanationSummaryResponse | ManagementAPIErrorResponse]
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
) -> ErrorResponse | EvalExplanationSummaryResponse | ManagementAPIErrorResponse | None:
    """Fetch the evaluation explanation summary from the database.
    If not present, trigger async calculation and return empty response.

    Args:
        test_execution_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | EvalExplanationSummaryResponse | ManagementAPIErrorResponse
    """

    return (
        await asyncio_detailed(
            test_execution_id=test_execution_id,
            client=client,
        )
    ).parsed
