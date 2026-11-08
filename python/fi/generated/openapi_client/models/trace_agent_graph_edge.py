from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TraceAgentGraphEdge")


@_attrs_define
class TraceAgentGraphEdge:
    """
    Attributes:
        source (str):
        target (str):
        transition_count (int):
        avg_latency_ms (float):
        total_tokens (int):
        total_cost (float):
        error_count (int):
        trace_count (int | None):
        is_self_loop (bool):
        trace_count_exact (bool | Unset):
        is_aggregate (bool | Unset):
    """

    source: str
    target: str
    transition_count: int
    avg_latency_ms: float
    total_tokens: int
    total_cost: float
    error_count: int
    trace_count: int | None
    is_self_loop: bool
    trace_count_exact: bool | Unset = UNSET
    is_aggregate: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        source = self.source

        target = self.target

        transition_count = self.transition_count

        avg_latency_ms = self.avg_latency_ms

        total_tokens = self.total_tokens

        total_cost = self.total_cost

        error_count = self.error_count

        trace_count: int | None
        trace_count = self.trace_count

        is_self_loop = self.is_self_loop

        trace_count_exact = self.trace_count_exact

        is_aggregate = self.is_aggregate

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "source": source,
                "target": target,
                "transition_count": transition_count,
                "avg_latency_ms": avg_latency_ms,
                "total_tokens": total_tokens,
                "total_cost": total_cost,
                "error_count": error_count,
                "trace_count": trace_count,
                "is_self_loop": is_self_loop,
            }
        )
        if trace_count_exact is not UNSET:
            field_dict["trace_count_exact"] = trace_count_exact
        if is_aggregate is not UNSET:
            field_dict["is_aggregate"] = is_aggregate

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        source = d.pop("source")

        target = d.pop("target")

        transition_count = d.pop("transition_count")

        avg_latency_ms = d.pop("avg_latency_ms")

        total_tokens = d.pop("total_tokens")

        total_cost = d.pop("total_cost")

        error_count = d.pop("error_count")

        def _parse_trace_count(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        trace_count = _parse_trace_count(d.pop("trace_count"))

        is_self_loop = d.pop("is_self_loop")

        trace_count_exact = d.pop("trace_count_exact", UNSET)

        is_aggregate = d.pop("is_aggregate", UNSET)

        trace_agent_graph_edge = cls(
            source=source,
            target=target,
            transition_count=transition_count,
            avg_latency_ms=avg_latency_ms,
            total_tokens=total_tokens,
            total_cost=total_cost,
            error_count=error_count,
            trace_count=trace_count,
            is_self_loop=is_self_loop,
            trace_count_exact=trace_count_exact,
            is_aggregate=is_aggregate,
        )

        trace_agent_graph_edge.additional_properties = d
        return trace_agent_graph_edge

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
