from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.model_hub_text_error_response import ModelHubTextErrorResponse
from ...models.prompt_label import PromptLabel
from ...types import Response


def _get_kwargs(
    *,
    body: PromptLabel,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/model-hub/prompt-labels/remove/",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ManagementAPIErrorResponse | ModelHubTextErrorResponse | PromptLabel:
    if response.status_code == 201:
        response_201 = PromptLabel.from_dict(response.json())

        return response_201

    if response.status_code == 400:
        response_400 = ModelHubTextErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 403:
        response_403 = ModelHubTextErrorResponse.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = ModelHubTextErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 409:
        response_409 = ModelHubTextErrorResponse.from_dict(response.json())

        return response_409

    if response.status_code == 500:
        response_500 = ModelHubTextErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ManagementAPIErrorResponse | ModelHubTextErrorResponse | PromptLabel]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PromptLabel,
) -> Response[ManagementAPIErrorResponse | ModelHubTextErrorResponse | PromptLabel]:
    """Detach label from a prompt version.

    Args:
        body (PromptLabel):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ModelHubTextErrorResponse | PromptLabel]
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
    body: PromptLabel,
) -> ManagementAPIErrorResponse | ModelHubTextErrorResponse | PromptLabel | None:
    """Detach label from a prompt version.

    Args:
        body (PromptLabel):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ModelHubTextErrorResponse | PromptLabel
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PromptLabel,
) -> Response[ManagementAPIErrorResponse | ModelHubTextErrorResponse | PromptLabel]:
    """Detach label from a prompt version.

    Args:
        body (PromptLabel):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ModelHubTextErrorResponse | PromptLabel]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: PromptLabel,
) -> ManagementAPIErrorResponse | ModelHubTextErrorResponse | PromptLabel | None:
    """Detach label from a prompt version.

    Args:
        body (PromptLabel):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ModelHubTextErrorResponse | PromptLabel
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
