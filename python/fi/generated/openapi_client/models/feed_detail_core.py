from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.feed_list_row import FeedListRow
    from ..models.rca_summary import RcaSummary
    from ..models.trace_preview import TracePreview


T = TypeVar("T", bound="FeedDetailCore")


@_attrs_define
class FeedDetailCore:
    """
    Attributes:
        row (FeedListRow):
        description (None | str):
        success_trace (TracePreview):
        representative_trace (TracePreview):
        rca (RcaSummary | Unset):
    """

    row: FeedListRow
    description: None | str
    success_trace: TracePreview
    representative_trace: TracePreview
    rca: RcaSummary | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        row = self.row.to_dict()

        description: None | str
        description = self.description

        success_trace = self.success_trace.to_dict()

        representative_trace = self.representative_trace.to_dict()

        rca: dict[str, Any] | Unset = UNSET
        if not isinstance(self.rca, Unset):
            rca = self.rca.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "row": row,
                "description": description,
                "success_trace": success_trace,
                "representative_trace": representative_trace,
            }
        )
        if rca is not UNSET:
            field_dict["rca"] = rca

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.feed_list_row import FeedListRow
        from ..models.rca_summary import RcaSummary
        from ..models.trace_preview import TracePreview

        d = dict(src_dict)
        row = FeedListRow.from_dict(d.pop("row"))

        def _parse_description(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        description = _parse_description(d.pop("description"))

        success_trace = TracePreview.from_dict(d.pop("success_trace"))

        representative_trace = TracePreview.from_dict(d.pop("representative_trace"))

        _rca = d.pop("rca", UNSET)
        rca: RcaSummary | Unset
        if isinstance(_rca, Unset):
            rca = UNSET
        else:
            rca = RcaSummary.from_dict(_rca)

        feed_detail_core = cls(
            row=row,
            description=description,
            success_trace=success_trace,
            representative_trace=representative_trace,
            rca=rca,
        )

        feed_detail_core.additional_properties = d
        return feed_detail_core

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
