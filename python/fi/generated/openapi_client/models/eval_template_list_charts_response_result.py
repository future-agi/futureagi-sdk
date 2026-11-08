from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.eval_template_list_charts_response_result_query_error_code import (
    EvalTemplateListChartsResponseResultQueryErrorCode,
)
from ..models.eval_template_list_charts_response_result_query_status import (
    EvalTemplateListChartsResponseResultQueryStatus,
)
from ..types import UNSET, Unset

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
        query_complete (bool):
        query_status (EvalTemplateListChartsResponseResultQueryStatus):
        query_sampled (bool):
        data_stale (bool):
        query_error_code (EvalTemplateListChartsResponseResultQueryErrorCode | Unset):
    """

    charts: EvalTemplateListChartsResponseResultCharts
    query_complete: bool
    query_status: EvalTemplateListChartsResponseResultQueryStatus
    query_sampled: bool
    data_stale: bool
    query_error_code: EvalTemplateListChartsResponseResultQueryErrorCode | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        charts = self.charts.to_dict()

        query_complete = self.query_complete

        query_status = self.query_status.value

        query_sampled = self.query_sampled

        data_stale = self.data_stale

        query_error_code: str | Unset = UNSET
        if not isinstance(self.query_error_code, Unset):
            query_error_code = self.query_error_code.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "charts": charts,
                "query_complete": query_complete,
                "query_status": query_status,
                "query_sampled": query_sampled,
                "data_stale": data_stale,
            }
        )
        if query_error_code is not UNSET:
            field_dict["query_error_code"] = query_error_code

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_template_list_charts_response_result_charts import (
            EvalTemplateListChartsResponseResultCharts,
        )

        d = dict(src_dict)
        charts = EvalTemplateListChartsResponseResultCharts.from_dict(d.pop("charts"))

        query_complete = d.pop("query_complete")

        query_status = EvalTemplateListChartsResponseResultQueryStatus(
            d.pop("query_status")
        )

        query_sampled = d.pop("query_sampled")

        data_stale = d.pop("data_stale")

        _query_error_code = d.pop("query_error_code", UNSET)
        query_error_code: EvalTemplateListChartsResponseResultQueryErrorCode | Unset
        if isinstance(_query_error_code, Unset):
            query_error_code = UNSET
        else:
            query_error_code = EvalTemplateListChartsResponseResultQueryErrorCode(
                _query_error_code
            )

        eval_template_list_charts_response_result = cls(
            charts=charts,
            query_complete=query_complete,
            query_status=query_status,
            query_sampled=query_sampled,
            data_stale=data_stale,
            query_error_code=query_error_code,
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
