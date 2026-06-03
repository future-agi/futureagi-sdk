from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.eval_template_chart_point import EvalTemplateChartPoint


T = TypeVar("T", bound="EvalTemplateListChartsItem")


@_attrs_define
class EvalTemplateListChartsItem:
    """
    Attributes:
        chart (list[EvalTemplateChartPoint]):
        error_rate (list[EvalTemplateChartPoint]):
        run_count (int):
    """

    chart: list[EvalTemplateChartPoint]
    error_rate: list[EvalTemplateChartPoint]
    run_count: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        chart = []
        for chart_item_data in self.chart:
            chart_item = chart_item_data.to_dict()
            chart.append(chart_item)

        error_rate = []
        for error_rate_item_data in self.error_rate:
            error_rate_item = error_rate_item_data.to_dict()
            error_rate.append(error_rate_item)

        run_count = self.run_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "chart": chart,
                "error_rate": error_rate,
                "run_count": run_count,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_template_chart_point import EvalTemplateChartPoint

        d = dict(src_dict)
        chart = []
        _chart = d.pop("chart")
        for chart_item_data in _chart:
            chart_item = EvalTemplateChartPoint.from_dict(chart_item_data)

            chart.append(chart_item)

        error_rate = []
        _error_rate = d.pop("error_rate")
        for error_rate_item_data in _error_rate:
            error_rate_item = EvalTemplateChartPoint.from_dict(error_rate_item_data)

            error_rate.append(error_rate_item)

        run_count = d.pop("run_count")

        eval_template_list_charts_item = cls(
            chart=chart,
            error_rate=error_rate,
            run_count=run_count,
        )

        eval_template_list_charts_item.additional_properties = d
        return eval_template_list_charts_item

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
