from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="QueueForSourceItem")


@_attrs_define
class QueueForSourceItem:
    """
    Attributes:
        id (UUID):
        status (str):
        source_type (str):
        source_id (None | str):
    """

    id: UUID
    status: str
    source_type: str
    source_id: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        status = self.status

        source_type = self.source_type

        source_id: None | str
        source_id = self.source_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "status": status,
                "source_type": source_type,
                "source_id": source_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        status = d.pop("status")

        source_type = d.pop("source_type")

        def _parse_source_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        source_id = _parse_source_id(d.pop("source_id"))

        queue_for_source_item = cls(
            id=id,
            status=status,
            source_type=source_type,
            source_id=source_id,
        )

        queue_for_source_item.additional_properties = d
        return queue_for_source_item

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
