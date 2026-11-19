import datetime
from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.eval_usage_stats_response import EvalUsageStatsResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.model_hub_error_response import ModelHubErrorResponse
from ...models.model_hub_eval_templates_usage_list_period import (
    ModelHubEvalTemplatesUsageListPeriod,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    template_id: str,
    *,
    page: int | Unset = 0,
    page_size: int | Unset = 25,
    period: ModelHubEvalTemplatesUsageListPeriod
    | Unset = ModelHubEvalTemplatesUsageListPeriod.VALUE_4,
    start_date: datetime.datetime | Unset = UNSET,
    end_date: datetime.datetime | Unset = UNSET,
    refresh: bool | Unset = False,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["page"] = page

    params["page_size"] = page_size

    json_period: str | Unset = UNSET
    if not isinstance(period, Unset):
        json_period = period.value

    params["period"] = json_period

    json_start_date: str | Unset = UNSET
    if not isinstance(start_date, Unset):
        json_start_date = start_date.isoformat()
    params["start_date"] = json_start_date

    json_end_date: str | Unset = UNSET
    if not isinstance(end_date, Unset):
        json_end_date = end_date.isoformat()
    params["end_date"] = json_end_date

    params["refresh"] = refresh

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/model-hub/eval-templates/{template_id}/usage/".format(
            template_id=quote(str(template_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> EvalUsageStatsResponse | ManagementAPIErrorResponse | ModelHubErrorResponse:
    if response.status_code == 200:
        response_200 = EvalUsageStatsResponse.from_dict(response.json())

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
    EvalUsageStatsResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
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
    page: int | Unset = 0,
    page_size: int | Unset = 25,
    period: ModelHubEvalTemplatesUsageListPeriod
    | Unset = ModelHubEvalTemplatesUsageListPeriod.VALUE_4,
    start_date: datetime.datetime | Unset = UNSET,
    end_date: datetime.datetime | Unset = UNSET,
    refresh: bool | Unset = False,
) -> Response[
    EvalUsageStatsResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    """GET /model-hub/eval-templates/<id>/usage/

     Returns usage stats, chart data, and the paginated usage table.
    Query params: page (0-based), page_size, period
    (30m|6h|1d|7d|30d|90d|180d|365d), optional start_date/end_date pair
    (overrides period — sent by the FE for Today / Yesterday / Custom).

    The response is rendered through
    ``EvalUsageStatsResponseResultSerializer(instance=...).data`` at the
    boundary so shape drift surfaces here instead of shipping silently.

    Counts and lists only successful runs from the usage ledger
    (``APICallLog`` rows with status ``success``), from every source: tasks,
    playground, composites, datasets and experiments. Errored and skipped runs
    are not usage but stay in the eval logs (task logs, template eval logs);
    an in-flight run counts once it succeeds. ``error_count`` is therefore 0
    and ``pass_rate`` 100 whenever there are runs; both remain for
    compatibility.

    Pagination: page (0-based); page_size (page size).

    Args:
        template_id (str):
        page (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 25.
        period (ModelHubEvalTemplatesUsageListPeriod | Unset):  Default:
            ModelHubEvalTemplatesUsageListPeriod.VALUE_4.
        start_date (datetime.datetime | Unset):
        end_date (datetime.datetime | Unset):
        refresh (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EvalUsageStatsResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        template_id=template_id,
        page=page,
        page_size=page_size,
        period=period,
        start_date=start_date,
        end_date=end_date,
        refresh=refresh,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    template_id: str,
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = 0,
    page_size: int | Unset = 25,
    period: ModelHubEvalTemplatesUsageListPeriod
    | Unset = ModelHubEvalTemplatesUsageListPeriod.VALUE_4,
    start_date: datetime.datetime | Unset = UNSET,
    end_date: datetime.datetime | Unset = UNSET,
    refresh: bool | Unset = False,
) -> EvalUsageStatsResponse | ManagementAPIErrorResponse | ModelHubErrorResponse | None:
    """GET /model-hub/eval-templates/<id>/usage/

     Returns usage stats, chart data, and the paginated usage table.
    Query params: page (0-based), page_size, period
    (30m|6h|1d|7d|30d|90d|180d|365d), optional start_date/end_date pair
    (overrides period — sent by the FE for Today / Yesterday / Custom).

    The response is rendered through
    ``EvalUsageStatsResponseResultSerializer(instance=...).data`` at the
    boundary so shape drift surfaces here instead of shipping silently.

    Counts and lists only successful runs from the usage ledger
    (``APICallLog`` rows with status ``success``), from every source: tasks,
    playground, composites, datasets and experiments. Errored and skipped runs
    are not usage but stay in the eval logs (task logs, template eval logs);
    an in-flight run counts once it succeeds. ``error_count`` is therefore 0
    and ``pass_rate`` 100 whenever there are runs; both remain for
    compatibility.

    Pagination: page (0-based); page_size (page size).

    Args:
        template_id (str):
        page (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 25.
        period (ModelHubEvalTemplatesUsageListPeriod | Unset):  Default:
            ModelHubEvalTemplatesUsageListPeriod.VALUE_4.
        start_date (datetime.datetime | Unset):
        end_date (datetime.datetime | Unset):
        refresh (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EvalUsageStatsResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return sync_detailed(
        template_id=template_id,
        client=client,
        page=page,
        page_size=page_size,
        period=period,
        start_date=start_date,
        end_date=end_date,
        refresh=refresh,
    ).parsed


async def asyncio_detailed(
    template_id: str,
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = 0,
    page_size: int | Unset = 25,
    period: ModelHubEvalTemplatesUsageListPeriod
    | Unset = ModelHubEvalTemplatesUsageListPeriod.VALUE_4,
    start_date: datetime.datetime | Unset = UNSET,
    end_date: datetime.datetime | Unset = UNSET,
    refresh: bool | Unset = False,
) -> Response[
    EvalUsageStatsResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    """GET /model-hub/eval-templates/<id>/usage/

     Returns usage stats, chart data, and the paginated usage table.
    Query params: page (0-based), page_size, period
    (30m|6h|1d|7d|30d|90d|180d|365d), optional start_date/end_date pair
    (overrides period — sent by the FE for Today / Yesterday / Custom).

    The response is rendered through
    ``EvalUsageStatsResponseResultSerializer(instance=...).data`` at the
    boundary so shape drift surfaces here instead of shipping silently.

    Counts and lists only successful runs from the usage ledger
    (``APICallLog`` rows with status ``success``), from every source: tasks,
    playground, composites, datasets and experiments. Errored and skipped runs
    are not usage but stay in the eval logs (task logs, template eval logs);
    an in-flight run counts once it succeeds. ``error_count`` is therefore 0
    and ``pass_rate`` 100 whenever there are runs; both remain for
    compatibility.

    Pagination: page (0-based); page_size (page size).

    Args:
        template_id (str):
        page (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 25.
        period (ModelHubEvalTemplatesUsageListPeriod | Unset):  Default:
            ModelHubEvalTemplatesUsageListPeriod.VALUE_4.
        start_date (datetime.datetime | Unset):
        end_date (datetime.datetime | Unset):
        refresh (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EvalUsageStatsResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        template_id=template_id,
        page=page,
        page_size=page_size,
        period=period,
        start_date=start_date,
        end_date=end_date,
        refresh=refresh,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    template_id: str,
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = 0,
    page_size: int | Unset = 25,
    period: ModelHubEvalTemplatesUsageListPeriod
    | Unset = ModelHubEvalTemplatesUsageListPeriod.VALUE_4,
    start_date: datetime.datetime | Unset = UNSET,
    end_date: datetime.datetime | Unset = UNSET,
    refresh: bool | Unset = False,
) -> EvalUsageStatsResponse | ManagementAPIErrorResponse | ModelHubErrorResponse | None:
    """GET /model-hub/eval-templates/<id>/usage/

     Returns usage stats, chart data, and the paginated usage table.
    Query params: page (0-based), page_size, period
    (30m|6h|1d|7d|30d|90d|180d|365d), optional start_date/end_date pair
    (overrides period — sent by the FE for Today / Yesterday / Custom).

    The response is rendered through
    ``EvalUsageStatsResponseResultSerializer(instance=...).data`` at the
    boundary so shape drift surfaces here instead of shipping silently.

    Counts and lists only successful runs from the usage ledger
    (``APICallLog`` rows with status ``success``), from every source: tasks,
    playground, composites, datasets and experiments. Errored and skipped runs
    are not usage but stay in the eval logs (task logs, template eval logs);
    an in-flight run counts once it succeeds. ``error_count`` is therefore 0
    and ``pass_rate`` 100 whenever there are runs; both remain for
    compatibility.

    Pagination: page (0-based); page_size (page size).

    Args:
        template_id (str):
        page (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 25.
        period (ModelHubEvalTemplatesUsageListPeriod | Unset):  Default:
            ModelHubEvalTemplatesUsageListPeriod.VALUE_4.
        start_date (datetime.datetime | Unset):
        end_date (datetime.datetime | Unset):
        refresh (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EvalUsageStatsResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return (
        await asyncio_detailed(
            template_id=template_id,
            client=client,
            page=page,
            page_size=page_size,
            period=period,
            start_date=start_date,
            end_date=end_date,
            refresh=refresh,
        )
    ).parsed
