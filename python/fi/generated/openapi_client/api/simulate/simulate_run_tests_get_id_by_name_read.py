from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_text_error_response import ApiTextErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.run_test_name_response import RunTestNameResponse
from ...types import Response


def _get_kwargs(
    run_test_name: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/simulate/run-tests/get-id-by-name/{run_test_name}/".format(
            run_test_name=quote(str(run_test_name), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | RunTestNameResponse:
    if response.status_code == 200:
        response_200 = RunTestNameResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ApiTextErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 500:
        response_500 = ApiTextErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ApiTextErrorResponse | ManagementAPIErrorResponse | RunTestNameResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    run_test_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[ApiTextErrorResponse | ManagementAPIErrorResponse | RunTestNameResponse]:
    """API View to get the id of a run test by name

    Args:
        run_test_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | RunTestNameResponse]
    """

    kwargs = _get_kwargs(
        run_test_name=run_test_name,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    run_test_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | RunTestNameResponse | None:
    """API View to get the id of a run test by name

    Args:
        run_test_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | RunTestNameResponse
    """

    return sync_detailed(
        run_test_name=run_test_name,
        client=client,
    ).parsed


async def asyncio_detailed(
    run_test_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[ApiTextErrorResponse | ManagementAPIErrorResponse | RunTestNameResponse]:
    """API View to get the id of a run test by name

    Args:
        run_test_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | RunTestNameResponse]
    """

    kwargs = _get_kwargs(
        run_test_name=run_test_name,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    run_test_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | RunTestNameResponse | None:
    """API View to get the id of a run test by name

    Args:
        run_test_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | RunTestNameResponse
    """

    return (
        await asyncio_detailed(
            run_test_name=run_test_name,
            client=client,
        )
    ).parsed
