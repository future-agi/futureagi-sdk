from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="EvalUsageStats")


@_attrs_define
class EvalUsageStats:
    """
    Attributes:
        total_runs (int):
        runs_period (int):
        success_count (int):
        error_count (int):
        pass_rate (float):
    """

    total_runs: int
    runs_period: int
    success_count: int
    error_count: int
    pass_rate: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        total_runs = self.total_runs

        runs_period = self.runs_period

        success_count = self.success_count

        error_count = self.error_count

        pass_rate = self.pass_rate

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "total_runs": total_runs,
                "runs_period": runs_period,
                "success_count": success_count,
                "error_count": error_count,
                "pass_rate": pass_rate,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        total_runs = d.pop("total_runs")

        runs_period = d.pop("runs_period")

        success_count = d.pop("success_count")

        error_count = d.pop("error_count")

        pass_rate = d.pop("pass_rate")

        eval_usage_stats = cls(
            total_runs=total_runs,
            runs_period=runs_period,
            success_count=success_count,
            error_count=error_count,
            pass_rate=pass_rate,
        )

        eval_usage_stats.additional_properties = d
        return eval_usage_stats

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
