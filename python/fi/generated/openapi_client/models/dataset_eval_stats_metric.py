from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.dataset_eval_stats_metric_output import DatasetEvalStatsMetricOutput


T = TypeVar("T", bound="DatasetEvalStatsMetric")


@_attrs_define
class DatasetEvalStatsMetric:
    """
    Attributes:
        name (str):
        output (DatasetEvalStatsMetricOutput):
        id (UUID | Unset):
        total_cells (int | None | Unset):
    """

    name: str
    output: DatasetEvalStatsMetricOutput
    id: UUID | Unset = UNSET
    total_cells: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        output = self.output.to_dict()

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        total_cells: int | None | Unset
        if isinstance(self.total_cells, Unset):
            total_cells = UNSET
        else:
            total_cells = self.total_cells

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "output": output,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if total_cells is not UNSET:
            field_dict["total_cells"] = total_cells

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.dataset_eval_stats_metric_output import (
            DatasetEvalStatsMetricOutput,
        )

        d = dict(src_dict)
        name = d.pop("name")

        output = DatasetEvalStatsMetricOutput.from_dict(d.pop("output"))

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        def _parse_total_cells(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        total_cells = _parse_total_cells(d.pop("total_cells", UNSET))

        dataset_eval_stats_metric = cls(
            name=name,
            output=output,
            id=id,
            total_cells=total_cells,
        )

        dataset_eval_stats_metric.additional_properties = d
        return dataset_eval_stats_metric

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
