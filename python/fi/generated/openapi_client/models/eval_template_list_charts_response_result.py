from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.eval_template_list_charts_response_result_charts import (
        EvalTemplateListChartsResponseResultCharts,
    )


T = TypeVar("T", bound="EvalTemplateListChartsResponseResult")


@_attrs_define
class EvalTemplateListChartsResponseResult:
    """
    Attributes:
        charts (EvalTemplateListChartsResponseResultCharts):
    """

    charts: EvalTemplateListChartsResponseResultCharts
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        charts = self.charts.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "charts": charts,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_template_list_charts_response_result_charts import (
            EvalTemplateListChartsResponseResultCharts,
        )

        d = dict(src_dict)
        charts = EvalTemplateListChartsResponseResultCharts.from_dict(d.pop("charts"))

        eval_template_list_charts_response_result = cls(
            charts=charts,
        )

        eval_template_list_charts_response_result.additional_properties = d
        return eval_template_list_charts_response_result

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
