from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.eval_template_version_response import EvalTemplateVersionResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.model_hub_empty_request import ModelHubEmptyRequest
from ...models.model_hub_error_response import ModelHubErrorResponse
from ...types import Response


def _get_kwargs(
    template_id: str,
    version_id: str,
    *,
    body: ModelHubEmptyRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/model-hub/eval-templates/{template_id}/versions/{version_id}/set-default/".format(
            template_id=quote(str(template_id), safe=""),
            version_id=quote(str(version_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> EvalTemplateVersionResponse | ManagementAPIErrorResponse | ModelHubErrorResponse:
    if response.status_code == 200:
        response_200 = EvalTemplateVersionResponse.from_dict(response.json())

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
    EvalTemplateVersionResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    template_id: str,
    version_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: ModelHubEmptyRequest,
) -> Response[
    EvalTemplateVersionResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    """PUT /model-hub/eval-templates/<id>/versions/<version_id>/set-default/

     Set a specific version as the default (active) version.

    Args:
        template_id (str):
        version_id (str):
        body (ModelHubEmptyRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EvalTemplateVersionResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        template_id=template_id,
        version_id=version_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    template_id: str,
    version_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: ModelHubEmptyRequest,
) -> (
    EvalTemplateVersionResponse
    | ManagementAPIErrorResponse
    | ModelHubErrorResponse
    | None
):
    """PUT /model-hub/eval-templates/<id>/versions/<version_id>/set-default/

     Set a specific version as the default (active) version.

    Args:
        template_id (str):
        version_id (str):
        body (ModelHubEmptyRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EvalTemplateVersionResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return sync_detailed(
        template_id=template_id,
        version_id=version_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    template_id: str,
    version_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: ModelHubEmptyRequest,
) -> Response[
    EvalTemplateVersionResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    """PUT /model-hub/eval-templates/<id>/versions/<version_id>/set-default/

     Set a specific version as the default (active) version.

    Args:
        template_id (str):
        version_id (str):
        body (ModelHubEmptyRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EvalTemplateVersionResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        template_id=template_id,
        version_id=version_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    template_id: str,
    version_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: ModelHubEmptyRequest,
) -> (
    EvalTemplateVersionResponse
    | ManagementAPIErrorResponse
    | ModelHubErrorResponse
    | None
):
    """PUT /model-hub/eval-templates/<id>/versions/<version_id>/set-default/

     Set a specific version as the default (active) version.

    Args:
        template_id (str):
        version_id (str):
        body (ModelHubEmptyRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EvalTemplateVersionResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return (
        await asyncio_detailed(
            template_id=template_id,
            version_id=version_id,
            client=client,
            body=body,
        )
    ).parsed
