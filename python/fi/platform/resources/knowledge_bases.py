"""Hand-written additions to `client.knowledge_bases`.

Scaffolded once by sdkgen/generate.py and never overwritten: methods added here survive
regeneration. The generated methods live in `fi.platform._generated.resources`.

    class Datasets(DatasetsResource):
        def get_by_name(self, name: str):
            ...                                     # compose generated methods, or
            return self._t.raw("GET", "/some/path/")  # call an endpoint the catalog lacks
"""

from __future__ import annotations

from .._generated.resources import AsyncKnowledgeBasesResource, KnowledgeBasesResource


class KnowledgeBases(KnowledgeBasesResource):
    """`client.knowledge_bases`: every generated `knowledge_bases.*` method, plus the hand-written additions in this module."""


class AsyncKnowledgeBases(AsyncKnowledgeBasesResource):
    """`client.knowledge_bases` for `AsyncClient`: the same methods as `KnowledgeBases`, awaited."""
