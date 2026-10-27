"""Hand-written additions to `client.experiments`.

Scaffolded once by sdkgen/generate.py and never overwritten: methods added here survive
regeneration. The generated methods live in `fi.platform._generated.resources`.

    class Datasets(DatasetsResource):
        def get_by_name(self, name: str):
            ...                                     # compose generated methods, or
            return self._t.raw("GET", "/some/path/")  # call an endpoint the catalog lacks
"""

from __future__ import annotations

from .._generated.resources import AsyncExperimentsResource, ExperimentsResource


class Experiments(ExperimentsResource):
    """`client.experiments`: every generated `experiments.*` method, plus the hand-written additions in this module."""


class AsyncExperiments(AsyncExperimentsResource):
    """`client.experiments` for `AsyncClient`: the same methods as `Experiments`, awaited."""
