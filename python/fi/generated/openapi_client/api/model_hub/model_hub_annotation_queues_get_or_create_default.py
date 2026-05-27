from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_text_error_response import ApiTextErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.queue_default_request import QueueDefaultRequest
from ...models.queue_default_response import QueueDefaultResponse
from ...types import Response


def _get_kwargs(
    *,
    body: QueueDefaultRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/model-hub/annotation-queues/get-or-create-default/",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | QueueDefaultResponse:
    if response.status_code == 200:
        response_200 = QueueDefaultResponse.from_dict(response.json())

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
) -> Response[ApiTextErrorResponse | ManagementAPIErrorResponse | QueueDefaultResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: QueueDefaultRequest,
) -> Response[ApiTextErrorResponse | ManagementAPIErrorResponse | QueueDefaultResponse]:
    """Get or create the default annotation queue for a project, dataset, or agent definition.
    Default queues are open to all org members (no annotator restriction).

    Body params (one of):
      - project_id
      - dataset_id
      - agent_definition_id

    Args:
        body (QueueDefaultRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | QueueDefaultResponse]
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
    body: QueueDefaultRequest,
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | QueueDefaultResponse | None:
    """Get or create the default annotation queue for a project, dataset, or agent definition.
    Default queues are open to all org members (no annotator restriction).

    Body params (one of):
      - project_id
      - dataset_id
      - agent_definition_id

    Args:
        body (QueueDefaultRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | QueueDefaultResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: QueueDefaultRequest,
) -> Response[ApiTextErrorResponse | ManagementAPIErrorResponse | QueueDefaultResponse]:
    """Get or create the default annotation queue for a project, dataset, or agent definition.
    Default queues are open to all org members (no annotator restriction).

    Body params (one of):
      - project_id
      - dataset_id
      - agent_definition_id

    Args:
        body (QueueDefaultRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | QueueDefaultResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: QueueDefaultRequest,
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | QueueDefaultResponse | None:
    """Get or create the default annotation queue for a project, dataset, or agent definition.
    Default queues are open to all org members (no annotator restriction).

    Body params (one of):
      - project_id
      - dataset_id
      - agent_definition_id

    Args:
        body (QueueDefaultRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | QueueDefaultResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
