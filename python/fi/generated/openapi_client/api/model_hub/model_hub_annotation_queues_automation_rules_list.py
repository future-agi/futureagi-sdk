from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.model_hub_annotation_queues_automation_rules_list_response_200 import (
    ModelHubAnnotationQueuesAutomationRulesListResponse200,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    queue_id: str,
    *,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["page"] = page

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/model-hub/annotation-queues/{queue_id}/automation-rules/".format(
            queue_id=quote(str(queue_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ManagementAPIErrorResponse | ModelHubAnnotationQueuesAutomationRulesListResponse200
):
    if response.status_code == 200:
        response_200 = ModelHubAnnotationQueuesAutomationRulesListResponse200.from_dict(
            response.json()
        )

        return response_200

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ManagementAPIErrorResponse | ModelHubAnnotationQueuesAutomationRulesListResponse200
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    queue_id: str,
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
) -> Response[
    ManagementAPIErrorResponse | ModelHubAnnotationQueuesAutomationRulesListResponse200
]:
    """
    Args:
        queue_id (str):
        page (int | Unset):
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ModelHubAnnotationQueuesAutomationRulesListResponse200]
    """

    kwargs = _get_kwargs(
        queue_id=queue_id,
        page=page,
        limit=limit,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    queue_id: str,
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
) -> (
    ManagementAPIErrorResponse
    | ModelHubAnnotationQueuesAutomationRulesListResponse200
    | None
):
    """
    Args:
        queue_id (str):
        page (int | Unset):
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ModelHubAnnotationQueuesAutomationRulesListResponse200
    """

    return sync_detailed(
        queue_id=queue_id,
        client=client,
        page=page,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    queue_id: str,
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
) -> Response[
    ManagementAPIErrorResponse | ModelHubAnnotationQueuesAutomationRulesListResponse200
]:
    """
    Args:
        queue_id (str):
        page (int | Unset):
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ModelHubAnnotationQueuesAutomationRulesListResponse200]
    """

    kwargs = _get_kwargs(
        queue_id=queue_id,
        page=page,
        limit=limit,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    queue_id: str,
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
) -> (
    ManagementAPIErrorResponse
    | ModelHubAnnotationQueuesAutomationRulesListResponse200
    | None
):
    """
    Args:
        queue_id (str):
        page (int | Unset):
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ModelHubAnnotationQueuesAutomationRulesListResponse200
    """

    return (
        await asyncio_detailed(
            queue_id=queue_id,
            client=client,
            page=page,
            limit=limit,
        )
    ).parsed
