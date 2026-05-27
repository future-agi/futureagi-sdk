from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.call_branch_analysis_response import CallBranchAnalysisResponse
from ...models.error_response import ErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...types import Response


def _get_kwargs(
    call_execution_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/simulate/call-executions/{call_execution_id}/branch-analysis/".format(
            call_execution_id=quote(str(call_execution_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CallBranchAnalysisResponse | ErrorResponse | ManagementAPIErrorResponse:
    if response.status_code == 200:
        response_200 = CallBranchAnalysisResponse.from_dict(response.json())

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
) -> Response[CallBranchAnalysisResponse | ErrorResponse | ManagementAPIErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    call_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[CallBranchAnalysisResponse | ErrorResponse | ManagementAPIErrorResponse]:
    """Analyze a call execution against graph branches and identify deviations

    Args:
        call_execution_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CallBranchAnalysisResponse | ErrorResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        call_execution_id=call_execution_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    call_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> CallBranchAnalysisResponse | ErrorResponse | ManagementAPIErrorResponse | None:
    """Analyze a call execution against graph branches and identify deviations

    Args:
        call_execution_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CallBranchAnalysisResponse | ErrorResponse | ManagementAPIErrorResponse
    """

    return sync_detailed(
        call_execution_id=call_execution_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    call_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[CallBranchAnalysisResponse | ErrorResponse | ManagementAPIErrorResponse]:
    """Analyze a call execution against graph branches and identify deviations

    Args:
        call_execution_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CallBranchAnalysisResponse | ErrorResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        call_execution_id=call_execution_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    call_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> CallBranchAnalysisResponse | ErrorResponse | ManagementAPIErrorResponse | None:
    """Analyze a call execution against graph branches and identify deviations

    Args:
        call_execution_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CallBranchAnalysisResponse | ErrorResponse | ManagementAPIErrorResponse
    """

    return (
        await asyncio_detailed(
            call_execution_id=call_execution_id,
            client=client,
        )
    ).parsed
