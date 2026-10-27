"""Hand-written additions to `client.error_clusters`.

Scaffolded once by sdkgen/generate.py and never overwritten: methods added here survive
regeneration. The generated methods live in `fi.platform._generated.resources`.

    class Datasets(DatasetsResource):
        def get_by_name(self, name: str):
            ...                                     # compose generated methods, or
            return self._t.raw("GET", "/some/path/")  # call an endpoint the catalog lacks
"""

from __future__ import annotations

from .._generated.resources import AsyncErrorClustersResource, ErrorClustersResource


class ErrorClusters(ErrorClustersResource):
    """`client.error_clusters`: every generated `error_clusters.*` method, plus the hand-written additions in this module."""


class AsyncErrorClusters(AsyncErrorClustersResource):
    """`client.error_clusters` for `AsyncClient`: the same methods as `ErrorClusters`, awaited."""
