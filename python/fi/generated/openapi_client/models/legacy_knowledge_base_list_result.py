from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.legacy_knowledge_base_option import LegacyKnowledgeBaseOption


T = TypeVar("T", bound="LegacyKnowledgeBaseListResult")


@_attrs_define
class LegacyKnowledgeBaseListResult:
    """
    Attributes:
        table_data (list[LegacyKnowledgeBaseOption]):
    """

    table_data: list[LegacyKnowledgeBaseOption]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        table_data = []
        for table_data_item_data in self.table_data:
            table_data_item = table_data_item_data.to_dict()
            table_data.append(table_data_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "table_data": table_data,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.legacy_knowledge_base_option import LegacyKnowledgeBaseOption

        d = dict(src_dict)
        table_data = []
        _table_data = d.pop("table_data")
        for table_data_item_data in _table_data:
            table_data_item = LegacyKnowledgeBaseOption.from_dict(table_data_item_data)

            table_data.append(table_data_item)

        legacy_knowledge_base_list_result = cls(
            table_data=table_data,
        )

        legacy_knowledge_base_list_result.additional_properties = d
        return legacy_knowledge_base_list_result

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
