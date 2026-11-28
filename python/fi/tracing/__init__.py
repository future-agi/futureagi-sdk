"""Observe queries on the one client; instrumentation belongs to traceAI.

Methods preserve response envelopes, identity fields and page/completeness metadata.
Use ``spans_by_trace`` for one trace in one project, and pass the returned cursor
explicitly to read another bounded page. No method silently claims a full trace.
Error clusters keep their existing ``issues``, ``issue`` and ``issue_stats`` names.
"""
from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

from fi.errors import ConfigurationError
from fi.generated.platform.catalog.dashboards import AsyncDashboards, Dashboards
from fi.generated.platform.tracing import AsyncTracingQueries, TracingQueries

__all__ = ['AsyncTracingClient', 'TracingClient']


def _trace_query(trace_id: str, project_id: str, filters: Sequence[Mapping[str, Any]] | None,
                 query: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(trace_id, str) or not trace_id.strip():
        raise ConfigurationError('trace_id must be a non-empty string')
    if not isinstance(project_id, str) or not project_id.strip():
        raise ConfigurationError('project_id must be a non-empty string')
    if filters is not None and (not isinstance(filters, (list, tuple)) or
                                any(not isinstance(item, Mapping) for item in filters)):
        raise ConfigurationError('filters must be a sequence of filter mappings')
    scoped = [dict(item) for item in (filters or [])]
    scoped.append({'column_id': 'trace_id', 'filter_config': {
        'col_type': 'SYSTEM_METRIC', 'filter_type': 'text',
        'filter_op': 'in', 'filter_value': [trace_id],
    }})
    return {**query, 'project_id': project_id, 'filters': json.dumps(scoped)}


class AsyncTracingClient(AsyncTracingQueries):
    """Async Observe queries and dashboard management over the root client's pool."""

    dashboards: AsyncDashboards

    def __init__(self, client: Any) -> None:
        super().__init__(client)
        self.dashboards = AsyncDashboards(client)

    async def spans_by_trace(self, trace_id: str, *, project_id: str,
                             filters: Sequence[Mapping[str, Any]] | None = None,
                             **query: Any) -> Any:
        """Read a bounded span page for a trace; keep cursor and completeness metadata.

        ``project_id`` is required because trace identifiers can occur in several
        projects. Additional filters are ANDed with the trace identity filter.

        Pagination: page_number (0-based); page_size (page size); cursor (opaque continuation token); cursor_mode (enable cursor pagination)."""
        return await self.spans(**_trace_query(trace_id, project_id, filters, query))


class TracingClient(TracingQueries):
    """Synchronous twin of AsyncTracingClient; it does not run an event loop."""

    dashboards: Dashboards

    def __init__(self, client: Any) -> None:
        super().__init__(client)
        self.dashboards = Dashboards(client)

    def spans_by_trace(self, trace_id: str, *, project_id: str,
                       filters: Sequence[Mapping[str, Any]] | None = None,
                       **query: Any) -> Any:
        """Read one span page, scoped to both project and trace, without flattening it.

        Pagination: page_number (0-based); page_size (page size); cursor (opaque continuation token); cursor_mode (enable cursor pagination)."""
        return self.spans(**_trace_query(trace_id, project_id, filters, query))
