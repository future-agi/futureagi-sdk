from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.model_hub_error_response import ModelHubErrorResponse
from ...models.preview_dataset_operation_request import PreviewDatasetOperationRequest
from ...models.preview_dataset_operation_response import PreviewDatasetOperationResponse
from ...types import Response


def _get_kwargs(
    dataset_id: str,
    operation_type: str,
    *,
    body: PreviewDatasetOperationRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/model-hub/datasets/{dataset_id}/preview/{operation_type}/".format(
            dataset_id=quote(str(dataset_id), safe=""),
            operation_type=quote(str(operation_type), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ManagementAPIErrorResponse | ModelHubErrorResponse | PreviewDatasetOperationResponse
):
    if response.status_code == 200:
        response_200 = PreviewDatasetOperationResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ModelHubErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 403:
        response_403 = ModelHubErrorResponse.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = ModelHubErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 409:
        response_409 = ModelHubErrorResponse.from_dict(response.json())

        return response_409

    if response.status_code == 500:
        response_500 = ModelHubErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ManagementAPIErrorResponse | ModelHubErrorResponse | PreviewDatasetOperationResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    dataset_id: str,
    operation_type: str,
    *,
    client: AuthenticatedClient | Client,
    body: PreviewDatasetOperationRequest,
) -> Response[
    ManagementAPIErrorResponse | ModelHubErrorResponse | PreviewDatasetOperationResponse
]:
    """
    Args:
        dataset_id (str):
        operation_type (str):
        body (PreviewDatasetOperationRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ModelHubErrorResponse | PreviewDatasetOperationResponse]
    """

    kwargs = _get_kwargs(
        dataset_id=dataset_id,
        operation_type=operation_type,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    dataset_id: str,
    operation_type: str,
    *,
    client: AuthenticatedClient | Client,
    body: PreviewDatasetOperationRequest,
) -> (
    ManagementAPIErrorResponse
    | ModelHubErrorResponse
    | PreviewDatasetOperationResponse
    | None
):
    """
    Args:
        dataset_id (str):
        operation_type (str):
        body (PreviewDatasetOperationRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ModelHubErrorResponse | PreviewDatasetOperationResponse
    """

    return sync_detailed(
        dataset_id=dataset_id,
        operation_type=operation_type,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    dataset_id: str,
    operation_type: str,
    *,
    client: AuthenticatedClient | Client,
    body: PreviewDatasetOperationRequest,
) -> Response[
    ManagementAPIErrorResponse | ModelHubErrorResponse | PreviewDatasetOperationResponse
]:
    """
    Args:
        dataset_id (str):
        operation_type (str):
        body (PreviewDatasetOperationRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ModelHubErrorResponse | PreviewDatasetOperationResponse]
    """

    kwargs = _get_kwargs(
        dataset_id=dataset_id,
        operation_type=operation_type,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    dataset_id: str,
    operation_type: str,
    *,
    client: AuthenticatedClient | Client,
    body: PreviewDatasetOperationRequest,
) -> (
    ManagementAPIErrorResponse
    | ModelHubErrorResponse
    | PreviewDatasetOperationResponse
    | None
):
    """
    Args:
        dataset_id (str):
        operation_type (str):
        body (PreviewDatasetOperationRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ModelHubErrorResponse | PreviewDatasetOperationResponse
    """

    return (
        await asyncio_detailed(
            dataset_id=dataset_id,
            operation_type=operation_type,
            client=client,
            body=body,
        )
    ).parsed
