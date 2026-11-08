from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.composite_child_item import CompositeChildItem


T = TypeVar("T", bound="CompositeEvalCreateResponseResult")


@_attrs_define
class CompositeEvalCreateResponseResult:
    """
    Attributes:
        id (UUID):
        name (str):
        aggregation_enabled (bool):
        aggregation_function (str):
        children (list[CompositeChildItem]):
        template_type (str | Unset):
        composite_child_axis (str | Unset):
    """

    id: UUID
    name: str
    aggregation_enabled: bool
    aggregation_function: str
    children: list[CompositeChildItem]
    template_type: str | Unset = UNSET
    composite_child_axis: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        aggregation_enabled = self.aggregation_enabled

        aggregation_function = self.aggregation_function

        children = []
        for children_item_data in self.children:
            children_item = children_item_data.to_dict()
            children.append(children_item)

        template_type = self.template_type

        composite_child_axis = self.composite_child_axis

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "aggregation_enabled": aggregation_enabled,
                "aggregation_function": aggregation_function,
                "children": children,
            }
        )
        if template_type is not UNSET:
            field_dict["template_type"] = template_type
        if composite_child_axis is not UNSET:
            field_dict["composite_child_axis"] = composite_child_axis

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.composite_child_item import CompositeChildItem

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        aggregation_enabled = d.pop("aggregation_enabled")

        aggregation_function = d.pop("aggregation_function")

        children = []
        _children = d.pop("children")
        for children_item_data in _children:
            children_item = CompositeChildItem.from_dict(children_item_data)

            children.append(children_item)

        template_type = d.pop("template_type", UNSET)

        composite_child_axis = d.pop("composite_child_axis", UNSET)

        composite_eval_create_response_result = cls(
            id=id,
            name=name,
            aggregation_enabled=aggregation_enabled,
            aggregation_function=aggregation_function,
            children=children,
            template_type=template_type,
            composite_child_axis=composite_child_axis,
        )

        composite_eval_create_response_result.additional_properties = d
        return composite_eval_create_response_result

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
