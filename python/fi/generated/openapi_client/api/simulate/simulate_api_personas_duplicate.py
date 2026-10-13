from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_error_with_details_response import ApiErrorWithDetailsResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.persona_duplicate_request import PersonaDuplicateRequest
from ...models.persona_duplicate_response import PersonaDuplicateResponse
from ...types import Response


def _get_kwargs(
    id: str,
    *,
    body: PersonaDuplicateRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/simulate/api/personas/{id}/duplicate/".format(
            id=quote(str(id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | PersonaDuplicateResponse
):
    if response.status_code == 201:
        response_201 = PersonaDuplicateResponse.from_dict(response.json())

        return response_201

    if response.status_code == 400:
        response_400 = ApiErrorWithDetailsResponse.from_dict(response.json())

        return response_400

    if response.status_code == 404:
        response_404 = ApiErrorWithDetailsResponse.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = ApiErrorWithDetailsResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | PersonaDuplicateResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PersonaDuplicateRequest,
) -> Response[
    ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | PersonaDuplicateResponse
]:
    """Duplicate a persona (creates a workspace-level copy)

    Args:
        id (str):
        body (PersonaDuplicateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | PersonaDuplicateResponse]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PersonaDuplicateRequest,
) -> (
    ApiErrorWithDetailsResponse
    | ManagementAPIErrorResponse
    | PersonaDuplicateResponse
    | None
):
    """Duplicate a persona (creates a workspace-level copy)

    Args:
        id (str):
        body (PersonaDuplicateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | PersonaDuplicateResponse
    """

    return sync_detailed(
        id=id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PersonaDuplicateRequest,
) -> Response[
    ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | PersonaDuplicateResponse
]:
    """Duplicate a persona (creates a workspace-level copy)

    Args:
        id (str):
        body (PersonaDuplicateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | PersonaDuplicateResponse]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PersonaDuplicateRequest,
) -> (
    ApiErrorWithDetailsResponse
    | ManagementAPIErrorResponse
    | PersonaDuplicateResponse
    | None
):
    """Duplicate a persona (creates a workspace-level copy)

    Args:
        id (str):
        body (PersonaDuplicateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | PersonaDuplicateResponse
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
        )
    ).parsed
