from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.eval_error_response import EvalErrorResponse
from ...models.eval_summary_response import EvalSummaryResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    run_test_id: str,
    *,
    execution_id: UUID | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_execution_id: str | Unset = UNSET
    if not isinstance(execution_id, Unset):
        json_execution_id = str(execution_id)
    params["execution_id"] = json_execution_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/simulate/run-tests/{run_test_id}/eval-summary/".format(
            run_test_id=quote(str(run_test_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | EvalErrorResponse | EvalSummaryResponse | ManagementAPIErrorResponse:
    if response.status_code == 200:
        response_200 = EvalSummaryResponse.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = cast(Any, None)
        return response_401

    if response.status_code == 404:
        response_404 = EvalErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = EvalErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    Any | EvalErrorResponse | EvalSummaryResponse | ManagementAPIErrorResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    run_test_id: str,
    *,
    client: AuthenticatedClient | Client,
    execution_id: UUID | Unset = UNSET,
) -> Response[
    Any | EvalErrorResponse | EvalSummaryResponse | ManagementAPIErrorResponse
]:
    """Get evaluation summary

     Returns evaluation summary statistics for a test run, optionally scoped to a single execution.

    Args:
        run_test_id (str):
        execution_id (UUID | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | EvalErrorResponse | EvalSummaryResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        run_test_id=run_test_id,
        execution_id=execution_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    run_test_id: str,
    *,
    client: AuthenticatedClient | Client,
    execution_id: UUID | Unset = UNSET,
) -> Any | EvalErrorResponse | EvalSummaryResponse | ManagementAPIErrorResponse | None:
    """Get evaluation summary

     Returns evaluation summary statistics for a test run, optionally scoped to a single execution.

    Args:
        run_test_id (str):
        execution_id (UUID | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | EvalErrorResponse | EvalSummaryResponse | ManagementAPIErrorResponse
    """

    return sync_detailed(
        run_test_id=run_test_id,
        client=client,
        execution_id=execution_id,
    ).parsed


async def asyncio_detailed(
    run_test_id: str,
    *,
    client: AuthenticatedClient | Client,
    execution_id: UUID | Unset = UNSET,
) -> Response[
    Any | EvalErrorResponse | EvalSummaryResponse | ManagementAPIErrorResponse
]:
    """Get evaluation summary

     Returns evaluation summary statistics for a test run, optionally scoped to a single execution.

    Args:
        run_test_id (str):
        execution_id (UUID | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | EvalErrorResponse | EvalSummaryResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        run_test_id=run_test_id,
        execution_id=execution_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    run_test_id: str,
    *,
    client: AuthenticatedClient | Client,
    execution_id: UUID | Unset = UNSET,
) -> Any | EvalErrorResponse | EvalSummaryResponse | ManagementAPIErrorResponse | None:
    """Get evaluation summary

     Returns evaluation summary statistics for a test run, optionally scoped to a single execution.

    Args:
        run_test_id (str):
        execution_id (UUID | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | EvalErrorResponse | EvalSummaryResponse | ManagementAPIErrorResponse
    """

    return (
        await asyncio_detailed(
            run_test_id=run_test_id,
            client=client,
            execution_id=execution_id,
        )
    ).parsed
