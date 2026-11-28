from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.model_hub_error_response import ModelHubErrorResponse
from ...models.prompt_run_status_response import PromptRunStatusResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    id: UUID,
    *,
    template_version: str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["template_version"] = template_version

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/model-hub/prompt-templates/{id}/get-run-status/".format(
            id=quote(str(id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ManagementAPIErrorResponse | ModelHubErrorResponse | PromptRunStatusResponse:
    if response.status_code == 200:
        response_200 = PromptRunStatusResponse.from_dict(response.json())

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
    ManagementAPIErrorResponse | ModelHubErrorResponse | PromptRunStatusResponse
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
    template_version: str | Unset = UNSET,
) -> Response[
    ManagementAPIErrorResponse | ModelHubErrorResponse | PromptRunStatusResponse
]:
    """Get the current status and results of a template run

    Args:
        id (UUID):
        template_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ModelHubErrorResponse | PromptRunStatusResponse]
    """

    kwargs = _get_kwargs(
        id=id,
        template_version=template_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    template_version: str | Unset = UNSET,
) -> (
    ManagementAPIErrorResponse | ModelHubErrorResponse | PromptRunStatusResponse | None
):
    """Get the current status and results of a template run

    Args:
        id (UUID):
        template_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ModelHubErrorResponse | PromptRunStatusResponse
    """

    return sync_detailed(
        id=id,
        client=client,
        template_version=template_version,
    ).parsed


async def asyncio_detailed(
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    template_version: str | Unset = UNSET,
) -> Response[
    ManagementAPIErrorResponse | ModelHubErrorResponse | PromptRunStatusResponse
]:
    """Get the current status and results of a template run

    Args:
        id (UUID):
        template_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ModelHubErrorResponse | PromptRunStatusResponse]
    """

    kwargs = _get_kwargs(
        id=id,
        template_version=template_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    template_version: str | Unset = UNSET,
) -> (
    ManagementAPIErrorResponse | ModelHubErrorResponse | PromptRunStatusResponse | None
):
    """Get the current status and results of a template run

    Args:
        id (UUID):
        template_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ModelHubErrorResponse | PromptRunStatusResponse
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            template_version=template_version,
        )
    ).parsed
