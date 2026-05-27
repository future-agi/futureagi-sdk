from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.run_test_error_response import RunTestErrorResponse
from ...models.run_test_message_response import RunTestMessageResponse
from ...types import Response


def _get_kwargs(
    run_test_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/simulate/run-tests/{run_test_id}/".format(
            run_test_id=quote(str(run_test_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ManagementAPIErrorResponse | RunTestErrorResponse | RunTestMessageResponse:
    if response.status_code == 200:
        response_200 = RunTestMessageResponse.from_dict(response.json())

        return response_200

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
) -> Response[
    ManagementAPIErrorResponse | RunTestErrorResponse | RunTestMessageResponse
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
) -> Response[
    ManagementAPIErrorResponse | RunTestErrorResponse | RunTestMessageResponse
]:
    """Delete a specific RunTest (soft delete)

    Args:
        run_test_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | RunTestErrorResponse | RunTestMessageResponse]
    """

    kwargs = _get_kwargs(
        run_test_id=run_test_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    run_test_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> ManagementAPIErrorResponse | RunTestErrorResponse | RunTestMessageResponse | None:
    """Delete a specific RunTest (soft delete)

    Args:
        run_test_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | RunTestErrorResponse | RunTestMessageResponse
    """

    return sync_detailed(
        run_test_id=run_test_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    run_test_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    ManagementAPIErrorResponse | RunTestErrorResponse | RunTestMessageResponse
]:
    """Delete a specific RunTest (soft delete)

    Args:
        run_test_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | RunTestErrorResponse | RunTestMessageResponse]
    """

    kwargs = _get_kwargs(
        run_test_id=run_test_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    run_test_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> ManagementAPIErrorResponse | RunTestErrorResponse | RunTestMessageResponse | None:
    """Delete a specific RunTest (soft delete)

    Args:
        run_test_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | RunTestErrorResponse | RunTestMessageResponse
    """

    return (
        await asyncio_detailed(
            run_test_id=run_test_id,
            client=client,
        )
    ).parsed
