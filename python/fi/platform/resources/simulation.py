"""Hand-written additions to `client.simulation`.

Scaffolded once by sdkgen/generate.py and never overwritten: methods added here survive
regeneration. The generated methods live in `fi.platform._generated.resources`.

    class Datasets(DatasetsResource):
        def get_by_name(self, name: str):
            ...                                     # compose generated methods, or
            return self._t.raw("GET", "/some/path/")  # call an endpoint the catalog lacks
"""

from __future__ import annotations

from .._generated.resources import AsyncSimulationResource, SimulationResource


class Simulation(SimulationResource):
    """`client.simulation`: every generated `simulation.*` method, plus the hand-written additions in this module."""


class AsyncSimulation(AsyncSimulationResource):
    """`client.simulation` for `AsyncClient`: the same methods as `Simulation`, awaited."""
