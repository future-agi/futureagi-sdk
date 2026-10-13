from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.dataset_eval_stats_item_total_avg import DatasetEvalStatsItemTotalAvg
    from ..models.dataset_eval_stats_item_total_choices_avg import (
        DatasetEvalStatsItemTotalChoicesAvg,
    )
    from ..models.dataset_eval_stats_metric import DatasetEvalStatsMetric


T = TypeVar("T", bound="DatasetEvalStatsItem")


@_attrs_define
class DatasetEvalStatsItem:
    """
    Attributes:
        id (UUID):
        name (str):
        output_type (str):
        result (list[DatasetEvalStatsMetric]):
        total_pass_rate (float | None | Unset):
        total_avg (DatasetEvalStatsItemTotalAvg | Unset):
        total_choices_avg (DatasetEvalStatsItemTotalChoicesAvg | Unset):
        is_numeric_eval (bool | Unset):
        is_numeric_eval_percentage (bool | Unset):
    """

    id: UUID
    name: str
    output_type: str
    result: list[DatasetEvalStatsMetric]
    total_pass_rate: float | None | Unset = UNSET
    total_avg: DatasetEvalStatsItemTotalAvg | Unset = UNSET
    total_choices_avg: DatasetEvalStatsItemTotalChoicesAvg | Unset = UNSET
    is_numeric_eval: bool | Unset = UNSET
    is_numeric_eval_percentage: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        output_type = self.output_type

        result = []
        for result_item_data in self.result:
            result_item = result_item_data.to_dict()
            result.append(result_item)

        total_pass_rate: float | None | Unset
        if isinstance(self.total_pass_rate, Unset):
            total_pass_rate = UNSET
        else:
            total_pass_rate = self.total_pass_rate

        total_avg: dict[str, Any] | Unset = UNSET
        if not isinstance(self.total_avg, Unset):
            total_avg = self.total_avg.to_dict()

        total_choices_avg: dict[str, Any] | Unset = UNSET
        if not isinstance(self.total_choices_avg, Unset):
            total_choices_avg = self.total_choices_avg.to_dict()

        is_numeric_eval = self.is_numeric_eval

        is_numeric_eval_percentage = self.is_numeric_eval_percentage

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "output_type": output_type,
                "result": result,
            }
        )
        if total_pass_rate is not UNSET:
            field_dict["total_pass_rate"] = total_pass_rate
        if total_avg is not UNSET:
            field_dict["total_avg"] = total_avg
        if total_choices_avg is not UNSET:
            field_dict["total_choices_avg"] = total_choices_avg
        if is_numeric_eval is not UNSET:
            field_dict["is_numeric_eval"] = is_numeric_eval
        if is_numeric_eval_percentage is not UNSET:
            field_dict["is_numeric_eval_percentage"] = is_numeric_eval_percentage

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.dataset_eval_stats_item_total_avg import (
            DatasetEvalStatsItemTotalAvg,
        )
        from ..models.dataset_eval_stats_item_total_choices_avg import (
            DatasetEvalStatsItemTotalChoicesAvg,
        )
        from ..models.dataset_eval_stats_metric import DatasetEvalStatsMetric

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        output_type = d.pop("output_type")

        result = []
        _result = d.pop("result")
        for result_item_data in _result:
            result_item = DatasetEvalStatsMetric.from_dict(result_item_data)

            result.append(result_item)

        def _parse_total_pass_rate(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        total_pass_rate = _parse_total_pass_rate(d.pop("total_pass_rate", UNSET))

        _total_avg = d.pop("total_avg", UNSET)
        total_avg: DatasetEvalStatsItemTotalAvg | Unset
        if isinstance(_total_avg, Unset):
            total_avg = UNSET
        else:
            total_avg = DatasetEvalStatsItemTotalAvg.from_dict(_total_avg)

        _total_choices_avg = d.pop("total_choices_avg", UNSET)
        total_choices_avg: DatasetEvalStatsItemTotalChoicesAvg | Unset
        if isinstance(_total_choices_avg, Unset):
            total_choices_avg = UNSET
        else:
            total_choices_avg = DatasetEvalStatsItemTotalChoicesAvg.from_dict(
                _total_choices_avg
            )

        is_numeric_eval = d.pop("is_numeric_eval", UNSET)

        is_numeric_eval_percentage = d.pop("is_numeric_eval_percentage", UNSET)

        dataset_eval_stats_item = cls(
            id=id,
            name=name,
            output_type=output_type,
            result=result,
            total_pass_rate=total_pass_rate,
            total_avg=total_avg,
            total_choices_avg=total_choices_avg,
            is_numeric_eval=is_numeric_eval,
            is_numeric_eval_percentage=is_numeric_eval_percentage,
        )

        dataset_eval_stats_item.additional_properties = d
        return dataset_eval_stats_item

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
