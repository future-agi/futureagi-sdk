from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.trace_detail_result_graph import TraceDetailResultGraph
    from ..models.trace_detail_result_summary import TraceDetailResultSummary
    from ..models.trace_detail_result_trace import TraceDetailResultTrace
    from ..models.trace_detail_span import TraceDetailSpan


T = TypeVar("T", bound="TraceDetailResult")


@_attrs_define
class TraceDetailResult:
    """
    Attributes:
        trace (TraceDetailResultTrace):
        observation_spans (list[TraceDetailSpan]):
        summary (TraceDetailResultSummary):
        graph (TraceDetailResultGraph):
    """

    trace: TraceDetailResultTrace
    observation_spans: list[TraceDetailSpan]
    summary: TraceDetailResultSummary
    graph: TraceDetailResultGraph
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        trace = self.trace.to_dict()

        observation_spans = []
        for observation_spans_item_data in self.observation_spans:
            observation_spans_item = observation_spans_item_data.to_dict()
            observation_spans.append(observation_spans_item)

        summary = self.summary.to_dict()

        graph = self.graph.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "trace": trace,
                "observation_spans": observation_spans,
                "summary": summary,
                "graph": graph,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.trace_detail_result_graph import TraceDetailResultGraph
        from ..models.trace_detail_result_summary import TraceDetailResultSummary
        from ..models.trace_detail_result_trace import TraceDetailResultTrace
        from ..models.trace_detail_span import TraceDetailSpan

        d = dict(src_dict)
        trace = TraceDetailResultTrace.from_dict(d.pop("trace"))

        observation_spans = []
        _observation_spans = d.pop("observation_spans")
        for observation_spans_item_data in _observation_spans:
            observation_spans_item = TraceDetailSpan.from_dict(
                observation_spans_item_data
            )

            observation_spans.append(observation_spans_item)

        summary = TraceDetailResultSummary.from_dict(d.pop("summary"))

        graph = TraceDetailResultGraph.from_dict(d.pop("graph"))

        trace_detail_result = cls(
            trace=trace,
            observation_spans=observation_spans,
            summary=summary,
            graph=graph,
        )

        trace_detail_result.additional_properties = d
        return trace_detail_result

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
