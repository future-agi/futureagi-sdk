from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.create_run_test import CreateRunTest
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.run_test_error_response import RunTestErrorResponse
from ...models.run_test_response import RunTestResponse
from ...types import Response


def _get_kwargs(
    *,
    body: CreateRunTest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/simulate/run-tests/create/",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ManagementAPIErrorResponse | RunTestErrorResponse | RunTestResponse:
    if response.status_code == 201:
        response_201 = RunTestResponse.from_dict(response.json())

        return response_201

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
    *,
    client: AuthenticatedClient | Client,
    body: CreateRunTest,
) -> Response[ManagementAPIErrorResponse | RunTestErrorResponse | RunTestResponse]:
    """Create a new RunTest

    Args:
        body (CreateRunTest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | RunTestErrorResponse | RunTestResponse]
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
    body: CreateRunTest,
) -> ManagementAPIErrorResponse | RunTestErrorResponse | RunTestResponse | None:
    """Create a new RunTest

    Args:
        body (CreateRunTest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | RunTestErrorResponse | RunTestResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateRunTest,
) -> Response[ManagementAPIErrorResponse | RunTestErrorResponse | RunTestResponse]:
    """Create a new RunTest

    Args:
        body (CreateRunTest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | RunTestErrorResponse | RunTestResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateRunTest,
) -> ManagementAPIErrorResponse | RunTestErrorResponse | RunTestResponse | None:
    """Create a new RunTest

    Args:
        body (CreateRunTest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | RunTestErrorResponse | RunTestResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
