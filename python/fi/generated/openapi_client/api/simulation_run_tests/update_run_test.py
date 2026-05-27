from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.run_test_error_response import RunTestErrorResponse
from ...models.run_test_response import RunTestResponse
from ...models.update_run_test import UpdateRunTest
from ...types import Response


def _get_kwargs(
    run_test_id: str,
    *,
    body: UpdateRunTest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/simulate/run-tests/{run_test_id}/".format(
            run_test_id=quote(str(run_test_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ManagementAPIErrorResponse | RunTestErrorResponse | RunTestResponse:
    if response.status_code == 200:
        response_200 = RunTestResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = RunTestErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 404:
        response_404 = RunTestErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = RunTestErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ManagementAPIErrorResponse | RunTestErrorResponse | RunTestResponse]:
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
    body: UpdateRunTest,
) -> Response[ManagementAPIErrorResponse | RunTestErrorResponse | RunTestResponse]:
    """Update a specific RunTest

    Args:
        run_test_id (str):
        body (UpdateRunTest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | RunTestErrorResponse | RunTestResponse]
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
    body: UpdateRunTest,
) -> ManagementAPIErrorResponse | RunTestErrorResponse | RunTestResponse | None:
    """Update a specific RunTest

    Args:
        run_test_id (str):
        body (UpdateRunTest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | RunTestErrorResponse | RunTestResponse
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
    body: UpdateRunTest,
) -> Response[ManagementAPIErrorResponse | RunTestErrorResponse | RunTestResponse]:
    """Update a specific RunTest

    Args:
        run_test_id (str):
        body (UpdateRunTest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | RunTestErrorResponse | RunTestResponse]
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
    body: UpdateRunTest,
) -> ManagementAPIErrorResponse | RunTestErrorResponse | RunTestResponse | None:
    """Update a specific RunTest

    Args:
        run_test_id (str):
        body (UpdateRunTest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | RunTestErrorResponse | RunTestResponse
    """

    return (
        await asyncio_detailed(
            run_test_id=run_test_id,
            client=client,
            body=body,
        )
    ).parsed
