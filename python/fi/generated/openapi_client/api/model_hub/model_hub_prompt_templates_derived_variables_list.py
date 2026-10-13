from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.model_hub_error_response import ModelHubErrorResponse
from ...models.prompt_derived_variables_response import PromptDerivedVariablesResponse
from ...types import Response


def _get_kwargs(
    prompt_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/model-hub/prompt-templates/{prompt_id}/derived-variables/".format(
            prompt_id=quote(str(prompt_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ManagementAPIErrorResponse | ModelHubErrorResponse | PromptDerivedVariablesResponse
):
    if response.status_code == 200:
        response_200 = PromptDerivedVariablesResponse.from_dict(response.json())

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
    ManagementAPIErrorResponse | ModelHubErrorResponse | PromptDerivedVariablesResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    prompt_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    ManagementAPIErrorResponse | ModelHubErrorResponse | PromptDerivedVariablesResponse
]:
    """Get all derived variables for a prompt template.

     Returns derived variables from JSON outputs across all versions.

    Query params:
        - version: Optional version filter
        - column_name: Optional column name filter

    Args:
        prompt_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ModelHubErrorResponse | PromptDerivedVariablesResponse]
    """

    kwargs = _get_kwargs(
        prompt_id=prompt_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    prompt_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    ManagementAPIErrorResponse
    | ModelHubErrorResponse
    | PromptDerivedVariablesResponse
    | None
):
    """Get all derived variables for a prompt template.

     Returns derived variables from JSON outputs across all versions.

    Query params:
        - version: Optional version filter
        - column_name: Optional column name filter

    Args:
        prompt_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ModelHubErrorResponse | PromptDerivedVariablesResponse
    """

    return sync_detailed(
        prompt_id=prompt_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    prompt_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    ManagementAPIErrorResponse | ModelHubErrorResponse | PromptDerivedVariablesResponse
]:
    """Get all derived variables for a prompt template.

     Returns derived variables from JSON outputs across all versions.

    Query params:
        - version: Optional version filter
        - column_name: Optional column name filter

    Args:
        prompt_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ModelHubErrorResponse | PromptDerivedVariablesResponse]
    """

    kwargs = _get_kwargs(
        prompt_id=prompt_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    prompt_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    ManagementAPIErrorResponse
    | ModelHubErrorResponse
    | PromptDerivedVariablesResponse
    | None
):
    """Get all derived variables for a prompt template.

     Returns derived variables from JSON outputs across all versions.

    Query params:
        - version: Optional version filter
        - column_name: Optional column name filter

    Args:
        prompt_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ModelHubErrorResponse | PromptDerivedVariablesResponse
    """

    return (
        await asyncio_detailed(
            prompt_id=prompt_id,
            client=client,
        )
    ).parsed
