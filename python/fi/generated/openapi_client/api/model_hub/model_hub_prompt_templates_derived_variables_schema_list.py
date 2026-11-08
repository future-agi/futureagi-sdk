from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.derived_variable_detail_response import DerivedVariableDetailResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.model_hub_error_response import ModelHubErrorResponse
from ...types import Response


def _get_kwargs(
    prompt_id: str,
    column_name: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/model-hub/prompt-templates/{prompt_id}/derived-variables/{column_name}/schema/".format(
            prompt_id=quote(str(prompt_id), safe=""),
            column_name=quote(str(column_name), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DerivedVariableDetailResponse | ManagementAPIErrorResponse | ModelHubErrorResponse:
    if response.status_code == 200:
        response_200 = DerivedVariableDetailResponse.from_dict(response.json())

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
    DerivedVariableDetailResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    prompt_id: str,
    column_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    DerivedVariableDetailResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    """Get the schema for derived variables of a specific column.

     Returns detailed schema information including types and sample values.

    Path params:
        - prompt_id: UUID of the prompt template
        - column_name: Name of the column

    Query params:
        - version: Optional version filter

    Args:
        prompt_id (str):
        column_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DerivedVariableDetailResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        prompt_id=prompt_id,
        column_name=column_name,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    prompt_id: str,
    column_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    DerivedVariableDetailResponse
    | ManagementAPIErrorResponse
    | ModelHubErrorResponse
    | None
):
    """Get the schema for derived variables of a specific column.

     Returns detailed schema information including types and sample values.

    Path params:
        - prompt_id: UUID of the prompt template
        - column_name: Name of the column

    Query params:
        - version: Optional version filter

    Args:
        prompt_id (str):
        column_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DerivedVariableDetailResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return sync_detailed(
        prompt_id=prompt_id,
        column_name=column_name,
        client=client,
    ).parsed


async def asyncio_detailed(
    prompt_id: str,
    column_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    DerivedVariableDetailResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    """Get the schema for derived variables of a specific column.

     Returns detailed schema information including types and sample values.

    Path params:
        - prompt_id: UUID of the prompt template
        - column_name: Name of the column

    Query params:
        - version: Optional version filter

    Args:
        prompt_id (str):
        column_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DerivedVariableDetailResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        prompt_id=prompt_id,
        column_name=column_name,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    prompt_id: str,
    column_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    DerivedVariableDetailResponse
    | ManagementAPIErrorResponse
    | ModelHubErrorResponse
    | None
):
    """Get the schema for derived variables of a specific column.

     Returns detailed schema information including types and sample values.

    Path params:
        - prompt_id: UUID of the prompt template
        - column_name: Name of the column

    Query params:
        - version: Optional version filter

    Args:
        prompt_id (str):
        column_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DerivedVariableDetailResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return (
        await asyncio_detailed(
            prompt_id=prompt_id,
            column_name=column_name,
            client=client,
        )
    ).parsed
