from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.events_over_time_point import EventsOverTimePoint
    from ..models.heatmap_cell import HeatmapCell
    from ..models.score_trend import ScoreTrend
    from ..models.trend_metric import TrendMetric


T = TypeVar("T", bound="TrendsTabResponse")


@_attrs_define
class TrendsTabResponse:
    """
    Attributes:
        metrics (list[TrendMetric]):
        events_over_time (list[EventsOverTimePoint]):
        score_trends (list[ScoreTrend]):
        activity_heatmap (list[list[HeatmapCell]]):
    """

    metrics: list[TrendMetric]
    events_over_time: list[EventsOverTimePoint]
    score_trends: list[ScoreTrend]
    activity_heatmap: list[list[HeatmapCell]]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        metrics = []
        for metrics_item_data in self.metrics:
            metrics_item = metrics_item_data.to_dict()
            metrics.append(metrics_item)

        events_over_time = []
        for events_over_time_item_data in self.events_over_time:
            events_over_time_item = events_over_time_item_data.to_dict()
            events_over_time.append(events_over_time_item)

        score_trends = []
        for score_trends_item_data in self.score_trends:
            score_trends_item = score_trends_item_data.to_dict()
            score_trends.append(score_trends_item)

        activity_heatmap = []
        for activity_heatmap_item_data in self.activity_heatmap:
            activity_heatmap_item = []
            for activity_heatmap_item_item_data in activity_heatmap_item_data:
                activity_heatmap_item_item = activity_heatmap_item_item_data.to_dict()
                activity_heatmap_item.append(activity_heatmap_item_item)

            activity_heatmap.append(activity_heatmap_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "metrics": metrics,
                "events_over_time": events_over_time,
                "score_trends": score_trends,
                "activity_heatmap": activity_heatmap,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.events_over_time_point import EventsOverTimePoint
        from ..models.heatmap_cell import HeatmapCell
        from ..models.score_trend import ScoreTrend
        from ..models.trend_metric import TrendMetric

        d = dict(src_dict)
        metrics = []
        _metrics = d.pop("metrics")
        for metrics_item_data in _metrics:
            metrics_item = TrendMetric.from_dict(metrics_item_data)

            metrics.append(metrics_item)

        events_over_time = []
        _events_over_time = d.pop("events_over_time")
        for events_over_time_item_data in _events_over_time:
            events_over_time_item = EventsOverTimePoint.from_dict(
                events_over_time_item_data
            )

            events_over_time.append(events_over_time_item)

        score_trends = []
        _score_trends = d.pop("score_trends")
        for score_trends_item_data in _score_trends:
            score_trends_item = ScoreTrend.from_dict(score_trends_item_data)

            score_trends.append(score_trends_item)

        activity_heatmap = []
        _activity_heatmap = d.pop("activity_heatmap")
        for activity_heatmap_item_data in _activity_heatmap:
            activity_heatmap_item = []
            _activity_heatmap_item = activity_heatmap_item_data
            for activity_heatmap_item_item_data in _activity_heatmap_item:
                activity_heatmap_item_item = HeatmapCell.from_dict(
                    activity_heatmap_item_item_data
                )

                activity_heatmap_item.append(activity_heatmap_item_item)

            activity_heatmap.append(activity_heatmap_item)

        trends_tab_response = cls(
            metrics=metrics,
            events_over_time=events_over_time,
            score_trends=score_trends,
            activity_heatmap=activity_heatmap,
        )

        trends_tab_response.additional_properties = d
        return trends_tab_response

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
