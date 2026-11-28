from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.trace_observe_column_config import TraceObserveColumnConfig
    from ..models.trace_session_list_metadata import TraceSessionListMetadata
    from ..models.trace_session_table_row import TraceSessionTableRow


T = TypeVar("T", bound="TraceSessionListResult")


@_attrs_define
class TraceSessionListResult:
    """
    Attributes:
        metadata (TraceSessionListMetadata):
        table (list[TraceSessionTableRow]):
        config (list[TraceObserveColumnConfig]):
    """

    metadata: TraceSessionListMetadata
    table: list[TraceSessionTableRow]
    config: list[TraceObserveColumnConfig]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        metadata = self.metadata.to_dict()

        table = []
        for table_item_data in self.table:
            table_item = table_item_data.to_dict()
            table.append(table_item)

        config = []
        for config_item_data in self.config:
            config_item = config_item_data.to_dict()
            config.append(config_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "metadata": metadata,
                "table": table,
                "config": config,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.trace_observe_column_config import TraceObserveColumnConfig
        from ..models.trace_session_list_metadata import TraceSessionListMetadata
        from ..models.trace_session_table_row import TraceSessionTableRow

        d = dict(src_dict)
        metadata = TraceSessionListMetadata.from_dict(d.pop("metadata"))

        table = []
        _table = d.pop("table")
        for table_item_data in _table:
            table_item = TraceSessionTableRow.from_dict(table_item_data)

            table.append(table_item)

        config = []
        _config = d.pop("config")
        for config_item_data in _config:
            config_item = TraceObserveColumnConfig.from_dict(config_item_data)

            config.append(config_item)

        trace_session_list_result = cls(
            metadata=metadata,
            table=table,
            config=config,
        )

        trace_session_list_result.additional_properties = d
        return trace_session_list_result

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
