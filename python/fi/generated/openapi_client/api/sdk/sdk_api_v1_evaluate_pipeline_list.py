from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.sdk_error_response import SDKErrorResponse
from ...models.sdkcicd_evaluation_runs_response import SDKCICDEvaluationRunsResponse
from ...types import UNSET, Response


def _get_kwargs(
    *,
    project_name: str,
    versions: str,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["project_name"] = project_name

    params["versions"] = versions

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/sdk/api/v1/evaluate-pipeline/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ManagementAPIErrorResponse | SDKCICDEvaluationRunsResponse | SDKErrorResponse:
    if response.status_code == 200:
        response_200 = SDKCICDEvaluationRunsResponse.from_dict(response.json())

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
    ManagementAPIErrorResponse | SDKCICDEvaluationRunsResponse | SDKErrorResponse
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
    project_name: str,
    versions: str,
) -> Response[
    ManagementAPIErrorResponse | SDKCICDEvaluationRunsResponse | SDKErrorResponse
]:
    """
    Args:
        project_name (str):
        versions (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | SDKCICDEvaluationRunsResponse | SDKErrorResponse]
    """

    kwargs = _get_kwargs(
        project_name=project_name,
        versions=versions,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    project_name: str,
    versions: str,
) -> (
    ManagementAPIErrorResponse | SDKCICDEvaluationRunsResponse | SDKErrorResponse | None
):
    """
    Args:
        project_name (str):
        versions (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | SDKCICDEvaluationRunsResponse | SDKErrorResponse
    """

    return sync_detailed(
        client=client,
        project_name=project_name,
        versions=versions,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    project_name: str,
    versions: str,
) -> Response[
    ManagementAPIErrorResponse | SDKCICDEvaluationRunsResponse | SDKErrorResponse
]:
    """
    Args:
        project_name (str):
        versions (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | SDKCICDEvaluationRunsResponse | SDKErrorResponse]
    """

    kwargs = _get_kwargs(
        project_name=project_name,
        versions=versions,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    project_name: str,
    versions: str,
) -> (
    ManagementAPIErrorResponse | SDKCICDEvaluationRunsResponse | SDKErrorResponse | None
):
    """
    Args:
        project_name (str):
        versions (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | SDKCICDEvaluationRunsResponse | SDKErrorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            project_name=project_name,
            versions=versions,
        )
    ).parsed
