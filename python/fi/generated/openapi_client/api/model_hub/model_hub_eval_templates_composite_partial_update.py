from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.composite_eval_detail_response import CompositeEvalDetailResponse
from ...models.composite_eval_update_request import CompositeEvalUpdateRequest
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.model_hub_error_response import ModelHubErrorResponse
from ...types import Response


def _get_kwargs(
    template_id: str,
    *,
    body: CompositeEvalUpdateRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/model-hub/eval-templates/{template_id}/composite/".format(
            template_id=quote(str(template_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CompositeEvalDetailResponse | ManagementAPIErrorResponse | ModelHubErrorResponse:
    if response.status_code == 200:
        response_200 = CompositeEvalDetailResponse.from_dict(response.json())

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
    CompositeEvalDetailResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    template_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: CompositeEvalUpdateRequest,
) -> Response[
    CompositeEvalDetailResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    """PATCH — partial update of a composite eval.

     Supported fields (all optional):
      name, description, tags,
      aggregation_enabled, aggregation_function,
      child_template_ids (replaces the child list),
      child_weights (map of child_id -> weight).

    Args:
        template_id (str):
        body (CompositeEvalUpdateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CompositeEvalDetailResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        template_id=template_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    template_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: CompositeEvalUpdateRequest,
) -> (
    CompositeEvalDetailResponse
    | ManagementAPIErrorResponse
    | ModelHubErrorResponse
    | None
):
    """PATCH — partial update of a composite eval.

     Supported fields (all optional):
      name, description, tags,
      aggregation_enabled, aggregation_function,
      child_template_ids (replaces the child list),
      child_weights (map of child_id -> weight).

    Args:
        template_id (str):
        body (CompositeEvalUpdateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CompositeEvalDetailResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return sync_detailed(
        template_id=template_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    template_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: CompositeEvalUpdateRequest,
) -> Response[
    CompositeEvalDetailResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    """PATCH — partial update of a composite eval.

     Supported fields (all optional):
      name, description, tags,
      aggregation_enabled, aggregation_function,
      child_template_ids (replaces the child list),
      child_weights (map of child_id -> weight).

    Args:
        template_id (str):
        body (CompositeEvalUpdateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CompositeEvalDetailResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        template_id=template_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    template_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: CompositeEvalUpdateRequest,
) -> (
    CompositeEvalDetailResponse
    | ManagementAPIErrorResponse
    | ModelHubErrorResponse
    | None
):
    """PATCH — partial update of a composite eval.

     Supported fields (all optional):
      name, description, tags,
      aggregation_enabled, aggregation_function,
      child_template_ids (replaces the child list),
      child_weights (map of child_id -> weight).

    Args:
        template_id (str):
        body (CompositeEvalUpdateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CompositeEvalDetailResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return (
        await asyncio_detailed(
            template_id=template_id,
            client=client,
            body=body,
        )
    ).parsed
