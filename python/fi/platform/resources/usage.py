"""Hand-written additions to `client.usage`.

Scaffolded once by sdkgen/generate.py and never overwritten: methods added here survive
regeneration. The generated methods live in `fi.platform.resources.base`.

    class Datasets(DatasetsResource):
        def get_by_name(self, name: str):
            ...                                     # compose generated methods, or
            return self._t.raw("GET", "/some/path/")  # call an endpoint the catalog lacks
"""

from __future__ import annotations

from typing import Any

from .. import models
from .._errors import NotFoundError
from .._transport import NOT_GIVEN, NotGiven, RequestOptions
from .base import AsyncUsageResource, UsageResource


class UsageOverviewUnavailableError(NotFoundError):
    """The deployment does not provide the usage overview endpoint."""


_UNAVAILABLE_MESSAGE = (
    "This deployment does not provide the usage overview endpoint "
    "(GET /usage/v2/usage-overview/)."
)


class Usage(UsageResource):
    """`client.usage`: every generated `usage.*` method, plus the hand-written additions in this module."""

    def overview(
        self, *, period: str | None | NotGiven = NOT_GIVEN,
        period_end: str | None | NotGiven = NOT_GIVEN,
        workspace_id: str | None | NotGiven = NOT_GIVEN,
        extra_query: dict[str, Any] | None = None,
        options: RequestOptions | None = None,
    ) -> models.UsageOverviewResult:
        """Return usage, or identify a deployment without GET /usage/v2/usage-overview/."""
        try:
            return super().overview(
                period=period, period_end=period_end, workspace_id=workspace_id,
                extra_query=extra_query, options=options,
            )
        except NotFoundError as exc:
            raise UsageOverviewUnavailableError(
                _UNAVAILABLE_MESSAGE, response=exc.response, body=exc.body,
            ) from exc


class AsyncUsage(AsyncUsageResource):
    """`client.usage` for `AsyncClient`: the same methods as `Usage`, awaited."""

    async def overview(
        self, *, period: str | None | NotGiven = NOT_GIVEN,
        period_end: str | None | NotGiven = NOT_GIVEN,
        workspace_id: str | None | NotGiven = NOT_GIVEN,
        extra_query: dict[str, Any] | None = None,
        options: RequestOptions | None = None,
    ) -> models.UsageOverviewResult:
        """Return usage, or identify a deployment without GET /usage/v2/usage-overview/."""
        try:
            return await super().overview(
                period=period, period_end=period_end, workspace_id=workspace_id,
                extra_query=extra_query, options=options,
            )
        except NotFoundError as exc:
            raise UsageOverviewUnavailableError(
                _UNAVAILABLE_MESSAGE, response=exc.response, body=exc.body,
            ) from exc
