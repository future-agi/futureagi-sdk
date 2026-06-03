from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.sdk_simulation_analytics_result_eval_averages import (
        SDKSimulationAnalyticsResultEvalAverages,
    )
    from ..models.sdk_simulation_analytics_result_eval_explanation_summary import (
        SDKSimulationAnalyticsResultEvalExplanationSummary,
    )
    from ..models.sdk_simulation_analytics_result_eval_results_item import (
        SDKSimulationAnalyticsResultEvalResultsItem,
    )
    from ..models.sdk_simulation_analytics_result_system_summary import (
        SDKSimulationAnalyticsResultSystemSummary,
    )


T = TypeVar("T", bound="SDKSimulationAnalyticsResult")


@_attrs_define
class SDKSimulationAnalyticsResult:
    """
    Attributes:
        run_test_name (str):
        eval_results (list[SDKSimulationAnalyticsResultEvalResultsItem]):
        eval_averages (SDKSimulationAnalyticsResultEvalAverages):
        system_summary (SDKSimulationAnalyticsResultSystemSummary):
        execution_id (UUID | Unset):
        status (str | Unset):
        message (str | Unset):
        eval_explanation_summary (SDKSimulationAnalyticsResultEvalExplanationSummary | Unset):
        eval_explanation_summary_status (None | str | Unset):
    """

    run_test_name: str
    eval_results: list[SDKSimulationAnalyticsResultEvalResultsItem]
    eval_averages: SDKSimulationAnalyticsResultEvalAverages
    system_summary: SDKSimulationAnalyticsResultSystemSummary
    execution_id: UUID | Unset = UNSET
    status: str | Unset = UNSET
    message: str | Unset = UNSET
    eval_explanation_summary: (
        SDKSimulationAnalyticsResultEvalExplanationSummary | Unset
    ) = UNSET
    eval_explanation_summary_status: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        run_test_name = self.run_test_name

        eval_results = []
        for eval_results_item_data in self.eval_results:
            eval_results_item = eval_results_item_data.to_dict()
            eval_results.append(eval_results_item)

        eval_averages = self.eval_averages.to_dict()

        system_summary = self.system_summary.to_dict()

        execution_id: str | Unset = UNSET
        if not isinstance(self.execution_id, Unset):
            execution_id = str(self.execution_id)

        status = self.status

        message = self.message

        eval_explanation_summary: dict[str, Any] | Unset = UNSET
        if not isinstance(self.eval_explanation_summary, Unset):
            eval_explanation_summary = self.eval_explanation_summary.to_dict()

        eval_explanation_summary_status: None | str | Unset
        if isinstance(self.eval_explanation_summary_status, Unset):
            eval_explanation_summary_status = UNSET
        else:
            eval_explanation_summary_status = self.eval_explanation_summary_status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "run_test_name": run_test_name,
                "eval_results": eval_results,
                "eval_averages": eval_averages,
                "system_summary": system_summary,
            }
        )
        if execution_id is not UNSET:
            field_dict["execution_id"] = execution_id
        if status is not UNSET:
            field_dict["status"] = status
        if message is not UNSET:
            field_dict["message"] = message
        if eval_explanation_summary is not UNSET:
            field_dict["eval_explanation_summary"] = eval_explanation_summary
        if eval_explanation_summary_status is not UNSET:
            field_dict["eval_explanation_summary_status"] = (
                eval_explanation_summary_status
            )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sdk_simulation_analytics_result_eval_averages import (
            SDKSimulationAnalyticsResultEvalAverages,
        )
        from ..models.sdk_simulation_analytics_result_eval_explanation_summary import (
            SDKSimulationAnalyticsResultEvalExplanationSummary,
        )
        from ..models.sdk_simulation_analytics_result_eval_results_item import (
            SDKSimulationAnalyticsResultEvalResultsItem,
        )
        from ..models.sdk_simulation_analytics_result_system_summary import (
            SDKSimulationAnalyticsResultSystemSummary,
        )

        d = dict(src_dict)
        run_test_name = d.pop("run_test_name")

        eval_results = []
        _eval_results = d.pop("eval_results")
        for eval_results_item_data in _eval_results:
            eval_results_item = SDKSimulationAnalyticsResultEvalResultsItem.from_dict(
                eval_results_item_data
            )

            eval_results.append(eval_results_item)

        eval_averages = SDKSimulationAnalyticsResultEvalAverages.from_dict(
            d.pop("eval_averages")
        )

        system_summary = SDKSimulationAnalyticsResultSystemSummary.from_dict(
            d.pop("system_summary")
        )

        _execution_id = d.pop("execution_id", UNSET)
        execution_id: UUID | Unset
        if isinstance(_execution_id, Unset):
            execution_id = UNSET
        else:
            execution_id = UUID(_execution_id)

        status = d.pop("status", UNSET)

        message = d.pop("message", UNSET)

        _eval_explanation_summary = d.pop("eval_explanation_summary", UNSET)
        eval_explanation_summary: (
            SDKSimulationAnalyticsResultEvalExplanationSummary | Unset
        )
        if isinstance(_eval_explanation_summary, Unset):
            eval_explanation_summary = UNSET
        else:
            eval_explanation_summary = (
                SDKSimulationAnalyticsResultEvalExplanationSummary.from_dict(
                    _eval_explanation_summary
                )
            )

        def _parse_eval_explanation_summary_status(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        eval_explanation_summary_status = _parse_eval_explanation_summary_status(
            d.pop("eval_explanation_summary_status", UNSET)
        )

        sdk_simulation_analytics_result = cls(
            run_test_name=run_test_name,
            eval_results=eval_results,
            eval_averages=eval_averages,
            system_summary=system_summary,
            execution_id=execution_id,
            status=status,
            message=message,
            eval_explanation_summary=eval_explanation_summary,
            eval_explanation_summary_status=eval_explanation_summary_status,
        )

        sdk_simulation_analytics_result.additional_properties = d
        return sdk_simulation_analytics_result

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
