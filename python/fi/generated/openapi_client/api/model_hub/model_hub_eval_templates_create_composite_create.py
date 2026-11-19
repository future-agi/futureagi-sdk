from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.composite_eval_create_request import CompositeEvalCreateRequest
from ...models.composite_eval_create_response import CompositeEvalCreateResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.model_hub_error_response import ModelHubErrorResponse
from ...types import Response


def _get_kwargs(
    *,
    body: CompositeEvalCreateRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/model-hub/eval-templates/create-composite/",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CompositeEvalCreateResponse | ManagementAPIErrorResponse | ModelHubErrorResponse:
    if response.status_code == 200:
        response_200 = CompositeEvalCreateResponse.from_dict(response.json())

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
    CompositeEvalCreateResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
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
    body: CompositeEvalCreateRequest,
) -> Response[
    CompositeEvalCreateResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    """POST /model-hub/eval-templates/create-composite/

     Create a composite eval from a list of existing eval template IDs.

    Args:
        body (CompositeEvalCreateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CompositeEvalCreateResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
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
    body: CompositeEvalCreateRequest,
) -> (
    CompositeEvalCreateResponse
    | ManagementAPIErrorResponse
    | ModelHubErrorResponse
    | None
):
    """POST /model-hub/eval-templates/create-composite/

     Create a composite eval from a list of existing eval template IDs.

    Args:
        body (CompositeEvalCreateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CompositeEvalCreateResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CompositeEvalCreateRequest,
) -> Response[
    CompositeEvalCreateResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    """POST /model-hub/eval-templates/create-composite/

     Create a composite eval from a list of existing eval template IDs.

    Args:
        body (CompositeEvalCreateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CompositeEvalCreateResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CompositeEvalCreateRequest,
) -> (
    CompositeEvalCreateResponse
    | ManagementAPIErrorResponse
    | ModelHubErrorResponse
    | None
):
    """POST /model-hub/eval-templates/create-composite/

     Create a composite eval from a list of existing eval template IDs.

    Args:
        body (CompositeEvalCreateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CompositeEvalCreateResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
