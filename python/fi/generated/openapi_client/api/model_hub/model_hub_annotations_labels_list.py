from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.annotations_labels import AnnotationsLabels
from ...models.api_text_error_response import ApiTextErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.model_hub_annotations_labels_list_type import (
    ModelHubAnnotationsLabelsListType,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    dataset: UUID | Unset = UNSET,
    project_id: UUID | Unset = UNSET,
    type_: ModelHubAnnotationsLabelsListType | Unset = UNSET,
    search: str | Unset = UNSET,
    include_usage_count: bool | Unset = UNSET,
    include_archived: bool | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["page"] = page

    params["limit"] = limit

    json_dataset: str | Unset = UNSET
    if not isinstance(dataset, Unset):
        json_dataset = str(dataset)
    params["dataset"] = json_dataset

    json_project_id: str | Unset = UNSET
    if not isinstance(project_id, Unset):
        json_project_id = str(project_id)
    params["project_id"] = json_project_id

    json_type_: str | Unset = UNSET
    if not isinstance(type_, Unset):
        json_type_ = type_.value

    params["type"] = json_type_

    params["search"] = search

    params["include_usage_count"] = include_usage_count

    params["include_archived"] = include_archived

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/model-hub/annotations-labels/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | list[AnnotationsLabels]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = AnnotationsLabels.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200

    if response.status_code == 400:
        response_400 = ApiTextErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 403:
        response_403 = ApiTextErrorResponse.from_dict(response.json())

        return response_403

    if response.status_code == 500:
        response_500 = ApiTextErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | list[AnnotationsLabels]
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
    dataset: UUID | Unset = UNSET,
    project_id: UUID | Unset = UNSET,
    type_: ModelHubAnnotationsLabelsListType | Unset = UNSET,
    search: str | Unset = UNSET,
    include_usage_count: bool | Unset = UNSET,
    include_archived: bool | Unset = UNSET,
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | list[AnnotationsLabels]
]:
    """
    Args:
        page (int | Unset):
        limit (int | Unset):
        dataset (UUID | Unset):
        project_id (UUID | Unset):
        type_ (ModelHubAnnotationsLabelsListType | Unset):
        search (str | Unset):
        include_usage_count (bool | Unset):
        include_archived (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | list[AnnotationsLabels]]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
        dataset=dataset,
        project_id=project_id,
        type_=type_,
        search=search,
        include_usage_count=include_usage_count,
        include_archived=include_archived,
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
    dataset: UUID | Unset = UNSET,
    project_id: UUID | Unset = UNSET,
    type_: ModelHubAnnotationsLabelsListType | Unset = UNSET,
    search: str | Unset = UNSET,
    include_usage_count: bool | Unset = UNSET,
    include_archived: bool | Unset = UNSET,
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | list[AnnotationsLabels] | None:
    """
    Args:
        page (int | Unset):
        limit (int | Unset):
        dataset (UUID | Unset):
        project_id (UUID | Unset):
        type_ (ModelHubAnnotationsLabelsListType | Unset):
        search (str | Unset):
        include_usage_count (bool | Unset):
        include_archived (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | list[AnnotationsLabels]
    """

    return sync_detailed(
        client=client,
        page=page,
        limit=limit,
        dataset=dataset,
        project_id=project_id,
        type_=type_,
        search=search,
        include_usage_count=include_usage_count,
        include_archived=include_archived,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    dataset: UUID | Unset = UNSET,
    project_id: UUID | Unset = UNSET,
    type_: ModelHubAnnotationsLabelsListType | Unset = UNSET,
    search: str | Unset = UNSET,
    include_usage_count: bool | Unset = UNSET,
    include_archived: bool | Unset = UNSET,
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | list[AnnotationsLabels]
]:
    """
    Args:
        page (int | Unset):
        limit (int | Unset):
        dataset (UUID | Unset):
        project_id (UUID | Unset):
        type_ (ModelHubAnnotationsLabelsListType | Unset):
        search (str | Unset):
        include_usage_count (bool | Unset):
        include_archived (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | list[AnnotationsLabels]]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
        dataset=dataset,
        project_id=project_id,
        type_=type_,
        search=search,
        include_usage_count=include_usage_count,
        include_archived=include_archived,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    dataset: UUID | Unset = UNSET,
    project_id: UUID | Unset = UNSET,
    type_: ModelHubAnnotationsLabelsListType | Unset = UNSET,
    search: str | Unset = UNSET,
    include_usage_count: bool | Unset = UNSET,
    include_archived: bool | Unset = UNSET,
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | list[AnnotationsLabels] | None:
    """
    Args:
        page (int | Unset):
        limit (int | Unset):
        dataset (UUID | Unset):
        project_id (UUID | Unset):
        type_ (ModelHubAnnotationsLabelsListType | Unset):
        search (str | Unset):
        include_usage_count (bool | Unset):
        include_archived (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | list[AnnotationsLabels]
    """

    return (
        await asyncio_detailed(
            client=client,
            page=page,
            limit=limit,
            dataset=dataset,
            project_id=project_id,
            type_=type_,
            search=search,
            include_usage_count=include_usage_count,
            include_archived=include_archived,
        )
    ).parsed
