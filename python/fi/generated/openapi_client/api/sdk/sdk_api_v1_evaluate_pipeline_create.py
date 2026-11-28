from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.cicd_job import CICDJob
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.sdk_error_response import SDKErrorResponse
from ...models.sdkcicd_evaluation_run_accepted_response import (
    SDKCICDEvaluationRunAcceptedResponse,
)
from ...types import Response


def _get_kwargs(
    *,
    body: CICDJob,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/sdk/api/v1/evaluate-pipeline/",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ManagementAPIErrorResponse | SDKCICDEvaluationRunAcceptedResponse | SDKErrorResponse
):
    if response.status_code == 200:
        response_200 = SDKCICDEvaluationRunAcceptedResponse.from_dict(response.json())

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
    ManagementAPIErrorResponse | SDKCICDEvaluationRunAcceptedResponse | SDKErrorResponse
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
    body: CICDJob,
) -> Response[
    ManagementAPIErrorResponse | SDKCICDEvaluationRunAcceptedResponse | SDKErrorResponse
]:
    """
    Args:
        body (CICDJob):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | SDKCICDEvaluationRunAcceptedResponse | SDKErrorResponse]
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
    body: CICDJob,
) -> (
    ManagementAPIErrorResponse
    | SDKCICDEvaluationRunAcceptedResponse
    | SDKErrorResponse
    | None
):
    """
    Args:
        body (CICDJob):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | SDKCICDEvaluationRunAcceptedResponse | SDKErrorResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CICDJob,
) -> Response[
    ManagementAPIErrorResponse | SDKCICDEvaluationRunAcceptedResponse | SDKErrorResponse
]:
    """
    Args:
        body (CICDJob):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | SDKCICDEvaluationRunAcceptedResponse | SDKErrorResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CICDJob,
) -> (
    ManagementAPIErrorResponse
    | SDKCICDEvaluationRunAcceptedResponse
    | SDKErrorResponse
    | None
):
    """
    Args:
        body (CICDJob):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | SDKCICDEvaluationRunAcceptedResponse | SDKErrorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
