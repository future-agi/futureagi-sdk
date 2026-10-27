"""Hand-written additions to `client.evals`.

Scaffolded once by sdkgen/generate.py and never overwritten: methods added here survive
regeneration. The generated methods live in `fi.platform.resources.base`.

    class Datasets(DatasetsResource):
        def get_by_name(self, name: str):
            ...                                     # compose generated methods, or
            return self._t.raw("GET", "/some/path/")  # call an endpoint the catalog lacks
"""

from __future__ import annotations

from .base import AsyncEvalsResource, EvalsResource


class Evals(EvalsResource):
    """`client.evals`: every generated `evals.*` method, plus the hand-written additions in this module."""


class AsyncEvals(AsyncEvalsResource):
    """`client.evals` for `AsyncClient`: the same methods as `Evals`, awaited."""
