"""Hand-written additions to `client.models`.

Scaffolded once by sdkgen/generate.py and never overwritten: methods added here survive
regeneration. The generated methods live in `fi.platform.resources.base`.

    class Datasets(DatasetsResource):
        def get_by_name(self, name: str):
            ...                                     # compose generated methods, or
            return self._t.raw("GET", "/some/path/")  # call an endpoint the catalog lacks
"""

from __future__ import annotations

from .base import AsyncModelsResource, ModelsResource


class Models(ModelsResource):
    """`client.models`: every generated `models.*` method, plus the hand-written additions in this module."""


class AsyncModels(AsyncModelsResource):
    """`client.models` for `AsyncClient`: the same methods as `Models`, awaited."""
