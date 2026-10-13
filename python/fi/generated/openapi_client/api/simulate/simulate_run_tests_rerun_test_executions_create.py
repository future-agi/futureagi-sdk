from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_text_error_response import ApiTextErrorResponse
from ...models.error_response import ErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.test_execution_rerun import TestExecutionRerun
from ...models.test_execution_rerun_response import TestExecutionRerunResponse
from ...types import Response


def _get_kwargs(
    run_test_id: str,
    *,
    body: TestExecutionRerun,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/simulate/run-tests/{run_test_id}/rerun-test-executions/".format(
            run_test_id=quote(str(run_test_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ApiTextErrorResponse
    | ErrorResponse
    | ManagementAPIErrorResponse
    | TestExecutionRerunResponse
):
    if response.status_code == 200:
        response_200 = TestExecutionRerunResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ApiTextErrorResponse.from_dict(response.json())

        return response_400

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
    ApiTextErrorResponse
    | ErrorResponse
    | ManagementAPIErrorResponse
    | TestExecutionRerunResponse
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
    body: TestExecutionRerun,
) -> Response[
    ApiTextErrorResponse
    | ErrorResponse
    | ManagementAPIErrorResponse
    | TestExecutionRerunResponse
]:
    """Rerun multiple test executions (either evaluation only or call + evaluation).
    All call executions within each test execution are rerun.

    Args:
        run_test_id (str):
        body (TestExecutionRerun):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ErrorResponse | ManagementAPIErrorResponse | TestExecutionRerunResponse]
    """

    kwargs = _get_kwargs(
        run_test_id=run_test_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    run_test_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: TestExecutionRerun,
) -> (
    ApiTextErrorResponse
    | ErrorResponse
    | ManagementAPIErrorResponse
    | TestExecutionRerunResponse
    | None
):
    """Rerun multiple test executions (either evaluation only or call + evaluation).
    All call executions within each test execution are rerun.

    Args:
        run_test_id (str):
        body (TestExecutionRerun):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ErrorResponse | ManagementAPIErrorResponse | TestExecutionRerunResponse
    """

    return sync_detailed(
        run_test_id=run_test_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    run_test_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: TestExecutionRerun,
) -> Response[
    ApiTextErrorResponse
    | ErrorResponse
    | ManagementAPIErrorResponse
    | TestExecutionRerunResponse
]:
    """Rerun multiple test executions (either evaluation only or call + evaluation).
    All call executions within each test execution are rerun.

    Args:
        run_test_id (str):
        body (TestExecutionRerun):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ErrorResponse | ManagementAPIErrorResponse | TestExecutionRerunResponse]
    """

    kwargs = _get_kwargs(
        run_test_id=run_test_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    run_test_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: TestExecutionRerun,
) -> (
    ApiTextErrorResponse
    | ErrorResponse
    | ManagementAPIErrorResponse
    | TestExecutionRerunResponse
    | None
):
    """Rerun multiple test executions (either evaluation only or call + evaluation).
    All call executions within each test execution are rerun.

    Args:
        run_test_id (str):
        body (TestExecutionRerun):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ErrorResponse | ManagementAPIErrorResponse | TestExecutionRerunResponse
    """

    return (
        await asyncio_detailed(
            run_test_id=run_test_id,
            client=client,
            body=body,
        )
    ).parsed
