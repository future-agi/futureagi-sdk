from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.scenario_edit_request_graph import ScenarioEditRequestGraph


T = TypeVar("T", bound="ScenarioEditRequest")


@_attrs_define
class ScenarioEditRequest:
    """
    Attributes:
        name (str | Unset):
        description (str | Unset):
        graph (ScenarioEditRequestGraph | Unset):
        prompt (str | Unset):
    """

    name: str | Unset = UNSET
    description: str | Unset = UNSET
    graph: ScenarioEditRequestGraph | Unset = UNSET
    prompt: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        graph: dict[str, Any] | Unset = UNSET
        if not isinstance(self.graph, Unset):
            graph = self.graph.to_dict()

        prompt = self.prompt

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if graph is not UNSET:
            field_dict["graph"] = graph
        if prompt is not UNSET:
            field_dict["prompt"] = prompt

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.scenario_edit_request_graph import ScenarioEditRequestGraph

        d = dict(src_dict)
        name = d.pop("name", UNSET)

        description = d.pop("description", UNSET)

        _graph = d.pop("graph", UNSET)
        graph: ScenarioEditRequestGraph | Unset
        if isinstance(_graph, Unset):
            graph = UNSET
        else:
            graph = ScenarioEditRequestGraph.from_dict(_graph)

        prompt = d.pop("prompt", UNSET)

        scenario_edit_request = cls(
            name=name,
            description=description,
            graph=graph,
            prompt=prompt,
        )

        scenario_edit_request.additional_properties = d
        return scenario_edit_request

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
