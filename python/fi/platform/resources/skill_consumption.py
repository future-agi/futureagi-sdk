"""Hand-written additions to `client.skill_consumption`.

Scaffolded once by sdkgen/generate.py and never overwritten: methods added here survive
regeneration. The generated methods live in `fi.platform.resources.base`.

    class Datasets(DatasetsResource):
        def get_by_name(self, name: str):
            ...                                     # compose generated methods, or
            return self._t.raw("GET", "/some/path/")  # call an endpoint the catalog lacks
"""

from __future__ import annotations

from .base import AsyncSkillConsumptionResource, SkillConsumptionResource


class SkillConsumption(SkillConsumptionResource):
    """`client.skill_consumption`: every generated `skill_consumption.*` method, plus the hand-written additions in this module."""


class AsyncSkillConsumption(AsyncSkillConsumptionResource):
    """`client.skill_consumption` for `AsyncClient`: the same methods as `SkillConsumption`, awaited."""
