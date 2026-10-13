from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.legacy_knowledge_base_table_column import (
        LegacyKnowledgeBaseTableColumn,
    )
    from ..models.legacy_knowledge_base_table_row import LegacyKnowledgeBaseTableRow


T = TypeVar("T", bound="LegacyKnowledgeBaseTableResult")


@_attrs_define
class LegacyKnowledgeBaseTableResult:
    """
    Attributes:
        column_config (list[LegacyKnowledgeBaseTableColumn] | Unset):
        table_data (list[LegacyKnowledgeBaseTableRow] | Unset):
        total_rows (int | Unset):
    """

    column_config: list[LegacyKnowledgeBaseTableColumn] | Unset = UNSET
    table_data: list[LegacyKnowledgeBaseTableRow] | Unset = UNSET
    total_rows: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        column_config: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.column_config, Unset):
            column_config = []
            for column_config_item_data in self.column_config:
                column_config_item = column_config_item_data.to_dict()
                column_config.append(column_config_item)

        table_data: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.table_data, Unset):
            table_data = []
            for table_data_item_data in self.table_data:
                table_data_item = table_data_item_data.to_dict()
                table_data.append(table_data_item)

        total_rows = self.total_rows

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if column_config is not UNSET:
            field_dict["column_config"] = column_config
        if table_data is not UNSET:
            field_dict["table_data"] = table_data
        if total_rows is not UNSET:
            field_dict["total_rows"] = total_rows

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.legacy_knowledge_base_table_column import (
            LegacyKnowledgeBaseTableColumn,
        )
        from ..models.legacy_knowledge_base_table_row import LegacyKnowledgeBaseTableRow

        d = dict(src_dict)
        _column_config = d.pop("column_config", UNSET)
        column_config: list[LegacyKnowledgeBaseTableColumn] | Unset = UNSET
        if _column_config is not UNSET:
            column_config = []
            for column_config_item_data in _column_config:
                column_config_item = LegacyKnowledgeBaseTableColumn.from_dict(
                    column_config_item_data
                )

                column_config.append(column_config_item)

        _table_data = d.pop("table_data", UNSET)
        table_data: list[LegacyKnowledgeBaseTableRow] | Unset = UNSET
        if _table_data is not UNSET:
            table_data = []
            for table_data_item_data in _table_data:
                table_data_item = LegacyKnowledgeBaseTableRow.from_dict(
                    table_data_item_data
                )

                table_data.append(table_data_item)

        total_rows = d.pop("total_rows", UNSET)

        legacy_knowledge_base_table_result = cls(
            column_config=column_config,
            table_data=table_data,
            total_rows=total_rows,
        )

        legacy_knowledge_base_table_result.additional_properties = d
        return legacy_knowledge_base_table_result

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
