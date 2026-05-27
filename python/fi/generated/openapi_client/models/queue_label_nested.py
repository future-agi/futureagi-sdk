from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="QueueLabelNested")


@_attrs_define
class QueueLabelNested:
    """
    Attributes:
        label_id (UUID):
        id (UUID | Unset):
        name (str | Unset):
        type_ (str | Unset):
        required (bool | Unset):
        order (int | Unset):
    """

    label_id: UUID
    id: UUID | Unset = UNSET
    name: str | Unset = UNSET
    type_: str | Unset = UNSET
    required: bool | Unset = UNSET
    order: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        label_id = str(self.label_id)

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        name = self.name

        type_ = self.type_

        required = self.required

        order = self.order

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "label_id": label_id,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if type_ is not UNSET:
            field_dict["type"] = type_
        if required is not UNSET:
            field_dict["required"] = required
        if order is not UNSET:
            field_dict["order"] = order

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        label_id = UUID(d.pop("label_id"))

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        name = d.pop("name", UNSET)

        type_ = d.pop("type", UNSET)

        required = d.pop("required", UNSET)

        order = d.pop("order", UNSET)

        queue_label_nested = cls(
            label_id=label_id,
            id=id,
            name=name,
            type_=type_,
            required=required,
            order=order,
        )

        queue_label_nested.additional_properties = d
        return queue_label_nested

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
