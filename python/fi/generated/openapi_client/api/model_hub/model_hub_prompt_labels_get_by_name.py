from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.model_hub_prompt_labels_get_by_name_response_200 import (
    ModelHubPromptLabelsGetByNameResponse200,
)
from ...models.model_hub_text_error_response import ModelHubTextErrorResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
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
        "url": "/model-hub/prompt-labels/get-by-name/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ManagementAPIErrorResponse
    | ModelHubPromptLabelsGetByNameResponse200
    | ModelHubTextErrorResponse
):
    if response.status_code == 200:
        response_200 = ModelHubPromptLabelsGetByNameResponse200.from_dict(
            response.json()
        )

        return response_200

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
) -> Response[
    ManagementAPIErrorResponse
    | ModelHubPromptLabelsGetByNameResponse200
    | ModelHubTextErrorResponse
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
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
) -> Response[
    ManagementAPIErrorResponse
    | ModelHubPromptLabelsGetByNameResponse200
    | ModelHubTextErrorResponse
]:
    """Fetch a prompt version by template name and either explicit version or label.

     Query params:
      - name: template name (required)
      - version: version name like v1 (optional)
      - label: label name like Production/Staging/Development or custom (optional)

    Args:
        page (int | Unset):
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ModelHubPromptLabelsGetByNameResponse200 | ModelHubTextErrorResponse]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
) -> (
    ManagementAPIErrorResponse
    | ModelHubPromptLabelsGetByNameResponse200
    | ModelHubTextErrorResponse
    | None
):
    """Fetch a prompt version by template name and either explicit version or label.

     Query params:
      - name: template name (required)
      - version: version name like v1 (optional)
      - label: label name like Production/Staging/Development or custom (optional)

    Args:
        page (int | Unset):
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ModelHubPromptLabelsGetByNameResponse200 | ModelHubTextErrorResponse
    """

    return sync_detailed(
        client=client,
        page=page,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
) -> Response[
    ManagementAPIErrorResponse
    | ModelHubPromptLabelsGetByNameResponse200
    | ModelHubTextErrorResponse
]:
    """Fetch a prompt version by template name and either explicit version or label.

     Query params:
      - name: template name (required)
      - version: version name like v1 (optional)
      - label: label name like Production/Staging/Development or custom (optional)

    Args:
        page (int | Unset):
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ModelHubPromptLabelsGetByNameResponse200 | ModelHubTextErrorResponse]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
) -> (
    ManagementAPIErrorResponse
    | ModelHubPromptLabelsGetByNameResponse200
    | ModelHubTextErrorResponse
    | None
):
    """Fetch a prompt version by template name and either explicit version or label.

     Query params:
      - name: template name (required)
      - version: version name like v1 (optional)
      - label: label name like Production/Staging/Development or custom (optional)

    Args:
        page (int | Unset):
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ModelHubPromptLabelsGetByNameResponse200 | ModelHubTextErrorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            page=page,
            limit=limit,
        )
    ).parsed
