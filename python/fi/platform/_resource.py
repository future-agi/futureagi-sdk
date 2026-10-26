"""Base classes that make the generated resource tree replaceable piece by piece."""

from __future__ import annotations

from typing import Any, Dict


class Resource:
    """A group of methods sharing one transport (`client.datasets`, `client.datasets.columns`).

    `_children` maps attribute name -> class for nested resources. A subclass can swap one:

        class Datasets(DatasetsResource):
            _children = {**DatasetsResource._children, "columns": MyColumns}
    """

    _children: Dict[str, type] = {}

    def __init__(self, transport: Any) -> None:
        self._t = transport
        for name, cls in self._children.items():
            setattr(self, name, cls(transport))


class ResourceSet:
    """Mixed into `Client`: `_resources` maps attribute name -> top-level resource class.

    Override it in a subclass to swap or add resources:

        class MyClient(Client):
            _resources = {**Client._resources, "datasets": MyDatasets, "billing": Billing}
    """

    _resources: Dict[str, type] = {}

    def _init_resources(self, transport: Any) -> None:
        for name, cls in self._resources.items():
            setattr(self, name, cls(transport))
