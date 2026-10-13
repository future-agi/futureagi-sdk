from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.trace_session_graph_data_request_interval import (
    TraceSessionGraphDataRequestInterval,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.trace_session_graph_data_request_filters_item import (
        TraceSessionGraphDataRequestFiltersItem,
    )
    from ..models.trace_session_graph_data_request_req_data_config import (
        TraceSessionGraphDataRequestReqDataConfig,
    )


T = TypeVar("T", bound="TraceSessionGraphDataRequest")


@_attrs_define
class TraceSessionGraphDataRequest:
    """
    Attributes:
        project_id (UUID):
        req_data_config (TraceSessionGraphDataRequestReqDataConfig):
        filters (list[TraceSessionGraphDataRequestFiltersItem] | Unset):
        interval (TraceSessionGraphDataRequestInterval | Unset):  Default: TraceSessionGraphDataRequestInterval.DAY.
        property_ (str | Unset):  Default: 'average'.
    """

    project_id: UUID
    req_data_config: TraceSessionGraphDataRequestReqDataConfig
    filters: list[TraceSessionGraphDataRequestFiltersItem] | Unset = UNSET
    interval: TraceSessionGraphDataRequestInterval | Unset = (
        TraceSessionGraphDataRequestInterval.DAY
    )
    property_: str | Unset = "average"
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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.trace_session_graph_data_request_filters_item import (
            TraceSessionGraphDataRequestFiltersItem,
        )
        from ..models.trace_session_graph_data_request_req_data_config import (
            TraceSessionGraphDataRequestReqDataConfig,
        )

        d = dict(src_dict)
        project_id = UUID(d.pop("project_id"))

        req_data_config = TraceSessionGraphDataRequestReqDataConfig.from_dict(
            d.pop("req_data_config")
        )

        _filters = d.pop("filters", UNSET)
        filters: list[TraceSessionGraphDataRequestFiltersItem] | Unset = UNSET
        if _filters is not UNSET:
            filters = []
            for filters_item_data in _filters:
                filters_item = TraceSessionGraphDataRequestFiltersItem.from_dict(
                    filters_item_data
                )

                filters.append(filters_item)

        _interval = d.pop("interval", UNSET)
        interval: TraceSessionGraphDataRequestInterval | Unset
        if isinstance(_interval, Unset):
            interval = UNSET
        else:
            interval = TraceSessionGraphDataRequestInterval(_interval)

        property_ = d.pop("property", UNSET)

        trace_session_graph_data_request = cls(
            project_id=project_id,
            req_data_config=req_data_config,
            filters=filters,
            interval=interval,
            property_=property_,
        )

        trace_session_graph_data_request.additional_properties = d
        return trace_session_graph_data_request

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
