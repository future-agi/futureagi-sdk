from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.composite_child_item import CompositeChildItem


T = TypeVar("T", bound="CompositeEvalDetailResponseResult")


@_attrs_define
class CompositeEvalDetailResponseResult:
    """
    Attributes:
        id (UUID):
        name (str):
        aggregation_enabled (bool):
        aggregation_function (str):
        children (list[CompositeChildItem]):
        template_type (str | Unset):
        composite_child_axis (str | Unset):
        description (None | str | Unset):
        tags (list[str] | Unset):
        created_at (str | Unset):
        updated_at (str | Unset):
        version_number (int | None | Unset):
    """

    id: UUID
    name: str
    aggregation_enabled: bool
    aggregation_function: str
    children: list[CompositeChildItem]
    template_type: str | Unset = UNSET
    composite_child_axis: str | Unset = UNSET
    description: None | str | Unset = UNSET
    tags: list[str] | Unset = UNSET
    created_at: str | Unset = UNSET
    updated_at: str | Unset = UNSET
    version_number: int | None | Unset = UNSET
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

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        tags: list[str] | Unset = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags

        created_at = self.created_at

        updated_at = self.updated_at

        version_number: int | None | Unset
        if isinstance(self.version_number, Unset):
            version_number = UNSET
        else:
            version_number = self.version_number

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
        if description is not UNSET:
            field_dict["description"] = description
        if tags is not UNSET:
            field_dict["tags"] = tags
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if version_number is not UNSET:
            field_dict["version_number"] = version_number

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

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        tags = cast(list[str], d.pop("tags", UNSET))

        created_at = d.pop("created_at", UNSET)

        updated_at = d.pop("updated_at", UNSET)

        def _parse_version_number(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        version_number = _parse_version_number(d.pop("version_number", UNSET))

        composite_eval_detail_response_result = cls(
            id=id,
            name=name,
            aggregation_enabled=aggregation_enabled,
            aggregation_function=aggregation_function,
            children=children,
            template_type=template_type,
            composite_child_axis=composite_child_axis,
            description=description,
            tags=tags,
            created_at=created_at,
            updated_at=updated_at,
            version_number=version_number,
        )

        composite_eval_detail_response_result.additional_properties = d
        return composite_eval_detail_response_result

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
