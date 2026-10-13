from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_text_error_response import ApiTextErrorResponse
from ...models.export_annotation_queue_export_format import (
    ExportAnnotationQueueExportFormat,
)
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.queue_export_annotations_response import QueueExportAnnotationsResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    id: UUID,
    *,
    export_format: ExportAnnotationQueueExportFormat | Unset = UNSET,
    status: str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_export_format: str | Unset = UNSET
    if not isinstance(export_format, Unset):
        json_export_format = export_format.value

    params["export_format"] = json_export_format

    params["status"] = status

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/model-hub/annotation-queues/{id}/export/".format(
            id=quote(str(id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | QueueExportAnnotationsResponse:
    if response.status_code == 200:
        response_200 = QueueExportAnnotationsResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ApiTextErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 403:
        response_403 = ApiTextErrorResponse.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = ApiTextErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 409:
        response_409 = ApiTextErrorResponse.from_dict(response.json())

        return response_409

    if response.status_code == 500:
        response_500 = ApiTextErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | QueueExportAnnotationsResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    export_format: ExportAnnotationQueueExportFormat | Unset = UNSET,
    status: str | Unset = UNSET,
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | QueueExportAnnotationsResponse
]:
    """Export all items with their annotations.

    Args:
        id (UUID):
        export_format (ExportAnnotationQueueExportFormat | Unset):
        status (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | QueueExportAnnotationsResponse]
    """

    kwargs = _get_kwargs(
        id=id,
        export_format=export_format,
        status=status,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    export_format: ExportAnnotationQueueExportFormat | Unset = UNSET,
    status: str | Unset = UNSET,
) -> (
    ApiTextErrorResponse
    | ManagementAPIErrorResponse
    | QueueExportAnnotationsResponse
    | None
):
    """Export all items with their annotations.

    Args:
        id (UUID):
        export_format (ExportAnnotationQueueExportFormat | Unset):
        status (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | QueueExportAnnotationsResponse
    """

    return sync_detailed(
        id=id,
        client=client,
        export_format=export_format,
        status=status,
    ).parsed


async def asyncio_detailed(
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    export_format: ExportAnnotationQueueExportFormat | Unset = UNSET,
    status: str | Unset = UNSET,
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | QueueExportAnnotationsResponse
]:
    """Export all items with their annotations.

    Args:
        id (UUID):
        export_format (ExportAnnotationQueueExportFormat | Unset):
        status (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | QueueExportAnnotationsResponse]
    """

    kwargs = _get_kwargs(
        id=id,
        export_format=export_format,
        status=status,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    export_format: ExportAnnotationQueueExportFormat | Unset = UNSET,
    status: str | Unset = UNSET,
) -> (
    ApiTextErrorResponse
    | ManagementAPIErrorResponse
    | QueueExportAnnotationsResponse
    | None
):
    """Export all items with their annotations.

    Args:
        id (UUID):
        export_format (ExportAnnotationQueueExportFormat | Unset):
        status (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | QueueExportAnnotationsResponse
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            export_format=export_format,
            status=status,
        )
    ).parsed
