from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.add_queue_item_source_type import AddQueueItemSourceType

T = TypeVar("T", bound="AddQueueItem")


@_attrs_define
class AddQueueItem:
    """
    Attributes:
        source_type (AddQueueItemSourceType):
        source_id (str):
    """

    source_type: AddQueueItemSourceType
    source_id: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        source_type = self.source_type.value

        source_id = self.source_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "source_type": source_type,
                "source_id": source_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        source_type = AddQueueItemSourceType(d.pop("source_type"))

        source_id = d.pop("source_id")

        add_queue_item = cls(
            source_type=source_type,
            source_id=source_id,
        )

        add_queue_item.additional_properties = d
        return add_queue_item

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
