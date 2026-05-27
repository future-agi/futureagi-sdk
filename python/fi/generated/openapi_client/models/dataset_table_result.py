from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.dataset_table_metadata import DatasetTableMetadata
    from ..models.dataset_table_result_column_config_item import (
        DatasetTableResultColumnConfigItem,
    )
    from ..models.dataset_table_result_dataset_config import (
        DatasetTableResultDatasetConfig,
    )
    from ..models.dataset_table_result_table_item import DatasetTableResultTableItem


T = TypeVar("T", bound="DatasetTableResult")


@_attrs_define
class DatasetTableResult:
    """
    Attributes:
        column_config (list[DatasetTableResultColumnConfigItem]):
        metadata (DatasetTableMetadata | Unset):
        table (list[DatasetTableResultTableItem] | Unset):
        dataset_config (DatasetTableResultDatasetConfig | Unset):
        synthetic_dataset (bool | Unset):
        synthetic_dataset_percentage (float | None | Unset):
        synthetic_regenerate (bool | Unset):
        is_processing_data (bool | Unset):
    """

    column_config: list[DatasetTableResultColumnConfigItem]
    metadata: DatasetTableMetadata | Unset = UNSET
    table: list[DatasetTableResultTableItem] | Unset = UNSET
    dataset_config: DatasetTableResultDatasetConfig | Unset = UNSET
    synthetic_dataset: bool | Unset = UNSET
    synthetic_dataset_percentage: float | None | Unset = UNSET
    synthetic_regenerate: bool | Unset = UNSET
    is_processing_data: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        column_config = []
        for column_config_item_data in self.column_config:
            column_config_item = column_config_item_data.to_dict()
            column_config.append(column_config_item)

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        table: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.table, Unset):
            table = []
            for table_item_data in self.table:
                table_item = table_item_data.to_dict()
                table.append(table_item)

        dataset_config: dict[str, Any] | Unset = UNSET
        if not isinstance(self.dataset_config, Unset):
            dataset_config = self.dataset_config.to_dict()

        synthetic_dataset = self.synthetic_dataset

        synthetic_dataset_percentage: float | None | Unset
        if isinstance(self.synthetic_dataset_percentage, Unset):
            synthetic_dataset_percentage = UNSET
        else:
            synthetic_dataset_percentage = self.synthetic_dataset_percentage

        synthetic_regenerate = self.synthetic_regenerate

        is_processing_data = self.is_processing_data

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "column_config": column_config,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if table is not UNSET:
            field_dict["table"] = table
        if dataset_config is not UNSET:
            field_dict["dataset_config"] = dataset_config
        if synthetic_dataset is not UNSET:
            field_dict["synthetic_dataset"] = synthetic_dataset
        if synthetic_dataset_percentage is not UNSET:
            field_dict["synthetic_dataset_percentage"] = synthetic_dataset_percentage
        if synthetic_regenerate is not UNSET:
            field_dict["synthetic_regenerate"] = synthetic_regenerate
        if is_processing_data is not UNSET:
            field_dict["is_processing_data"] = is_processing_data

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.dataset_table_metadata import DatasetTableMetadata
        from ..models.dataset_table_result_column_config_item import (
            DatasetTableResultColumnConfigItem,
        )
        from ..models.dataset_table_result_dataset_config import (
            DatasetTableResultDatasetConfig,
        )
        from ..models.dataset_table_result_table_item import DatasetTableResultTableItem

        d = dict(src_dict)
        column_config = []
        _column_config = d.pop("column_config")
        for column_config_item_data in _column_config:
            column_config_item = DatasetTableResultColumnConfigItem.from_dict(
                column_config_item_data
            )

            column_config.append(column_config_item)

        _metadata = d.pop("metadata", UNSET)
        metadata: DatasetTableMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = DatasetTableMetadata.from_dict(_metadata)

        _table = d.pop("table", UNSET)
        table: list[DatasetTableResultTableItem] | Unset = UNSET
        if _table is not UNSET:
            table = []
            for table_item_data in _table:
                table_item = DatasetTableResultTableItem.from_dict(table_item_data)

                table.append(table_item)

        _dataset_config = d.pop("dataset_config", UNSET)
        dataset_config: DatasetTableResultDatasetConfig | Unset
        if isinstance(_dataset_config, Unset):
            dataset_config = UNSET
        else:
            dataset_config = DatasetTableResultDatasetConfig.from_dict(_dataset_config)

        synthetic_dataset = d.pop("synthetic_dataset", UNSET)

        def _parse_synthetic_dataset_percentage(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        synthetic_dataset_percentage = _parse_synthetic_dataset_percentage(
            d.pop("synthetic_dataset_percentage", UNSET)
        )

        synthetic_regenerate = d.pop("synthetic_regenerate", UNSET)

        is_processing_data = d.pop("is_processing_data", UNSET)

        dataset_table_result = cls(
            column_config=column_config,
            metadata=metadata,
            table=table,
            dataset_config=dataset_config,
            synthetic_dataset=synthetic_dataset,
            synthetic_dataset_percentage=synthetic_dataset_percentage,
            synthetic_regenerate=synthetic_regenerate,
            is_processing_data=is_processing_data,
        )

        dataset_table_result.additional_properties = d
        return dataset_table_result

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
