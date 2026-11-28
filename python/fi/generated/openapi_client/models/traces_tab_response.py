from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.traces_aggregates import TracesAggregates
    from ..models.traces_list_row import TracesListRow


T = TypeVar("T", bound="TracesTabResponse")


@_attrs_define
class TracesTabResponse:
    """
    Attributes:
        aggregates (TracesAggregates):
        traces (list[TracesListRow]):
        total (int):
    """

    aggregates: TracesAggregates
    traces: list[TracesListRow]
    total: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        aggregates = self.aggregates.to_dict()

        traces = []
        for traces_item_data in self.traces:
            traces_item = traces_item_data.to_dict()
            traces.append(traces_item)

        total = self.total

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "aggregates": aggregates,
                "traces": traces,
                "total": total,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.traces_aggregates import TracesAggregates
        from ..models.traces_list_row import TracesListRow

        d = dict(src_dict)
        aggregates = TracesAggregates.from_dict(d.pop("aggregates"))

        traces = []
        _traces = d.pop("traces")
        for traces_item_data in _traces:
            traces_item = TracesListRow.from_dict(traces_item_data)

            traces.append(traces_item)

        total = d.pop("total")

        traces_tab_response = cls(
            aggregates=aggregates,
            traces=traces,
            total=total,
        )

        traces_tab_response.additional_properties = d
        return traces_tab_response

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
