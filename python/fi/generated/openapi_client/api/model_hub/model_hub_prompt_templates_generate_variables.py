from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.prompt_template import PromptTemplate
from ...types import Response


def _get_kwargs(
    *,
    body: PromptTemplate,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/model-hub/prompt-templates/generate-variables/",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ManagementAPIErrorResponse | PromptTemplate:
    if response.status_code == 201:
        response_201 = PromptTemplate.from_dict(response.json())

        return response_201

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ManagementAPIErrorResponse | PromptTemplate]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PromptTemplate,
) -> Response[ManagementAPIErrorResponse | PromptTemplate]:
    r"""Generate synthetic data for prompt variables using the SyntheticDataAgent.

     Expected payload:
    {
        \"prompt_name\": \"string\",
        \"prompt_instructions\": \"list/array\" ,
        \"variable_names\": [\"string\"],
        \"variable_count\": \"int\",
        \"generation_type\": \"prompt\"
    }

    Args:
        body (PromptTemplate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | PromptTemplate]
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
    body: PromptTemplate,
) -> ManagementAPIErrorResponse | PromptTemplate | None:
    r"""Generate synthetic data for prompt variables using the SyntheticDataAgent.

     Expected payload:
    {
        \"prompt_name\": \"string\",
        \"prompt_instructions\": \"list/array\" ,
        \"variable_names\": [\"string\"],
        \"variable_count\": \"int\",
        \"generation_type\": \"prompt\"
    }

    Args:
        body (PromptTemplate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | PromptTemplate
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PromptTemplate,
) -> Response[ManagementAPIErrorResponse | PromptTemplate]:
    r"""Generate synthetic data for prompt variables using the SyntheticDataAgent.

     Expected payload:
    {
        \"prompt_name\": \"string\",
        \"prompt_instructions\": \"list/array\" ,
        \"variable_names\": [\"string\"],
        \"variable_count\": \"int\",
        \"generation_type\": \"prompt\"
    }

    Args:
        body (PromptTemplate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | PromptTemplate]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: PromptTemplate,
) -> ManagementAPIErrorResponse | PromptTemplate | None:
    r"""Generate synthetic data for prompt variables using the SyntheticDataAgent.

     Expected payload:
    {
        \"prompt_name\": \"string\",
        \"prompt_instructions\": \"list/array\" ,
        \"variable_names\": [\"string\"],
        \"variable_count\": \"int\",
        \"generation_type\": \"prompt\"
    }

    Args:
        body (PromptTemplate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | PromptTemplate
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
