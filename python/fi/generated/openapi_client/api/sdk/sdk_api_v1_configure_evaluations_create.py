from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.sdk_configure_evaluations_request import SDKConfigureEvaluationsRequest
from ...models.sdk_configure_evaluations_response import SDKConfigureEvaluationsResponse
from ...models.sdk_error_response import SDKErrorResponse
from ...types import Response


def _get_kwargs(
    *,
    body: SDKConfigureEvaluationsRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/sdk/api/v1/configure-evaluations/",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ManagementAPIErrorResponse | SDKConfigureEvaluationsResponse | SDKErrorResponse:
    if response.status_code == 200:
        response_200 = SDKConfigureEvaluationsResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = SDKErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 500:
        response_500 = SDKErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ManagementAPIErrorResponse | SDKConfigureEvaluationsResponse | SDKErrorResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: SDKConfigureEvaluationsRequest,
) -> Response[
    ManagementAPIErrorResponse | SDKConfigureEvaluationsResponse | SDKErrorResponse
]:
    """
    Args:
        body (SDKConfigureEvaluationsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | SDKConfigureEvaluationsResponse | SDKErrorResponse]
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
    body: SDKConfigureEvaluationsRequest,
) -> (
    ManagementAPIErrorResponse
    | SDKConfigureEvaluationsResponse
    | SDKErrorResponse
    | None
):
    """
    Args:
        body (SDKConfigureEvaluationsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | SDKConfigureEvaluationsResponse | SDKErrorResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: SDKConfigureEvaluationsRequest,
) -> Response[
    ManagementAPIErrorResponse | SDKConfigureEvaluationsResponse | SDKErrorResponse
]:
    """
    Args:
        body (SDKConfigureEvaluationsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | SDKConfigureEvaluationsResponse | SDKErrorResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: SDKConfigureEvaluationsRequest,
) -> (
    ManagementAPIErrorResponse
    | SDKConfigureEvaluationsResponse
    | SDKErrorResponse
    | None
):
    """
    Args:
        body (SDKConfigureEvaluationsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | SDKConfigureEvaluationsResponse | SDKErrorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
