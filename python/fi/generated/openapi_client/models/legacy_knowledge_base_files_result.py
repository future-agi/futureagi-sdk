from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

if TYPE_CHECKING:
    from ..models.legacy_knowledge_base_file_row import LegacyKnowledgeBaseFileRow


T = TypeVar("T", bound="LegacyKnowledgeBaseFilesResult")


@_attrs_define
class LegacyKnowledgeBaseFilesResult:
    """
    Attributes:
        table_data (list[LegacyKnowledgeBaseFileRow]):
        last_updated (datetime.datetime):
        status (str):
        status_count (int):
        total_rows (int):
    """

    table_data: list[LegacyKnowledgeBaseFileRow]
    last_updated: datetime.datetime
    status: str
    status_count: int
    total_rows: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        table_data = []
        for table_data_item_data in self.table_data:
            table_data_item = table_data_item_data.to_dict()
            table_data.append(table_data_item)

        last_updated = self.last_updated.isoformat()

        status = self.status

        status_count = self.status_count

        total_rows = self.total_rows

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "table_data": table_data,
                "last_updated": last_updated,
                "status": status,
                "status_count": status_count,
                "total_rows": total_rows,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.legacy_knowledge_base_file_row import LegacyKnowledgeBaseFileRow

        d = dict(src_dict)
        table_data = []
        _table_data = d.pop("table_data")
        for table_data_item_data in _table_data:
            table_data_item = LegacyKnowledgeBaseFileRow.from_dict(table_data_item_data)

            table_data.append(table_data_item)

        last_updated = isoparse(d.pop("last_updated"))

        status = d.pop("status")

        status_count = d.pop("status_count")

        total_rows = d.pop("total_rows")

        legacy_knowledge_base_files_result = cls(
            table_data=table_data,
            last_updated=last_updated,
            status=status,
            status_count=status_count,
            total_rows=total_rows,
        )

        legacy_knowledge_base_files_result.additional_properties = d
        return legacy_knowledge_base_files_result

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
