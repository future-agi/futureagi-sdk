from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.experiment_name_suggestion_response import (
    ExperimentNameSuggestionResponse,
)
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.model_hub_error_response import ModelHubErrorResponse
from ...types import Response


def _get_kwargs(
    dataset_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/model-hub/experiments/v2/suggest-name/{dataset_id}/".format(
            dataset_id=quote(str(dataset_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ExperimentNameSuggestionResponse
    | ManagementAPIErrorResponse
    | ModelHubErrorResponse
):
    if response.status_code == 200:
        response_200 = ExperimentNameSuggestionResponse.from_dict(response.json())

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
    ExperimentNameSuggestionResponse
    | ManagementAPIErrorResponse
    | ModelHubErrorResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    dataset_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    ExperimentNameSuggestionResponse
    | ManagementAPIErrorResponse
    | ModelHubErrorResponse
]:
    """Generate a suggested experiment name for a dataset.

    Args:
        dataset_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ExperimentNameSuggestionResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        dataset_id=dataset_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    dataset_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    ExperimentNameSuggestionResponse
    | ManagementAPIErrorResponse
    | ModelHubErrorResponse
    | None
):
    """Generate a suggested experiment name for a dataset.

    Args:
        dataset_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ExperimentNameSuggestionResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return sync_detailed(
        dataset_id=dataset_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    dataset_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    ExperimentNameSuggestionResponse
    | ManagementAPIErrorResponse
    | ModelHubErrorResponse
]:
    """Generate a suggested experiment name for a dataset.

    Args:
        dataset_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ExperimentNameSuggestionResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        dataset_id=dataset_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    dataset_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    ExperimentNameSuggestionResponse
    | ManagementAPIErrorResponse
    | ModelHubErrorResponse
    | None
):
    """Generate a suggested experiment name for a dataset.

    Args:
        dataset_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ExperimentNameSuggestionResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return (
        await asyncio_detailed(
            dataset_id=dataset_id,
            client=client,
        )
    ).parsed
