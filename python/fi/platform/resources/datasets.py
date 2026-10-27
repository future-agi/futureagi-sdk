"""Hand-written additions to `client.datasets`.

Scaffolded once by sdkgen/generate.py and never overwritten: methods added here survive
regeneration. The generated methods live in `fi.platform._generated.resources`.

    class Datasets(DatasetsResource):
        def get_by_name(self, name: str):
            ...                                     # compose generated methods, or
            return self._t.raw("GET", "/some/path/")  # call an endpoint the catalog lacks
"""

from __future__ import annotations

from .._generated.resources import AsyncDatasetsResource, DatasetsResource


class Datasets(DatasetsResource):
    """`client.datasets`: every generated `datasets.*` method, plus the hand-written additions in this module."""


class AsyncDatasets(AsyncDatasetsResource):
    """`client.datasets` for `AsyncClient`: the same methods as `Datasets`, awaited."""
