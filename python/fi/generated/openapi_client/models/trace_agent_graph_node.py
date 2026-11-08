from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TraceAgentGraphNode")


@_attrs_define
class TraceAgentGraphNode:
    """
    Attributes:
        id (str):
        name (str):
        type_ (str):
        span_count (int):
        avg_latency_ms (float):
        total_tokens (int):
        total_cost (float):
        error_count (int):
        trace_count (int | None):
        trace_count_exact (bool | Unset):
        is_aggregate (bool | Unset):
        member_count (int | Unset):
    """

    id: str
    name: str
    type_: str
    span_count: int
    avg_latency_ms: float
    total_tokens: int
    total_cost: float
    error_count: int
    trace_count: int | None
    trace_count_exact: bool | Unset = UNSET
    is_aggregate: bool | Unset = UNSET
    member_count: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        type_ = self.type_

        span_count = self.span_count

        avg_latency_ms = self.avg_latency_ms

        total_tokens = self.total_tokens

        total_cost = self.total_cost

        error_count = self.error_count

        trace_count: int | None
        trace_count = self.trace_count

        trace_count_exact = self.trace_count_exact

        is_aggregate = self.is_aggregate

        member_count = self.member_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "type": type_,
                "span_count": span_count,
                "avg_latency_ms": avg_latency_ms,
                "total_tokens": total_tokens,
                "total_cost": total_cost,
                "error_count": error_count,
                "trace_count": trace_count,
            }
        )
        if trace_count_exact is not UNSET:
            field_dict["trace_count_exact"] = trace_count_exact
        if is_aggregate is not UNSET:
            field_dict["is_aggregate"] = is_aggregate
        if member_count is not UNSET:
            field_dict["member_count"] = member_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        type_ = d.pop("type")

        span_count = d.pop("span_count")

        avg_latency_ms = d.pop("avg_latency_ms")

        total_tokens = d.pop("total_tokens")

        total_cost = d.pop("total_cost")

        error_count = d.pop("error_count")

        def _parse_trace_count(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        trace_count = _parse_trace_count(d.pop("trace_count"))

        trace_count_exact = d.pop("trace_count_exact", UNSET)

        is_aggregate = d.pop("is_aggregate", UNSET)

        member_count = d.pop("member_count", UNSET)

        trace_agent_graph_node = cls(
            id=id,
            name=name,
            type_=type_,
            span_count=span_count,
            avg_latency_ms=avg_latency_ms,
            total_tokens=total_tokens,
            total_cost=total_cost,
            error_count=error_count,
            trace_count=trace_count,
            trace_count_exact=trace_count_exact,
            is_aggregate=is_aggregate,
            member_count=member_count,
        )

        trace_agent_graph_node.additional_properties = d
        return trace_agent_graph_node

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
