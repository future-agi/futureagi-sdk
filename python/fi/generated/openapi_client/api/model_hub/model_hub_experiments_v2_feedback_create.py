from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.experiment_feedback_create_response import (
    ExperimentFeedbackCreateResponse,
)
from ...models.feedback import Feedback
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.model_hub_error_response import ModelHubErrorResponse
from ...types import Response


def _get_kwargs(
    experiment_id: str,
    *,
    body: Feedback,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/model-hub/experiments/v2/{experiment_id}/feedback/".format(
            experiment_id=quote(str(experiment_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ExperimentFeedbackCreateResponse
    | ManagementAPIErrorResponse
    | ModelHubErrorResponse
):
    if response.status_code == 200:
        response_200 = ExperimentFeedbackCreateResponse.from_dict(response.json())

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
    ExperimentFeedbackCreateResponse
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
    experiment_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: Feedback,
) -> Response[
    ExperimentFeedbackCreateResponse
    | ManagementAPIErrorResponse
    | ModelHubErrorResponse
]:
    """Create a feedback record scoped to an experiment.

    Args:
        experiment_id (str):
        body (Feedback):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ExperimentFeedbackCreateResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        experiment_id=experiment_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    experiment_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: Feedback,
) -> (
    ExperimentFeedbackCreateResponse
    | ManagementAPIErrorResponse
    | ModelHubErrorResponse
    | None
):
    """Create a feedback record scoped to an experiment.

    Args:
        experiment_id (str):
        body (Feedback):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ExperimentFeedbackCreateResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return sync_detailed(
        experiment_id=experiment_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    experiment_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: Feedback,
) -> Response[
    ExperimentFeedbackCreateResponse
    | ManagementAPIErrorResponse
    | ModelHubErrorResponse
]:
    """Create a feedback record scoped to an experiment.

    Args:
        experiment_id (str):
        body (Feedback):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ExperimentFeedbackCreateResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        experiment_id=experiment_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    experiment_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: Feedback,
) -> (
    ExperimentFeedbackCreateResponse
    | ManagementAPIErrorResponse
    | ModelHubErrorResponse
    | None
):
    """Create a feedback record scoped to an experiment.

    Args:
        experiment_id (str):
        body (Feedback):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ExperimentFeedbackCreateResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return (
        await asyncio_detailed(
            experiment_id=experiment_id,
            client=client,
            body=body,
        )
    ).parsed
