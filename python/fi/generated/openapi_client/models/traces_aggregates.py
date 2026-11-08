from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="TracesAggregates")


@_attrs_define
class TracesAggregates:
    """
    Attributes:
        total_traces (int):
        failing_traces (int):
        passing_traces (int):
        avg_score (float):
        p50_latency (int):
        p95_latency (int):
        avg_turns (float):
    """

    total_traces: int
    failing_traces: int
    passing_traces: int
    avg_score: float
    p50_latency: int
    p95_latency: int
    avg_turns: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        total_traces = self.total_traces

        failing_traces = self.failing_traces

        passing_traces = self.passing_traces

        avg_score = self.avg_score

        p50_latency = self.p50_latency

        p95_latency = self.p95_latency

        avg_turns = self.avg_turns

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "total_traces": total_traces,
                "failing_traces": failing_traces,
                "passing_traces": passing_traces,
                "avg_score": avg_score,
                "p50_latency": p50_latency,
                "p95_latency": p95_latency,
                "avg_turns": avg_turns,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        total_traces = d.pop("total_traces")

        failing_traces = d.pop("failing_traces")

        passing_traces = d.pop("passing_traces")

        avg_score = d.pop("avg_score")

        p50_latency = d.pop("p50_latency")

        p95_latency = d.pop("p95_latency")

        avg_turns = d.pop("avg_turns")

        traces_aggregates = cls(
            total_traces=total_traces,
            failing_traces=failing_traces,
            passing_traces=passing_traces,
            avg_score=avg_score,
            p50_latency=p50_latency,
            p95_latency=p95_latency,
            avg_turns=avg_turns,
        )

        traces_aggregates.additional_properties = d
        return traces_aggregates

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
