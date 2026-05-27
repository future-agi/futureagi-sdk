from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.experiment_table_rows_column_config import (
        ExperimentTableRowsColumnConfig,
    )
    from ..models.experiment_table_rows_metadata import ExperimentTableRowsMetadata
    from ..models.experiment_table_rows_result_table_item import (
        ExperimentTableRowsResultTableItem,
    )


T = TypeVar("T", bound="ExperimentTableRowsResult")


@_attrs_define
class ExperimentTableRowsResult:
    """
    Attributes:
        column_config (list[ExperimentTableRowsColumnConfig]):
        table (list[ExperimentTableRowsResultTableItem] | Unset):
        metadata (ExperimentTableRowsMetadata | Unset):
        output_format (str | Unset):
        status (str | Unset):
        next_row_ids (list[UUID] | Unset):
    """

    column_config: list[ExperimentTableRowsColumnConfig]
    table: list[ExperimentTableRowsResultTableItem] | Unset = UNSET
    metadata: ExperimentTableRowsMetadata | Unset = UNSET
    output_format: str | Unset = UNSET
    status: str | Unset = UNSET
    next_row_ids: list[UUID] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
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

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        output_format = self.output_format

        status = self.status

        next_row_ids: list[str] | Unset = UNSET
        if not isinstance(self.next_row_ids, Unset):
            next_row_ids = []
            for next_row_ids_item_data in self.next_row_ids:
                next_row_ids_item = str(next_row_ids_item_data)
                next_row_ids.append(next_row_ids_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "column_config": column_config,
            }
        )
        if table is not UNSET:
            field_dict["table"] = table
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if output_format is not UNSET:
            field_dict["output_format"] = output_format
        if status is not UNSET:
            field_dict["status"] = status
        if next_row_ids is not UNSET:
            field_dict["next_row_ids"] = next_row_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.experiment_table_rows_column_config import (
            ExperimentTableRowsColumnConfig,
        )
        from ..models.experiment_table_rows_metadata import ExperimentTableRowsMetadata
        from ..models.experiment_table_rows_result_table_item import (
            ExperimentTableRowsResultTableItem,
        )

        d = dict(src_dict)
        column_config = []
        _column_config = d.pop("column_config")
        for column_config_item_data in _column_config:
            column_config_item = ExperimentTableRowsColumnConfig.from_dict(
                column_config_item_data
            )

            column_config.append(column_config_item)

        _table = d.pop("table", UNSET)
        table: list[ExperimentTableRowsResultTableItem] | Unset = UNSET
        if _table is not UNSET:
            table = []
            for table_item_data in _table:
                table_item = ExperimentTableRowsResultTableItem.from_dict(
                    table_item_data
                )

                table.append(table_item)

        _metadata = d.pop("metadata", UNSET)
        metadata: ExperimentTableRowsMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = ExperimentTableRowsMetadata.from_dict(_metadata)

        output_format = d.pop("output_format", UNSET)

        status = d.pop("status", UNSET)

        _next_row_ids = d.pop("next_row_ids", UNSET)
        next_row_ids: list[UUID] | Unset = UNSET
        if _next_row_ids is not UNSET:
            next_row_ids = []
            for next_row_ids_item_data in _next_row_ids:
                next_row_ids_item = UUID(next_row_ids_item_data)

                next_row_ids.append(next_row_ids_item)

        experiment_table_rows_result = cls(
            column_config=column_config,
            table=table,
            metadata=metadata,
            output_format=output_format,
            status=status,
            next_row_ids=next_row_ids,
        )

        experiment_table_rows_result.additional_properties = d
        return experiment_table_rows_result

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
