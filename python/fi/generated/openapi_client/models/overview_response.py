from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.events_over_time_point import EventsOverTimePoint
    from ..models.pattern_summary import PatternSummary
    from ..models.representative_trace import RepresentativeTrace


T = TypeVar("T", bound="OverviewResponse")


@_attrs_define
class OverviewResponse:
    """
    Attributes:
        events_over_time (list[EventsOverTimePoint]):
        pattern_summary (PatternSummary):
        representative_traces (list[RepresentativeTrace]):
    """

    events_over_time: list[EventsOverTimePoint]
    pattern_summary: PatternSummary
    representative_traces: list[RepresentativeTrace]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        events_over_time = []
        for events_over_time_item_data in self.events_over_time:
            events_over_time_item = events_over_time_item_data.to_dict()
            events_over_time.append(events_over_time_item)

        pattern_summary = self.pattern_summary.to_dict()

        representative_traces = []
        for representative_traces_item_data in self.representative_traces:
            representative_traces_item = representative_traces_item_data.to_dict()
            representative_traces.append(representative_traces_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "events_over_time": events_over_time,
                "pattern_summary": pattern_summary,
                "representative_traces": representative_traces,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.events_over_time_point import EventsOverTimePoint
        from ..models.pattern_summary import PatternSummary
        from ..models.representative_trace import RepresentativeTrace

        d = dict(src_dict)
        events_over_time = []
        _events_over_time = d.pop("events_over_time")
        for events_over_time_item_data in _events_over_time:
            events_over_time_item = EventsOverTimePoint.from_dict(
                events_over_time_item_data
            )

            events_over_time.append(events_over_time_item)

        pattern_summary = PatternSummary.from_dict(d.pop("pattern_summary"))

        representative_traces = []
        _representative_traces = d.pop("representative_traces")
        for representative_traces_item_data in _representative_traces:
            representative_traces_item = RepresentativeTrace.from_dict(
                representative_traces_item_data
            )

            representative_traces.append(representative_traces_item)

        overview_response = cls(
            events_over_time=events_over_time,
            pattern_summary=pattern_summary,
            representative_traces=representative_traces,
        )

        overview_response.additional_properties = d
        return overview_response

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
