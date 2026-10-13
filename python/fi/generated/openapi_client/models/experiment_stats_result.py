from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.experiment_stats_column_config import ExperimentStatsColumnConfig
    from ..models.experiment_stats_metadata import ExperimentStatsMetadata
    from ..models.experiment_stats_result_table_data_item import (
        ExperimentStatsResultTableDataItem,
    )


T = TypeVar("T", bound="ExperimentStatsResult")


@_attrs_define
class ExperimentStatsResult:
    """
    Attributes:
        column_config (list[ExperimentStatsColumnConfig]):
        table_data (list[ExperimentStatsResultTableDataItem]):
        metadata (ExperimentStatsMetadata):
    """

    column_config: list[ExperimentStatsColumnConfig]
    table_data: list[ExperimentStatsResultTableDataItem]
    metadata: ExperimentStatsMetadata
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        column_config = []
        for column_config_item_data in self.column_config:
            column_config_item = column_config_item_data.to_dict()
            column_config.append(column_config_item)

        table_data = []
        for table_data_item_data in self.table_data:
            table_data_item = table_data_item_data.to_dict()
            table_data.append(table_data_item)

        metadata = self.metadata.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "column_config": column_config,
                "table_data": table_data,
                "metadata": metadata,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.experiment_stats_column_config import ExperimentStatsColumnConfig
        from ..models.experiment_stats_metadata import ExperimentStatsMetadata
        from ..models.experiment_stats_result_table_data_item import (
            ExperimentStatsResultTableDataItem,
        )

        d = dict(src_dict)
        column_config = []
        _column_config = d.pop("column_config")
        for column_config_item_data in _column_config:
            column_config_item = ExperimentStatsColumnConfig.from_dict(
                column_config_item_data
            )

            column_config.append(column_config_item)

        table_data = []
        _table_data = d.pop("table_data")
        for table_data_item_data in _table_data:
            table_data_item = ExperimentStatsResultTableDataItem.from_dict(
                table_data_item_data
            )

            table_data.append(table_data_item)

        metadata = ExperimentStatsMetadata.from_dict(d.pop("metadata"))

        experiment_stats_result = cls(
            column_config=column_config,
            table_data=table_data,
            metadata=metadata,
        )

        experiment_stats_result.additional_properties = d
        return experiment_stats_result

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
