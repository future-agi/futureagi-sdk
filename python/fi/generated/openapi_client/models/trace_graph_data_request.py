from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.trace_graph_data_request_interval import TraceGraphDataRequestInterval
from ..models.trace_graph_data_request_observe_type import (
    TraceGraphDataRequestObserveType,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.trace_graph_data_request_filters_item import (
        TraceGraphDataRequestFiltersItem,
    )
    from ..models.trace_graph_data_request_req_data_config import (
        TraceGraphDataRequestReqDataConfig,
    )


T = TypeVar("T", bound="TraceGraphDataRequest")


@_attrs_define
class TraceGraphDataRequest:
    """
    Attributes:
        project_id (UUID):
        req_data_config (TraceGraphDataRequestReqDataConfig):
        filters (list[TraceGraphDataRequestFiltersItem] | Unset): On trace, span, session, graph, and eval-task bounded
            reads, created_at/start_time datetime filters support equals, greater_than, greater_than_or_equal, less_than,
            less_than_or_equal, between, not_equals, not_between, is_null, and is_not_null. Missing bounds retain the finite
            default window: 30 days ago for the lower bound and request-time now for the upper bound. Between and
            not_between use half-open [start, end) ranges; not_equals excludes one DateTime64(6) microsecond. Because the
            physical created_at/start_time field is non-null, is_null returns an exact empty result without a ClickHouse
            read and is_not_null preserves the base window. Valid contradictions also return an exact empty result.
        interval (TraceGraphDataRequestInterval | Unset):  Default: TraceGraphDataRequestInterval.DAY.
        property_ (str | Unset): Accepted for older clients and ignored for SYSTEM_METRIC graphs: each system metric has
            one statistic, named by the response's metric_statistic. Latency is always the mean (avg) span latency. Default:
            'average'.
        observe_type (TraceGraphDataRequestObserveType | Unset): Population the graph counts: every trace, or only voice
            calls (traces whose root span is a conversation), exactly as list_voice_calls selects them. Default:
            TraceGraphDataRequestObserveType.TRACE.
        remove_simulation_calls (bool | Unset): Voice graphs only: exclude calls placed by a simulator phone, exactly as
            list_voice_calls' remove_simulation_calls does. Default: False.
    """

    project_id: UUID
    req_data_config: TraceGraphDataRequestReqDataConfig
    filters: list[TraceGraphDataRequestFiltersItem] | Unset = UNSET
    interval: TraceGraphDataRequestInterval | Unset = TraceGraphDataRequestInterval.DAY
    property_: str | Unset = "average"
    observe_type: TraceGraphDataRequestObserveType | Unset = (
        TraceGraphDataRequestObserveType.TRACE
    )
    remove_simulation_calls: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        project_id = str(self.project_id)

        req_data_config = self.req_data_config.to_dict()

        filters: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.filters, Unset):
            filters = []
            for filters_item_data in self.filters:
                filters_item = filters_item_data.to_dict()
                filters.append(filters_item)

        interval: str | Unset = UNSET
        if not isinstance(self.interval, Unset):
            interval = self.interval.value

        property_ = self.property_

        observe_type: str | Unset = UNSET
        if not isinstance(self.observe_type, Unset):
            observe_type = self.observe_type.value

        remove_simulation_calls = self.remove_simulation_calls

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "project_id": project_id,
                "req_data_config": req_data_config,
            }
        )
        if filters is not UNSET:
            field_dict["filters"] = filters
        if interval is not UNSET:
            field_dict["interval"] = interval
        if property_ is not UNSET:
            field_dict["property"] = property_
        if observe_type is not UNSET:
            field_dict["observe_type"] = observe_type
        if remove_simulation_calls is not UNSET:
            field_dict["remove_simulation_calls"] = remove_simulation_calls

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.trace_graph_data_request_filters_item import (
            TraceGraphDataRequestFiltersItem,
        )
        from ..models.trace_graph_data_request_req_data_config import (
            TraceGraphDataRequestReqDataConfig,
        )

        d = dict(src_dict)
        project_id = UUID(d.pop("project_id"))

        req_data_config = TraceGraphDataRequestReqDataConfig.from_dict(
            d.pop("req_data_config")
        )

        _filters = d.pop("filters", UNSET)
        filters: list[TraceGraphDataRequestFiltersItem] | Unset = UNSET
        if _filters is not UNSET:
            filters = []
            for filters_item_data in _filters:
                filters_item = TraceGraphDataRequestFiltersItem.from_dict(
                    filters_item_data
                )

                filters.append(filters_item)

        _interval = d.pop("interval", UNSET)
        interval: TraceGraphDataRequestInterval | Unset
        if isinstance(_interval, Unset):
            interval = UNSET
        else:
            interval = TraceGraphDataRequestInterval(_interval)

        property_ = d.pop("property", UNSET)

        _observe_type = d.pop("observe_type", UNSET)
        observe_type: TraceGraphDataRequestObserveType | Unset
        if isinstance(_observe_type, Unset):
            observe_type = UNSET
        else:
            observe_type = TraceGraphDataRequestObserveType(_observe_type)

        remove_simulation_calls = d.pop("remove_simulation_calls", UNSET)

        trace_graph_data_request = cls(
            project_id=project_id,
            req_data_config=req_data_config,
            filters=filters,
            interval=interval,
            property_=property_,
            observe_type=observe_type,
            remove_simulation_calls=remove_simulation_calls,
        )

        trace_graph_data_request.additional_properties = d
        return trace_graph_data_request

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
