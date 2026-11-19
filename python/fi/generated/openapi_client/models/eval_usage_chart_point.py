from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="EvalUsageChartPoint")


@_attrs_define
class EvalUsageChartPoint:
    """
    Attributes:
        timestamp (str):
        calls (int | Unset):
        avg_latency_ms (int | Unset):
        avg_score (float | None | Unset):
        pass_count (int | Unset):
        fail_count (int | Unset):
    """

    timestamp: str
    calls: int | Unset = UNSET
    avg_latency_ms: int | Unset = UNSET
    avg_score: float | None | Unset = UNSET
    pass_count: int | Unset = UNSET
    fail_count: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        timestamp = self.timestamp

        calls = self.calls

        avg_latency_ms = self.avg_latency_ms

        avg_score: float | None | Unset
        if isinstance(self.avg_score, Unset):
            avg_score = UNSET
        else:
            avg_score = self.avg_score

        pass_count = self.pass_count

        fail_count = self.fail_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "timestamp": timestamp,
            }
        )
        if calls is not UNSET:
            field_dict["calls"] = calls
        if avg_latency_ms is not UNSET:
            field_dict["avg_latency_ms"] = avg_latency_ms
        if avg_score is not UNSET:
            field_dict["avg_score"] = avg_score
        if pass_count is not UNSET:
            field_dict["pass_count"] = pass_count
        if fail_count is not UNSET:
            field_dict["fail_count"] = fail_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        timestamp = d.pop("timestamp")

        calls = d.pop("calls", UNSET)

        avg_latency_ms = d.pop("avg_latency_ms", UNSET)

        def _parse_avg_score(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        avg_score = _parse_avg_score(d.pop("avg_score", UNSET))

        pass_count = d.pop("pass_count", UNSET)

        fail_count = d.pop("fail_count", UNSET)

        eval_usage_chart_point = cls(
            timestamp=timestamp,
            calls=calls,
            avg_latency_ms=avg_latency_ms,
            avg_score=avg_score,
            pass_count=pass_count,
            fail_count=fail_count,
        )

        eval_usage_chart_point.additional_properties = d
        return eval_usage_chart_point

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
