from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.compare_dataset_metadata import CompareDatasetMetadata
    from ..models.compare_dataset_result_column_config_item import (
        CompareDatasetResultColumnConfigItem,
    )
    from ..models.compare_dataset_result_table_item import CompareDatasetResultTableItem


T = TypeVar("T", bound="CompareDatasetResult")


@_attrs_define
class CompareDatasetResult:
    """
    Attributes:
        metadata (CompareDatasetMetadata | Unset):
        column_config (list[CompareDatasetResultColumnConfigItem] | Unset):
        table (list[CompareDatasetResultTableItem] | Unset):
    """

    metadata: CompareDatasetMetadata | Unset = UNSET
    column_config: list[CompareDatasetResultColumnConfigItem] | Unset = UNSET
    table: list[CompareDatasetResultTableItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        column_config: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.column_config, Unset):
            column_config = []
            for column_config_item_data in self.column_config:
                column_config_item = column_config_item_data.to_dict()
                column_config.append(column_config_item)

        table: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.table, Unset):
            table = []
            for table_item_data in self.table:
                table_item = table_item_data.to_dict()
                table.append(table_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if column_config is not UNSET:
            field_dict["column_config"] = column_config
        if table is not UNSET:
            field_dict["table"] = table

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.compare_dataset_metadata import CompareDatasetMetadata
        from ..models.compare_dataset_result_column_config_item import (
            CompareDatasetResultColumnConfigItem,
        )
        from ..models.compare_dataset_result_table_item import (
            CompareDatasetResultTableItem,
        )

        d = dict(src_dict)
        _metadata = d.pop("metadata", UNSET)
        metadata: CompareDatasetMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = CompareDatasetMetadata.from_dict(_metadata)

        _column_config = d.pop("column_config", UNSET)
        column_config: list[CompareDatasetResultColumnConfigItem] | Unset = UNSET
        if _column_config is not UNSET:
            column_config = []
            for column_config_item_data in _column_config:
                column_config_item = CompareDatasetResultColumnConfigItem.from_dict(
                    column_config_item_data
                )

                column_config.append(column_config_item)

        _table = d.pop("table", UNSET)
        table: list[CompareDatasetResultTableItem] | Unset = UNSET
        if _table is not UNSET:
            table = []
            for table_item_data in _table:
                table_item = CompareDatasetResultTableItem.from_dict(table_item_data)

                table.append(table_item)

        compare_dataset_result = cls(
            metadata=metadata,
            column_config=column_config,
            table=table,
        )

        compare_dataset_result.additional_properties = d
        return compare_dataset_result

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
