"""Hand-written additions to `client.spans`.

Scaffolded once by sdkgen/generate.py and never overwritten: methods added here survive
regeneration. The generated methods live in `fi.platform.resources.base`.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .._transport import RequestOptions
from .base import AsyncSpansResource, SpansResource

INGEST_PATH = "/tracer/observation-span/create_otel_span/"


class Spans(SpansResource):
    """`client.spans`: every generated `spans.*` method, plus `ingest()`."""

    def ingest(self, spans: List[Dict[str, Any]], *, options: RequestOptions | None = None) -> Dict[str, Any]:
        """Send spans straight to the tracer (`{"ids": [...]}`), without the traceAI exporter.

        POST /tracer/observation-span/create_otel_span/

        Hand-written: the endpoint takes a JSON *array*, which the catalog cannot express.
        Send one span for a brand-new project first; the backend creates the project from
        parallel threads, so a first batch of several spans can race on its unique constraint.
        """
        return self._t.raw("POST", INGEST_PATH, body=list(spans), options=options)


class AsyncSpans(AsyncSpansResource):
    """`client.spans` for `AsyncClient`: the same methods as `Spans`, awaited."""

    async def ingest(self, spans: List[Dict[str, Any]], *, options: RequestOptions | None = None) -> Dict[str, Any]:
        """See `Spans.ingest`."""
        return await self._t.raw("POST", INGEST_PATH, body=list(spans), options=options)
